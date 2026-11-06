import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import verify_migration as vm  # noqa: E402

URL = "/blog/2020/01/02/post.html"


def live(body):
    return f'<html><body><div class="post-content">{body}</div></body></html>'


def built(body):
    return ('<html><body><h1>T</h1>'
            f'<div class="prose" data-pagefind-body>{body}</div></body></html>')


BODY = ('<h2 id="intro">Intro</h2><p>Hello <img src="/assets/a%20b.PNG"> world'
        '<sup id="fnref:1"><a href="#fn:1">1</a></sup></p>'
        '<div class="footnotes"><ol><li id="fn:1">Note</li></ol></div>')


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.snap = base / "snap"
        self.build = base / "build"
        self.allow = base / "allow.yaml"
        self.allow.write_text("[]\n", encoding="utf-8")
        self.write(self.snap / "posts" / URL.lstrip("/"), live(BODY))

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_main(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = vm.main(["--build", str(self.build), "--snapshot", str(self.snap),
                            "--allow", str(self.allow), "--content", ""])
        return code, out.getvalue()

    def test_missing_page_fails(self):
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("exists", out)
        self.assertIn(URL, out)

    def test_anchor_diff_fails(self):
        self.write(self.build / URL.lstrip("/"), built(BODY.replace('id="intro"', 'id="other"')))
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("heading_ids", out)

    def test_allowlisted_diff_passes(self):
        self.write(self.build / URL.lstrip("/"), built(BODY.replace('id="intro"', 'id="other"')))
        self.allow.write_text(
            f'- url: "{URL}"\n  check: heading_ids\n  reason: "fixture: renamed anchor"\n',
            encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 0, out)
        self.assertIn("allowed", out)

    def test_allowlist_is_narrow(self):
        # An entry for one check does not excuse another check on the same URL.
        self.write(self.build / URL.lstrip("/"), built(BODY.replace("world", "earth")))
        self.allow.write_text(
            f'- url: "{URL}"\n  check: heading_ids\n  reason: "x"\n', encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("body_text", out)

    def test_unused_allowlist_entry_fails(self):
        self.write(self.build / URL.lstrip("/"), built(BODY))
        self.allow.write_text(
            f'- url: "{URL}"\n  check: heading_ids\n  reason: "stale"\n', encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("unused", out)

    def test_identical_passes(self):
        self.write(self.build / URL.lstrip("/"), built(BODY))
        code, out = self.run_main()
        self.assertEqual(code, 0, out)
        for check in vm.CHECKS:
            self.assertIn(check, out)

    def test_build_root_is_prose_not_earlier_markup(self):
        page = ('<html><body><nav class="x">Hello world</nav>'
                f'<div class="prose" data-pagefind-body>{BODY}</div></body></html>')
        self.write(self.build / URL.lstrip("/"), page)
        code, out = self.run_main()
        self.assertEqual(code, 0, out)

    def test_first_prose_is_the_article(self):
        page = ('<html><body>'
                f'<div class="prose" data-pagefind-body>{BODY}</div>'
                '<div class="prose"><h2 id="x">Other</h2><img src="/o.png">'
                '<p>more text</p></div></body></html>')
        self.write(self.build / URL.lstrip("/"), page)
        code, out = self.run_main()
        self.assertEqual(code, 0, out)

    def test_missing_build_root_fails(self):
        self.write(self.build / URL.lstrip("/"),
                   f'<html><body><div class="content">{BODY}</div></body></html>')
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL root", out)

    def test_missing_live_root_fails(self):
        self.write(self.snap / "posts" / URL.lstrip("/"), "<html><body><p>x</p></body></html>")
        self.write(self.build / URL.lstrip("/"), "<html><body><p>x</p></body></html>")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL root", out)

    def test_missing_snapshot_dir_fails(self):
        self.snap = Path(self.tmp.name) / "nope"
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("no snapshot posts", out)

    def test_empty_snapshot_fails(self):
        (self.snap / "posts" / URL.lstrip("/")).unlink()
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("no snapshot posts", out)


class TagPageTests(unittest.TestCase):
    def test_missing_tag_dir_reported(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "content").mkdir()
            (d / "content" / "a.md").write_text(
                '---\ntitle: "x"\ntags: ["NVMe-oF", "파일 시스템"]\n---\nbody\n',
                encoding="utf-8")
            (d / "build" / "tags" / "NVMe-oF").mkdir(parents=True)
            (d / "build" / "tags" / "NVMe-oF" / "index.html").write_text("x")
            missing = vm.check_tag_pages(d / "build", d / "content")
            self.assertEqual(missing, [("파일 시스템", "tags/파일-시스템/index.html")])


class AllowlistLoaderTests(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.yaml"
            p.write_text(text, encoding="utf-8")
            return vm.load_allowlist(p)

    def test_empty(self):
        self.assertEqual(self.load("# nothing\n[]\n"), [])
        self.assertEqual(self.load(""), [])

    def test_entries(self):
        got = self.load(
            "# comment\n"
            '- url: "/blog/a.html"\n'
            "  check: footnotes\n"
            '  reason: "kramdown uses \\"label\\" numbers: fn:8"\n'
            "\n"
            "- url: /blog/b.html\n"
            "  check: body_text\n"
            "  reason: plain text, with: colon\n")
        self.assertEqual(got, [
            {"url": "/blog/a.html", "check": "footnotes",
             "reason": 'kramdown uses "label" numbers: fn:8'},
            {"url": "/blog/b.html", "check": "body_text",
             "reason": "plain text, with: colon"},
        ])

    def test_rejects_missing_reason(self):
        with self.assertRaises(ValueError):
            self.load('- url: "/a"\n  check: footnotes\n')

    def test_rejects_unknown_check(self):
        with self.assertRaises(ValueError):
            self.load('- url: "/a"\n  check: nope\n  reason: "r"\n')

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            self.load("url /a\n")


if __name__ == "__main__":
    unittest.main()
