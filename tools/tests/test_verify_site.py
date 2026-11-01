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


def rss(links):
    items = "".join(f"<item><title>t</title><link>{l}</link></item>" for l in links)
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


class FeedTests(unittest.TestCase):
    LINKS = [f"{BASE}/blog/2020/01/{d:02d}/p.html" for d in range(1, 11)]

    def test_feed_item_links_match(self):
        self.assertEqual(vs.check_feed(rss(self.LINKS), rss(self.LINKS)), [])

    def test_feed_order_mismatch_fails(self):
        swapped = [self.LINKS[1], self.LINKS[0]] + self.LINKS[2:]
        self.assertTrue(vs.check_feed(rss(swapped), rss(self.LINKS)))

    def test_feed_wrong_count_fails(self):
        self.assertTrue(vs.check_feed(rss(self.LINKS[:9]), rss(self.LINKS)))

    def test_feed_not_xml_or_not_rss2_fails(self):
        self.assertTrue(vs.check_feed("<rss", rss(self.LINKS)))
        self.assertTrue(vs.check_feed(
            rss(self.LINKS).replace('version="2.0"', 'version="0.91"'),
            rss(self.LINKS)))


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

    def test_unparseable_snapshot_feed_fails_without_traceback(self):
        links = FeedTests.LINKS
        self.assertTrue(vs.check_feed(rss(links), "<rss"))


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
