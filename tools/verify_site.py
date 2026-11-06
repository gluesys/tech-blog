#!/usr/bin/env python3
"""Check that every old URL still works in the Hugo build (stdlib only).

    python3 tools/verify_site.py --build build [--snapshot migration/snapshot] \
        [--allow migration/site-allowlist.yaml]
    python3 tools/verify_site.py --live https://tech.gluesys.com \
        --snapshot migration/snapshot

Build mode checks:
  * /blog/ and /page2/ .. /page6/ exist and redirect to /posts/;
  * /feed.xml is RSS 2.0 with exactly 10 items that are the 10 newest blog
    posts in date-descending order (post dates come from the built
    /blog/Y/M/D/<slug>.html paths, so they are the UTC dates in the URLs);
  * every internal <img src> / srcset entry resolves to a file (percent-decoded,
    case-sensitive);
  * CNAME, the Search Console file and favicon.ico match the SHA-256 values
    pinned in migration/static-baseline.txt (Jekyll baseline 5605f21);
  * the /tags/ page carries the tag lookup JSON for the old /tags#<tag> links,
    and it covers every alias in data/tag_aliases.yaml whose tag page exists;
  * every internal <a href> in build/**/*.html resolves to a file and, with a
    fragment (other than #:~:text=), to an existing id or name.
Snapshot checks run only when --snapshot is given (a missing or empty snapshot
then fails the run); without it they are skipped and reported as such:
  * every path in <snapshot>/urls.txt exists in the build;
  * every snapshot feed item that is still in the new feed (matched by title)
    keeps its exact link, so new posts may push old items out of the feed;
  * every URL in the snapshot sitemap is in the new sitemap (redirect pages
    are exempt: they are not canonical, /posts/ stands in for them).
Known broken internal links go in the site allow-list `{page, href, reason}`
(page "*" matches any page); an entry that matches nothing fails the run.

Live mode fetches the urls.txt paths, the alias paths and the main pages from
a running site (expects HTTP 200) and compares its /feed.xml item links.

Exit status is 1 on any failure.
"""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from tags import load_aliases, norm_key, tag_slug  # noqa: E402
from verify_migration import _scalar  # noqa: E402

SITE_HOST = "tech.gluesys.com"
ALIAS_PATHS = ("/blog/", "/page2/", "/page3/", "/page4/", "/page5/", "/page6/")
LIVE_EXTRA = ("/", "/posts/", "/tags/", "/sitemap.xml", "/robots.txt",
              "/googlea2b9a3ab05f01437.html", "/assets/icons/favicon.ico")
DEFAULT_BASELINE = ROOT / "migration" / "static-baseline.txt"
FEED_ITEMS = 10
SITE_ALLOW_KEYS = ("page", "href", "reason")


# ---------------------------------------------------------------- feed

