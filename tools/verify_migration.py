#!/usr/bin/env python3
"""Compare the Hugo build with the live-site snapshot (stdlib only).

    python3 tools/verify_migration.py --build build --snapshot migration/snapshot \
        --allow migration/allowlist.yaml [--content content]

For every snapshot post (`<snapshot>/posts/<url path>`) it checks that the
built page exists at the same path, that both pages contain their article
root, and that heading ids, image sources,
footnote ids and body text are equal. The live article root is `.post-content`,
the built one `.prose`. With `--content`, it also checks that every canonical
tag used in content has a built `/tags/<tag_slug>/index.html`.

Exit status is 1 if no snapshot post is found, if any difference is not
covered by an allow-list entry `{url, check, reason}`, or if an allow-list
entry matches nothing.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from lib import htmlfacts  # noqa: E402
from tags import tag_slug  # noqa: E402

LIVE_ROOT = "post-content"
BUILD_ROOT = "prose"
CHECKS = ("exists", "root", "heading_ids", "img_srcs", "footnotes", "body_text")
ALLOW_KEYS = ("url", "check", "reason")

_FACTS = {
    "heading_ids": htmlfacts.heading_ids,
    "img_srcs": htmlfacts.img_srcs,
    "footnotes": lambda h, r: list(map(list, htmlfacts.footnotes(h, r))),
    "body_text": htmlfacts.body_text,
}


def _scalar(s, where):
    s = s.strip()
    if s.startswith('"'):
        try:
            return json.loads(s)
        except ValueError as e:
            raise ValueError(f"{where}: bad quoted scalar {s!r}") from e
    return s


def load_allowlist(path):
    """Parse a YAML list of flat mappings with scalar values:

        - url: "/blog/..."
          check: footnotes
          reason: "..."

    Values are plain scalars or JSON double-quoted strings. A bare `[]` means
    an empty list. Every entry needs exactly url, check and reason.
    """
    entries = []
    cur = None
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
        if key not in ALLOW_KEYS:
            raise ValueError(f"{where}: unknown key {key!r}")
        if key in cur:
            raise ValueError(f"{where}: duplicate key {key!r}")
        cur[key] = _scalar(val, where)
    for i, e in enumerate(entries, 1):
        missing = [k for k in ALLOW_KEYS if not e.get(k)]
        if missing:
            raise ValueError(f"{path}: entry {i} missing {', '.join(missing)}")
        if e["check"] not in CHECKS:
            raise ValueError(f"{path}: entry {i} has unknown check {e['check']!r}")
    return entries


def _describe(check, live, new):
    if check == "body_text":
        sm = difflib.SequenceMatcher(None, live, new, autojunk=False)
        parts = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "equal":
                parts.append(f"{op} live[{i1}:{i2}]={live[i1:i2][:60]!r} "
                             f"build={new[j1:j2][:60]!r}")
        return "; ".join(parts[:5]) + (f"; ... ({len(parts)} edits)" if len(parts) > 5 else "")
    if check == "footnotes":
        live = live[0] + live[1]
        new = new[0] + new[1]
    live_l, new_l = list(map(str, live)), list(map(str, new))
    only_live = [x for x in live_l if x not in new_l]
    only_new = [x for x in new_l if x not in live_l]
    if not only_live and not only_new:
        return f"same items, different order/count (live {len(live_l)}, build {len(new_l)})"
    return f"live only {only_live[:6]}; build only {only_new[:6]}"


def compare(build, snapshot):
    """Yield (url, check, detail-or-None) for every snapshot post and check."""
    posts = Path(snapshot) / "posts"
    for live_path in sorted(posts.rglob("*.html")):
        rel = live_path.relative_to(posts).as_posix()
        url = "/" + rel
        built_path = Path(build) / rel
        if not built_path.is_file():
            yield url, "exists", f"missing {built_path}"
            continue
        yield url, "exists", None
        live_html = live_path.read_text(encoding="utf-8")
        new_html = built_path.read_text(encoding="utf-8")
        missing = [f"{side} .{root}" for side, html, root in
                   (("live", live_html, LIVE_ROOT), ("build", new_html, BUILD_ROOT))
                   if not htmlfacts.has_root(html, root)]
        if missing:
            yield url, "root", "no root element: " + ", ".join(missing)
            continue
        yield url, "root", None
        for check, fn in _FACTS.items():
            a, b = fn(live_html, LIVE_ROOT), fn(new_html, BUILD_ROOT)
            yield url, check, None if a == b else _describe(check, a, b)


def _front_matter_tags(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return []
    t = re.search(r"^tags:[ \t]*(\[.*\])[ \t]*$", m.group(1), re.M)
    return json.loads(t.group(1)) if t else []


def check_tag_pages(build, content):
    """Return [(tag, expected path)] for canonical tags without a built page."""
    used = set()
    for p in sorted(Path(content).rglob("*.md")):
        used.update(_front_matter_tags(p.read_text(encoding="utf-8")))
    missing = []
    for tag in sorted(used):
        rel = f"tags/{tag_slug(tag)}/index.html"
        if not (Path(build) / rel).is_file():
            missing.append((tag, rel))
    return missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--allow", required=True)
    ap.add_argument("--content", default=str(ROOT / "content"),
                    help="content dir for the tag-page check ('' to skip)")
    a = ap.parse_args(argv)

    allow = load_allowlist(a.allow)
    allowed = {(e["url"], e["check"]): e for e in allow}
    used = set()
    stats = {c: {"ok": 0, "allowed": 0, "fail": 0} for c in CHECKS}
    failures, excused = [], []
    posts_dir = Path(a.snapshot) / "posts"
    if not posts_dir.is_dir() or not any(posts_dir.rglob("*.html")):
        print(f"FAIL no snapshot posts under {posts_dir}")
        print("RESULT: FAIL")
        return 1
    for url, check, detail in compare(a.build, a.snapshot):
        if detail is None:
            stats[check]["ok"] += 1
        elif (url, check) in allowed:
            stats[check]["allowed"] += 1
            used.add((url, check))
            excused.append((url, check, allowed[(url, check)]["reason"]))
        else:
            stats[check]["fail"] += 1
            failures.append((url, check, detail))

    print(f"{'check':<12} {'ok':>4} {'allowed':>8} {'fail':>5}")
    for c in CHECKS:
        s = stats[c]
        print(f"{c:<12} {s['ok']:>4} {s['allowed']:>8} {s['fail']:>5}")

    tag_missing = []
    if a.content:
        tag_missing = check_tag_pages(a.build, a.content)
        print(f"tag pages: {len(tag_missing)} missing")

    for url, check, reason in excused:
        print(f"ALLOWED {check} {url}: {reason}")
    for url, check, detail in failures:
        print(f"FAIL {check} {url}: {detail}")
    for tag, rel in tag_missing:
        print(f"FAIL tag_page {tag!r}: missing {rel}")
    unused = [(e["url"], e["check"]) for e in allow if (e["url"], e["check"]) not in used]
    for url, check in unused:
        print(f"FAIL unused allow-list entry {check} {url}")

    bad = failures or tag_missing or unused
    print("RESULT:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
