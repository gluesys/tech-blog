import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from lib import htmlfacts  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PNFS = (FIXTURES / "pnfs.html").read_text(encoding="utf-8")


def wrap(inner):
    return f'<html><body><h2 id="outside">Out</h2><div class="post-content">{inner}</div></body></html>'


class HtmlFactsTest(unittest.TestCase):
    def test_heading_ids_korean(self):
        ids = [i for i, _ in htmlfacts.heading_ids(PNFS, "post-content")]
        self.assertEqual(
            ids[:3],
            ["기존-nfs와-병렬-파일-시스템", "pnfs-소개", "pnfs의-구조"],
        )

    def test_footnotes_pnfs(self):
        defs, refs = htmlfacts.footnotes(PNFS, "post-content")
        self.assertIn("fn:1", defs)
        self.assertIn("fnref:1", refs)

    def test_img_srcs_decode_preserves_case_and_korean(self):
        html = wrap('<img src="/assets/TrueNAS/A%20B.PNG"><img src="/assets/한글.png">')
        self.assertEqual(
            htmlfacts.img_srcs(html, "post-content"),
            ["/assets/TrueNAS/A B.PNG", "/assets/한글.png"],
        )

    def test_root_scoping(self):
        html = wrap('<h2 id="inside">In <code>x</code></h2>')
        self.assertEqual(
            htmlfacts.heading_ids(html, "post-content"), [("inside", "In x")]
        )

    def test_links(self):
        html = wrap('<a href="/a%20b">x</a><a href="#fn:1">y</a>')
        self.assertEqual(htmlfacts.links(html, "post-content"), ["/a%20b", "#fn:1"])

    def test_body_text_normalizes_nbsp(self):
        html = wrap("a&nbsp;&nbsp; b\n c")
        self.assertEqual(htmlfacts.body_text(html, "post-content"), "a b c")

    def test_body_text_block_boundaries(self):
        bt = lambda h: htmlfacts.body_text(wrap(h), "post-content")
        self.assertEqual(bt("<p>a</p><p>b</p>"), "a b")
        self.assertEqual(bt("<p>a</p>\n<p>b</p>"), "a b")
        self.assertEqual(bt("<ul><li>x<li>y</ul>"), "x y")
        self.assertEqual(bt("a<code>b</code>c"), "abc")

    def test_multi_class_root(self):
        html = '<div class="prose foo" data-pagefind-body><h2 id="x">X</h2></div>'
        self.assertEqual(htmlfacts.heading_ids(html, "prose"), [("x", "X")])


if __name__ == "__main__":
    unittest.main()
