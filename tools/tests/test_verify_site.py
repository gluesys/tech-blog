import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import verify_site as vs  # noqa: E402

BASE = "https://tech.gluesys.com"


def rss(links, titles=None):
    titles = titles or [f"t{i}" for i in range(len(links))]
    items = "".join(f"<item><title>{t}</title><link>{l}</link></item>"
                    for t, l in zip(titles, links))
    return ('<?xml version="1.0"?><rss version="2.0" '
            'xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>x</title>'
            f"{items}</channel></rss>")


def page(body, head=""):
    return f"<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>"


def refresh(target):
    return page("", f'<meta http-equiv="refresh" content="0; url={target}">')


class Site:
    """A throwaway build directory."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def cleanup(self):
        self._tmp.cleanup()


def post_url(y, m, d, slug="p"):
    return f"{BASE}/blog/{y}/{m:02d}/{d:02d}/{slug}.html"


class FeedTests(unittest.TestCase):
    # 12 posts, newest first; the feed holds the first 10
    ALL = [post_url(2020, 1, d) for d in range(12, 0, -1)]
    PATHS = [l[len(BASE):] for l in ALL]
    LINKS = ALL[:10]
    TITLES = [f"post {d}" for d in range(12, 0, -1)]

    def test_newest_ten_in_order_pass(self):
        self.assertEqual(vs.check_feed(rss(self.LINKS), self.PATHS), [])

    def test_feed_order_mismatch_fails(self):
        swapped = [self.LINKS[1], self.LINKS[0]] + self.LINKS[2:]
        self.assertTrue(vs.check_feed(rss(swapped), self.PATHS))

    def test_feed_missing_newer_post_fails(self):
        older = self.ALL[1:11]
        self.assertTrue(vs.check_feed(rss(older), self.PATHS))

    def test_feed_item_not_a_post_fails(self):
        bad = self.LINKS[:9] + [post_url(2020, 1, 20, "ghost")]
        self.assertTrue(vs.check_feed(rss(bad), self.PATHS))

    def test_feed_wrong_count_fails(self):
        self.assertTrue(vs.check_feed(rss(self.LINKS[:9]), self.PATHS))

    def test_fewer_than_ten_posts_is_not_required(self):
        self.assertTrue(vs.check_feed(rss(self.LINKS[:9]), self.PATHS[:9]))  # 9 != 10 items

    def test_feed_not_xml_or_not_rss2_fails(self):
        self.assertTrue(vs.check_feed("<rss", self.PATHS))
        self.assertTrue(vs.check_feed(
            rss(self.LINKS).replace('version="2.0"', 'version="0.91"'), self.PATHS))

    def test_new_posts_push_old_items_out(self):
        snap = rss(self.LINKS, self.TITLES[:10])
        new = [post_url(2021, 1, d, "new") for d in (3, 2, 1)]
        paths = self.PATHS + [l[len(BASE):] for l in new]
        feed = new + self.LINKS[:7]
        titles = ["n3", "n2", "n1"] + self.TITLES[:7]
        self.assertEqual(vs.check_feed(rss(feed, titles), paths, snap), [])

    def test_migrated_item_with_changed_link_fails(self):
        snap = rss(self.LINKS, self.TITLES[:10])
        changed = list(self.LINKS)
        changed[4] = changed[4].replace("p.html", "p2.html")
        paths = self.PATHS + [changed[4][len(BASE):]]
        out = vs.check_feed(rss(changed, self.TITLES[:10]), paths, snap)
        self.assertTrue(any("post 8" in m for m in out), out)

    def test_same_day_posts_may_swap(self):
        links = [post_url(2020, 1, 12 - i, "x") for i in range(8)] + \
                [post_url(2020, 1, 3, "a"), post_url(2020, 1, 3, "b")]
        paths = [l[len(BASE):] for l in links]
        self.assertEqual(vs.check_feed(rss(links), paths), [])
        swapped = links[:8] + [links[9], links[8]]
        self.assertEqual(vs.check_feed(rss(swapped), paths), [])

    def test_unparseable_snapshot_feed_fails_without_traceback(self):
        self.assertTrue(vs.check_feed(rss(self.LINKS), self.PATHS, "<rss"))


class PostFileTests(unittest.TestCase):
    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)
        self.site.write("blog/index.html", refresh(f"{BASE}/posts/"))

    def test_plain_file_ok(self):
        self.site.write("blog/2026/12/01/new-post.html", page("", ""))
        self.assertEqual(vs.check_post_files(self.site.root), [])

    def test_directory_style_post_fails(self):
        self.site.write("blog/2026/12/01/new-post.html/index.html", page("", ""))
        self.assertEqual(len(vs.check_post_files(self.site.root)), 1)

    def test_date_prefixed_slug_fails(self):
        self.site.write("blog/2026/12/01/2026-12-01-new-post.html", page("", ""))
        self.assertEqual(len(vs.check_post_files(self.site.root)), 1)


class AliasTests(unittest.TestCase):
    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)

    def test_alias_pages_exist(self):
        for p in vs.ALIAS_PATHS:
            self.site.write(p.strip("/") + "/index.html", refresh(f"{BASE}/posts/"))
        self.assertEqual(vs.check_aliases(self.site.root), [])

    def test_alias_missing_or_wrong_target_fails(self):
        for p in vs.ALIAS_PATHS:
            self.site.write(p.strip("/") + "/index.html", refresh(f"{BASE}/posts/"))
        (self.site.root / "page3/index.html").unlink()
        self.site.write("page4/index.html", refresh(f"{BASE}/tags/"))
        out = vs.check_aliases(self.site.root)
        self.assertEqual(len(out), 2)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)

    def run_links(self, allow=()):
        return vs.check_links(self.site.root, allow)

    def test_valid_links_pass(self):
        self.site.write("index.html", page(
            '<a href="/posts/">a</a><a href="/posts/#top">b</a>'
            '<a href="/blog/x.html#s1">c</a><a href="https://example.com/n">d</a>'
            '<a href="mailto:a@b.c">e</a>'))
        self.site.write("posts/index.html", page('<h2 id="top">T</h2>'))
        self.site.write("blog/x.html", page('<h2 id="s1">S</h2>'))
        self.assertEqual(self.run_links()[0], [])

    def test_zero_links_scanned_fails(self):
        self.site.write("index.html", page("no links"))
        failures, _ = self.run_links()
        self.assertEqual(len(failures), 1)

    def test_broken_file_fails(self):
        self.site.write("index.html", page('<a href="/nope/">x</a>'))
        failures, _ = self.run_links()
        self.assertEqual(len(failures), 1)

    def test_broken_fragment_fails(self):
        self.site.write("index.html", page('<a href="/p/#missing">x</a><a href="#also">y</a>'))
        self.site.write("p/index.html", page('<h2 id="here">H</h2>'))
        failures, _ = self.run_links()
        self.assertEqual(len(failures), 2)

    def test_text_fragment_skipped(self):
        self.site.write("index.html", page('<a href="/p/#:~:text=hello%20world">x</a>'))
        self.site.write("p/index.html", page("<p>hello world</p>"))
        self.assertEqual(self.run_links()[0], [])

    def test_percent_decoded_paths_and_fragments(self):
        self.site.write("index.html", page(
            '<a href="/blog/a%20b.html#%EA%B0%80">x</a><a href="/tags/%EA%B0%80/">y</a>'))
        self.site.write("blog/a b.html", page('<h2 id="가">G</h2>'))
        self.site.write("tags/가/index.html", page(""))
        self.assertEqual(self.run_links()[0], [])

    def test_relative_links_and_site_host(self):
        self.site.write("blog/x.html", page(
            f'<a href="y.html">y</a><a href="{BASE}/posts/">p</a>'))
        self.site.write("blog/y.html", page(""))
        self.site.write("posts/index.html", page(""))
        self.assertEqual(self.run_links()[0], [])

    def test_allowlist_excuses_and_unused_fails(self):
        self.site.write("blog/x.html", page('<a href="/gone/">x</a>'))
        entry = {"page": "/blog/x.html", "href": "/gone/", "reason": "dead on live too"}
        failures, unused = self.run_links([entry])
        self.assertEqual((failures, unused), ([], []))
        stale = {"page": "/blog/x.html", "href": "/other/", "reason": "stale"}
        failures, unused = self.run_links([entry, stale])
        self.assertEqual(failures, [])
        self.assertEqual(unused, [stale])


class WildcardAllowTests(unittest.TestCase):
    def test_wildcard_page_matches_every_page(self):
        site = Site()
        self.addCleanup(site.cleanup)
        site.write("a/index.html", page('<a href="/gone/">x</a>'))
        site.write("b/index.html", page('<a href="/gone/">x</a>'))
        entry = {"page": "*", "href": "/gone/", "reason": "r"}
        self.assertEqual(vs.check_links(site.root, [entry]), ([], []))


class TagMapTests(unittest.TestCase):
    ALIASES = {"storage": "스토리지", "스토리지": "스토리지"}

    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)
        self.site.write("tags/스토리지/index.html", page(""))

    def tags_page(self, table):
        self.site.write("tags/index.html", page(
            '<script type="application/json" id="tag-map">%s</script>' % table))

    def test_complete_map_passes(self):
        self.tags_page('{"storage":"/tags/%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80/",'
                       '"스토리지":"/tags/스토리지/"}')
        self.assertEqual(vs.check_tag_map(self.site.root, self.ALIASES), [])

    def test_missing_alias_dangling_target_and_missing_script_fail(self):
        self.tags_page('{"스토리지":"/tags/스토리지/","x":"/tags/nope/"}')
        out = vs.check_tag_map(self.site.root, self.ALIASES)
        self.assertEqual(len(out), 2)
        self.site.write("tags/index.html", page(""))
        self.assertTrue(vs.check_tag_map(self.site.root, self.ALIASES))


class StaticAndSitemapTests(unittest.TestCase):
    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)

    def test_static_files_match_baseline(self):
        import hashlib
        data = {"CNAME": b"x\n", "google.html": b"g", "assets/icons/favicon.ico": b"\x00\x01"}
        for rel, d in data.items():
            p = self.site.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(d)
        base = {rel: hashlib.sha256(d).hexdigest() for rel, d in data.items()}
        self.assertEqual(vs.check_static(self.site.root, base), [])
        (self.site.root / "CNAME").write_bytes(b"y\n")
        (self.site.root / "google.html").unlink()
        self.assertEqual(len(vs.check_static(self.site.root, base)), 2)

    def test_baseline_file_parses_and_matches_repo_files(self):
        base = vs.load_static_baseline(vs.DEFAULT_BASELINE)
        self.assertEqual(set(base), {"CNAME", "googlea2b9a3ab05f01437.html",
                                     "assets/icons/favicon.ico"})
        self.assertEqual(vs.check_static(ROOT / "static", base), [])
        self.site.write("b.txt", "nothex  CNAME\n")
        with self.assertRaises(ValueError):
            vs.load_static_baseline(self.site.root / "b.txt")

    def test_sitemap_must_cover_snapshot(self):
        snap = ("<urlset><url><loc>%s/a/</loc></url><url><loc>%s/blog/</loc></url></urlset>"
                % (BASE, BASE))
        new = "<urlset><url><loc>%s/a/</loc></url></urlset>" % BASE
        self.assertEqual(len(vs.check_sitemap(new, snap, set())), 1)
        self.assertEqual(vs.check_sitemap(new, snap, {"/blog/"}), [])
        self.assertTrue(vs.check_sitemap(new, "<urlset/>", set()))
        self.assertTrue(vs.check_sitemap(new, "<urlset", set()))


class MainTests(unittest.TestCase):
    def test_empty_inputs_fail(self):
        site = Site()
        self.addCleanup(site.cleanup)
        site.write("snap/urls.txt", "")
        site.write("allow.yaml", "[]\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = vs.main(["--build", str(site.root / "nobuild"),
                            "--snapshot", str(site.root / "snap"),
                            "--allow", str(site.root / "allow.yaml")])
        self.assertEqual(code, 1)
        self.assertIn("RESULT: FAIL", buf.getvalue())


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.site = Site()
        self.addCleanup(self.site.cleanup)

    def test_existing_images_pass_case_and_korean(self):
        for rel in ("assets/a/Shot.PNG", "assets/a/한글 사진.jpg", "assets/b.png"):
            p = self.site.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x")
        self.site.write("blog/2020/01/01/p.html", page(
            '<img src="/assets/a/Shot.PNG"><img src="/assets/a/%ED%95%9C%EA%B8%80%20%EC%82%AC%EC%A7%84.jpg">'
            '<img src="/assets/b.png" srcset="/assets/b.png 1x, /assets/a/Shot.PNG 2x">'
            '<img src="https://example.com/x.png"><img src="data:image/gif;base64,AAAA">'))
        self.assertEqual(vs.check_images(self.site.root), ([], 7))

    def test_missing_image_and_wrong_case_fail(self):
        (self.site.root / "assets").mkdir()
        (self.site.root / "assets" / "a.png").write_bytes(b"x")
        self.site.write("index.html", page(
            '<img src="/assets/gone.png"><img src="/assets/A.png">'
            '<img src="/assets/a.png" srcset="/assets/a.png 1x, /assets/nope.png 2x">'))
        fails, _ = vs.check_images(self.site.root)
        self.assertEqual(len(fails), 3, fails)


class SnapshotOptionalTests(unittest.TestCase):
    def test_build_without_snapshot_skips_snapshot_checks(self):
        site = Site()
        self.addCleanup(site.cleanup)
        for d in ALIAS_DIRS:
            site.write(f"{d}/index.html", refresh(f"{BASE}/posts/"))
        failures, notes = vs.run_build(site.root, None, [])
        self.assertTrue(any("snapshot absent: skipped 3 checks" in n for n in notes), notes)
        self.assertFalse([f for f in failures if f.startswith(("url ", "sitemap", "feed")) and "missing" not in f])

    def test_given_snapshot_missing_still_fails(self):
        site = Site()
        self.addCleanup(site.cleanup)
        failures, _ = vs.run_build(site.root, site.root / "nosnap", [])
        self.assertTrue(failures)


ALIAS_DIRS = ("blog", "page2", "page3", "page4", "page5", "page6")


class AllowlistParseTests(unittest.TestCase):
    def test_parse(self):
        site = Site()
        self.addCleanup(site.cleanup)
        site.write("a.yaml", '# c\n- page: "/x.html"\n  href: "/y/"\n  reason: "r"\n')
        self.assertEqual(vs.load_site_allowlist(site.root / "a.yaml"),
                         [{"page": "/x.html", "href": "/y/", "reason": "r"}])
        site.write("b.yaml", '- page: "/x.html"\n  href: "/y/"\n')
        with self.assertRaises(ValueError):
            vs.load_site_allowlist(site.root / "b.yaml")
        site.write("c.yaml", "[]\n")
        self.assertEqual(vs.load_site_allowlist(site.root / "c.yaml"), [])


if __name__ == "__main__":
    unittest.main()