def feed_items(text):
    """Return (rss version, [(title, link)]) or raise ValueError."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"not well-formed XML: {e}") from e
    if root.tag != "rss":
        raise ValueError(f"root element is <{root.tag}>, not <rss>")
    items = root.findall("./channel/item")
    return root.get("version"), [((i.findtext("title") or "").strip(),
                                  (i.findtext("link") or "").strip()) for i in items]


def post_paths(build):
    """URL paths of every built post page, /blog/Y/M/D/<slug>.html."""
    root = Path(build) / "blog"
    if not root.is_dir():
        return []
    return ["/" + f.relative_to(build).as_posix() for f in sorted(root.rglob("*.html"))
            if len(f.relative_to(root).parts) == 4]


def _post_date(path):
    m = re.match(r"^/blog/(\d{4})/(\d{2})/(\d{2})/", path)
    return m.groups() if m else None


def check_feed(feed_text, posts=None, snapshot_feed_text=None):
    """Check the feed structure, its content and, optionally, the snapshot.

    posts: URL paths of all built posts (None skips the newest-posts rule).
    The feed must hold the 10 newest posts, newest first. Dates are the Y/M/D
    of the URL (UTC date for migrated posts); posts of the same day may come in
    any order, but no omitted post may be newer than the oldest feed item.
    snapshot_feed_text: every snapshot item whose title is still in the feed
    must keep its link.
    """
    try:
        version, items = feed_items(feed_text)
    except ValueError as e:
        return [f"feed.xml: {e}"]
    links = [l for _, l in items]
    out = []
    if version != "2.0":
        out.append(f"feed.xml: RSS version {version!r}, expected '2.0'")
    if len(links) != FEED_ITEMS:
        out.append(f"feed.xml: {len(links)} items, expected {FEED_ITEMS}")
    if posts is not None:
        paths = [urlsplit(l).path for l in links]
        known = set(posts)
        dates = []
        for l, p in zip(links, paths):
            if p not in known:
                out.append(f"feed.xml: item {l!r} is not a built blog post")
            dates.append(_post_date(p) or ())
        if dates != sorted(dates, reverse=True):
            out.append("feed.xml: items are not in date-descending order")
        rest = [_post_date(p) for p in known - set(paths)]
        if dates and rest and max(d for d in rest if d) > min(dates):
            out.append("feed.xml: a newer post is missing from the feed items")
        if len(links) != min(FEED_ITEMS, len(known)):
            out.append(f"feed.xml: {len(links)} items for {len(known)} posts")
    if snapshot_feed_text is not None:
        try:
            old = feed_items(snapshot_feed_text)[1]
        except ValueError as e:
            return out + [f"snapshot feed.xml: {e}"]
        now = dict(items)
        for title, link in old:
            if title in now and now[title] != link:
                out.append(f"feed.xml: {title!r} link {now[title]!r}, snapshot has {link!r}")
    return out


# ---------------------------------------------------------------- aliases

class _Refresh(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            m = re.search(r"url\s*=\s*(\S+)", a.get("content") or "", re.I)
            if m:
                self.targets.append(m.group(1))


def check_aliases(build):
    out = []
    for path in ALIAS_PATHS:
        f = Path(build) / path.strip("/") / "index.html"
        if not f.is_file():
            out.append(f"alias {path}: missing {f}")
            continue
        p = _Refresh()
        p.feed(f.read_text(encoding="utf-8"))
        targets = {urlsplit(t).path for t in p.targets}
        if targets != {"/posts/"}:
            out.append(f"alias {path}: refresh targets {sorted(targets)}, expected ['/posts/']")
    return out


# ---------------------------------------------------------------- static, sitemap

def check_post_files(build):
    """Every post page must be a plain file /blog/Y/M/D/<slug>.html.

    Catches a directory-style post (<slug>.html/index.html) and a slug that kept
    its YYYY-MM-DD- file name prefix (new post that also set `date`).
    """
    problems = []
    root = Path(build) / "blog"
    if not root.is_dir():
        return [f"{root}: missing"]
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root)
        if len(rel.parts) == 1:        # /blog/index.html alias
            continue
        if len(rel.parts) != 4 or f.suffix != ".html":
            problems.append(f"blog/{rel}: post page is not a plain /blog/Y/M/D/<slug>.html file")
        elif re.match(r"\d{4}-\d{2}-\d{2}-", f.name):
            problems.append(f"blog/{rel}: slug keeps the date prefix (do not set `date` in a new post)")
    return problems


def load_static_baseline(path):
    """Read `<sha256>  <path>` lines -> {path: sha256}."""
    out = {}
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([0-9a-f]{64})  (\S.*)$", line)
        if not m:
            raise ValueError(f"{path}:{n}: cannot parse {line!r}")
        out[m.group(2)] = m.group(1)
    if not out:
        raise ValueError(f"{path}: no entries")
    return out


def check_static(build, baseline):
    out = []
    for rel, want in sorted(baseline.items()):
        f = Path(build) / rel
        if not f.is_file():
            out.append(f"static {rel}: missing from build")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != want:
            out.append(f"static {rel}: differs from the baseline checksum")
    return out


def sitemap_paths(text):
    root = ET.fromstring(text)
    return {urlsplit(e.text.strip()).path
            for e in root.iter() if e.tag.endswith("}loc") or e.tag == "loc"}


def check_sitemap(new_text, snapshot_text, exempt):
    try:
        new = sitemap_paths(new_text)
    except ET.ParseError as e:
        return [f"sitemap.xml: not well-formed XML: {e}"]
    try:
        want = sitemap_paths(snapshot_text)
    except ET.ParseError as e:
        return [f"snapshot sitemap.xml: not well-formed XML: {e}"]
    if not want:
        return ["snapshot sitemap.xml: no <loc> entries"]
    return [f"sitemap.xml: snapshot URL {p} missing"
            for p in sorted(want - new - set(exempt))]


# ---------------------------------------------------------------- tag map

class _TagMap(HTMLParser):
    def __init__(self):
        super().__init__()
        self._on = False
        self.text = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "tag-map":
            self._on = self.found = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._on = False

    def handle_data(self, data):
        if self._on:
            self.text.append(data)


def check_tag_map(build, aliases):
    """Check the lookup table the /tags/ page embeds for tags-redirect.ts."""
    page = Path(build) / "tags" / "index.html"
    if not page.is_file():
        return ["tag map: build/tags/index.html missing"]
    p = _TagMap()
    p.feed(page.read_text(encoding="utf-8"))
    if not p.found:
        return ["tag map: no <script id=\"tag-map\"> on /tags/"]
    try:
        table = json.loads("".join(p.text))
    except ValueError as e:
        return [f"tag map: bad JSON: {e}"]
    out = []
    for key, path in sorted(table.items()):
        if key != unicodedata.normalize("NFC", key) or key != re.sub(r"\s+", " ", key).strip().lower():
            out.append(f"tag map: key {key!r} is not normalized")
        if not _resolve(build, unquote(path)).is_file():
            out.append(f"tag map: {key!r} -> {path} has no built page")
    for raw, canon in sorted(aliases.items()):
        want = f"/tags/{tag_slug(canon)}/"
        if not _resolve(build, want).is_file():
            continue  # canonical tag unused by any post
        got = table.get(raw)
        if got is None:
            out.append(f"tag map: alias {raw!r} missing (want {want})")
        elif unquote(got) != want:
            out.append(f"tag map: alias {raw!r} -> {got}, want {want}")
    return out


# ---------------------------------------------------------------- links

class _Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.srcs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "img" or tag == "source":
            if a.get("src"):
                self.srcs.append(a["src"])
            for cand in (a.get("srcset") or "").split(","):
                if cand.strip():
                    self.srcs.append(cand.split()[0])
        if tag == "a":
            if a.get("name"):
                self.ids.add(a["name"])
            if a.get("href") is not None:
                self.hrefs.append(a["href"])


def _scan(path, cache):
    if path not in cache:
        p = _Anchors()
        p.feed(path.read_text(encoding="utf-8"))
        cache[path] = p
    return cache[path]


def _internal(href, page_url):
    """Return (path, fragment) for an internal href, else None."""
    h = href.strip()
    if not h or h.startswith("//"):
        return None
    parts = urlsplit(urljoin(page_url, h))
    if parts.scheme not in ("", "http", "https"):
        return None
    if parts.netloc and parts.netloc != SITE_HOST:
        return None
    return unquote(parts.path), unquote(parts.fragment)


def _resolve(build, path):
    f = Path(build) / path.lstrip("/")
    if path.endswith("/") or f.is_dir():
        f = f / "index.html"
    return f


def check_links(build, allow=()):
    """Return (failures, unused allow-list entries)."""
    build = Path(build)
    allowed = {(e["page"], e["href"]): e for e in allow}
    used = set()
    failures = []
    seen = set()
    cache = {}
    scanned = 0
    for html in sorted(build.rglob("*.html")):
        page_url = "/" + html.relative_to(build).as_posix()
        for href in _scan(html, cache).hrefs:
            scanned += 1
            target = _internal(href, f"https://{SITE_HOST}{page_url}")
            if target is None:
                continue
            path, frag = target
            if frag.startswith(":~:text="):
                frag = ""
            f = _resolve(build, path)
            problem = None
            if not f.is_file():
                problem = f"no such file {path}"
            elif frag and (f.suffix != ".html" or frag not in _scan(f, cache).ids):
                problem = f"no id {frag!r} in {path}"
            if problem is None:
                continue
            hit = next((k for k in ((page_url, href), ("*", href)) if k in allowed), None)
            if hit:
                used.add(hit)
            elif (page_url, href) not in seen:
                seen.add((page_url, href))
                failures.append(f"link {page_url}: {href!r}: {problem}")
    if not scanned:
        failures.append(f"link scan: no <a href> found under {build}")
    unused = [e for e in allow if (e["page"], e["href"]) not in used]
    return failures, unused


def check_images(build):
    """Every internal <img src> (and srcset entry) must resolve to a file."""
    build = Path(build)
    failures, cache, seen, scanned = [], {}, set(), 0
    for html in sorted(build.rglob("*.html")):
        page_url = "/" + html.relative_to(build).as_posix()
        for src in _scan(html, cache).srcs:
            scanned += 1
            if src.strip().startswith("data:"):
                continue
            target = _internal(src, f"https://{SITE_HOST}{page_url}")
            if target is None:
                continue
            if not (build / target[0].lstrip("/")).is_file() and (page_url, src) not in seen:
                seen.add((page_url, src))
                failures.append(f"image {page_url}: {src!r}: no such file {target[0]}")
    return failures, scanned


def load_site_allowlist(path):
    """Parse a YAML list of `page`, `href`, `reason` scalar mappings."""
    entries, cur = [], None
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        where = f"{path}:{n}"
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.strip() == "[]":
            if entries or cur:
                raise ValueError(f"{where}: '[]' after entries")
            continue
        m = re.match(r"^(- |  )([a-z_]+):[ \t]+(.*)$", line)
        if not m:
            raise ValueError(f"{where}: cannot parse {line!r}")
        lead, key, val = m.groups()
        if lead == "- ":
            cur = {}
            entries.append(cur)
        elif cur is None:
            raise ValueError(f"{where}: key outside a list item")
        if key not in SITE_ALLOW_KEYS:
            raise ValueError(f"{where}: unknown key {key!r}")
        if key in cur:
            raise ValueError(f"{where}: duplicate key {key!r}")
        cur[key] = _scalar(val, where)
    for i, e in enumerate(entries, 1):
        missing = [k for k in SITE_ALLOW_KEYS if not e.get(k)]
        if missing:
            raise ValueError(f"{path}: entry {i} missing {', '.join(missing)}")
    return entries


# ---------------------------------------------------------------- modes

def read_urls(snapshot):
    f = Path(snapshot) / "urls.txt"
    if not f.is_file():
        return []
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def url_to_file(build, url):
    return _resolve(build, unquote(url))


def run_build(build, snapshot, allow, static_baseline=DEFAULT_BASELINE):
    """snapshot None: skip the snapshot checks; a given snapshot must be usable."""
    failures, notes = [], []
    build = Path(build)
    skipped = 3 if snapshot is None else 0   # urls, feed links, sitemap
    if snapshot is not None:
        urls = read_urls(snapshot)
        if not urls:
            return [f"no URLs in {Path(snapshot) / 'urls.txt'}"], notes
    if not build.is_dir():
        return [f"build directory {build} not found"], notes

    if snapshot is not None:
        missing = [u for u in urls if not url_to_file(build, u).is_file()]
        failures += [f"url {u}: missing from build" for u in missing]
        notes.append(f"urls: {len(urls) - len(missing)}/{len(urls)} present")

    alias_fail = check_aliases(build)
    failures += alias_fail
    notes.append(f"aliases: {len(ALIAS_PATHS) - len(alias_fail)}/{len(ALIAS_PATHS)} ok")

    feed = build / "feed.xml"
    snap_feed = Path(snapshot) / "feed.xml" if snapshot is not None else None
    if not feed.is_file() or (snap_feed is not None and not snap_feed.is_file()):
        failures.append("feed.xml: missing from build or snapshot")
    else:
        f = check_feed(feed.read_text(encoding="utf-8"), post_paths(build),
                       snap_feed.read_text(encoding="utf-8") if snap_feed else None)
        failures += f
        notes.append(f"feed: {'ok' if not f else str(len(f)) + ' problems'}")

    sm = build / "sitemap.xml"
    snap_sm = Path(snapshot) / "sitemap.xml" if snapshot is not None else None
    if snap_sm is None:
        if not sm.is_file():
            failures.append("sitemap.xml: missing from build")
    elif not sm.is_file() or not snap_sm.is_file():
        failures.append("sitemap.xml: missing from build or snapshot")
    else:
        exempt = set(ALIAS_PATHS) if not alias_fail else set()
        f = check_sitemap(sm.read_text(encoding="utf-8"), snap_sm.read_text(encoding="utf-8"), exempt)
        failures += f
        notes.append(f"sitemap: {'ok' if not f else str(len(f)) + ' problems'}")

    f = check_post_files(build)
    failures += f
    notes.append(f"post files: {'ok' if not f else str(len(f)) + ' problems'}")

    baseline = load_static_baseline(static_baseline)
    f = check_static(build, baseline)
    failures += f
    notes.append(f"static files: {len(baseline) - len(f)}/{len(baseline)} identical")

    f = check_tag_map(build, {norm_key(k): v for k, v in load_aliases().items()})
    failures += f
    notes.append(f"tag map: {'ok' if not f else str(len(f)) + ' problems'}")

    link_fail, unused = check_links(build, allow)
    failures += link_fail
    failures += [f"unused site allow-list entry {e['page']} {e['href']!r}" for e in unused]
    img_fail, imgs = check_images(build)
    failures += img_fail
    notes.append(f"images: {imgs} srcs checked, {len(img_fail)} missing")
    pages = sum(1 for _ in build.rglob("*.html"))
    notes.append(f"links: {pages} pages scanned, {len(link_fail)} broken, "
                 f"{len(allow) - len(unused)} allowed")
    if skipped:
        notes.append(f"snapshot absent: skipped {skipped} checks (urls, feed links, sitemap)")
    return failures, notes


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "verify_site/1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, OSError) as e:
        return 0, str(e).encode()


def run_live(base, snapshot, fetch=_get):
    failures, notes = [], []
    base = base.rstrip("/")
    urls = read_urls(snapshot)
    if not urls:
        return [f"no URLs in {Path(snapshot) / 'urls.txt'}"], notes
    paths = list(dict.fromkeys(urls + list(ALIAS_PATHS) + list(LIVE_EXTRA)))
    bad = 0
    for p in paths:
        status, _ = fetch(base + p)
        if status != 200:
            bad += 1
            failures.append(f"live {p}: HTTP {status or 'error'}")
    notes.append(f"urls: {len(paths) - bad}/{len(paths)} returned 200")
    status, body = fetch(base + "/feed.xml")
    snap_feed = Path(snapshot) / "feed.xml"
    if status != 200:
        failures.append(f"live /feed.xml: HTTP {status or 'error'}")
    elif not snap_feed.is_file():
        failures.append("feed.xml missing from snapshot")
    else:
        f = check_feed(body.decode("utf-8", "replace"), None,
                       snap_feed.read_text(encoding="utf-8"))
        failures += f
        notes.append(f"feed: {'ok' if not f else str(len(f)) + ' problems'}")
    return failures, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", help="live-site snapshot (required with --live)")
    ap.add_argument("--build", help="build directory (default mode)")
    ap.add_argument("--live", metavar="BASE", help="check a running site instead of --build")
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE),
                    help="static file checksums (build mode)")
    ap.add_argument("--allow", default=str(ROOT / "migration" / "site-allowlist.yaml"))
    a = ap.parse_args(argv)
    if bool(a.build) == bool(a.live):
        ap.error("give exactly one of --build and --live")
    if a.live and not a.snapshot:
        ap.error("--live needs --snapshot")

    if a.live:
        failures, notes = run_live(a.live, a.snapshot)
    else:
        failures, notes = run_build(a.build, a.snapshot, load_site_allowlist(a.allow), a.baseline)
    for n in notes:
        print(n)
    for f in failures:
        print("FAIL", f)
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
