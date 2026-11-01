import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import convert_posts as cp  # noqa: E402
from convert_posts import ConversionError  # noqa: E402


def body(md, ids=()):
    return cp.convert_body(md, list(ids))[0]


class LiveUrlTest(unittest.TestCase):
    def test_url_uses_front_matter_date(self):
        self.assertEqual(
            cp.live_url({"date": "2019-12-02"}, "2019-11-22-storage_1_intro.markdown"),
            "/blog/2019/12/02/storage_1_intro.html",
        )

    def test_url_uses_front_matter_date_utc(self):
        self.assertEqual(
            cp.live_url({"date": "2020-01-01 23:30:00"}, "2020-01-01-x.markdown"),
            "/blog/2020/01/01/x.html",
        )
        self.assertEqual(
            cp.live_url({"date": "2020-01-01 08:00:00 +0900"}, "2020-01-01-x.markdown"),
            "/blog/2019/12/31/x.html",
        )

    def test_url_keeps_case(self):
        self.assertEqual(
            cp.live_url({"date": "2025-09-01"}, "2025-03-13-Lustre_FID_2.markdown"),
            "/blog/2025/09/01/Lustre_FID_2.html",
        )


class BodyTest(unittest.TestCase):
    def test_width_attribute(self):
        self.assertEqual(
            body('![a](/x.png){: width="700"}\n'),
            '<img src="/x.png" alt="a" width="700" loading="lazy">\n',
        )

    def test_space_in_path(self):
        self.assertEqual(
            body("![a](/assets/TrueNAS/a b.png)\n"),
            "![a](/assets/TrueNAS/a%20b.png)\n",
        )
        self.assertEqual(body("[t](#### 4. x)\n"), "[t](####%204.%20x)\n")

    def test_footnote_ref_followed_by_parens_untouched(self):
        md = "|글러스터[^6](오픈 소스 네트워크 파일시스템) 볼륨|\n"
        self.assertEqual(body(md), md)

    def test_nomarkdown_unwrapped(self):
        md = "| {::nomarkdown}<ul><li>{:/}가상화[^2] 환경{::nomarkdown}</ul></li>{:/} |\n"
        self.assertEqual(body(md), "| <ul><li>가상화[^2] 환경</ul></li> |\n")

    def test_target_blank(self):
        self.assertEqual(
            body('[t](u){:target="_blank"}를\n'),
            '<a href="u" target="_blank" rel="noopener">t</a>를\n',
        )

    def test_heading_ids_appended(self):
        self.assertEqual(
            body("## pNFS 소개\n\ntext\n", [("pnfs-소개", "pNFS 소개")]),
            "## pNFS 소개 {#pnfs-소개}\n\ntext\n",
        )

    def test_heading_match_with_inline_markup(self):
        md = "## `zfs create`와 **EBUSY**\n"
        self.assertEqual(
            body(md, [("x", "zfs create와 EBUSY")]),
            "## `zfs create`와 **EBUSY** {#x}\n",
        )
        md = "### [링크 *강조*](http://a) &amp; ds_owner_x...\n"
        self.assertEqual(
            body(md, [("y", "링크 강조 & ds_owner_x\u2026")]),
            md[:-1] + " {#y}\n",
        )

    def test_setext_heading(self):
        md = "&nbsp;\n\n마치며\n-----\n\n## 1. A\n----\n"
        self.assertEqual(
            body(md, [("마치며", "마치며"), ("1-a", "1. A")]),
            "&nbsp;\n\n마치며 {#마치며}\n-----\n\n## 1. A {#1-a}\n----\n",
        )

    def test_heading_footnote_number_by_reference_order(self):
        md = "a[^1] b[^8]\n\n## 비교 [^5]\n\n[^1]: x\n[^5]: y\n[^8]: z\n"
        out = body(md, [("비교-", "비교 3")])
        self.assertIn("## 비교 [^5] {#비교-}\n", out)

    def test_heading_text_mismatch_fails(self):
        with self.assertRaises(ConversionError):
            body("## A\n", [("a", "B")])

    def test_heading_mismatch_fails(self):
        with self.assertRaises(ConversionError):
            body("## A\n## B\n", [("a", "A")])
        with self.assertRaises(ConversionError):
            body("## A\n", [("a", "A"), ("b", "B")])

    def test_untouched_constructs(self):
        md = (
            "<center>&#60; x &#62;</center>\n"
            "\n"
            "&nbsp;\n"
            "a  \nb\n"
            "text[^1]\n\n"
            ":clap: :wave:\n\n"
            "    indented code { x}\n"
            "    ![a](b c.png)\n\n"
            '<iframe src="//x" width="700"></iframe>\n'
            "[^1]: note\n"
        )
        self.assertEqual(body(md), md)

    def test_fenced_code_untouched(self):
        md = (
            "```bash\n"
            "# not a heading\n"
            '![a](b c.png){: width="7"}\n'
            "{::nomarkdown}{: .x}\n"
            "```\n"
            "  ~~~\n"
            "  ## nope\n"
            "  ~~~\n"
        )
        self.assertEqual(body(md), md)

    def test_center_isolated(self):
        md = ("para line\n"
              "<center>&#60; cap &#62;</center>  \n"
              "[link](http://x) and `code`\n"
              "tail\n")
        out, notes = cp.convert_body(md, [])
        self.assertEqual(out, (
            "para line\n\n"
            "<center>&#60; cap &#62;</center>  \n\n"
            "[link](http://x) and `code`\n"
            "tail\n"))
        self.assertEqual(sum(n.startswith("center_isolated") for n in notes), 1)

    def test_center_already_isolated_unchanged(self):
        md = "a\n\n<center>&#60; cap &#62;</center>\n\nb\n"
        out, notes = cp.convert_body(md, [])
        self.assertEqual(out, md)
        self.assertFalse(any(n.startswith("center_isolated") for n in notes))

    def test_center_in_fence_unchanged(self):
        md = "```\na\n<center>x</center>\nb\n```\n"
        self.assertEqual(body(md), md)

    def test_center_crlf(self):
        md = "a\r\n<center>x</center>\r\nb\r\n"
        self.assertEqual(body(md), "a\r\n\r\n<center>x</center>\r\n\r\nb\r\n")

    def test_kramdown_in_indented_code_fails(self):
        with self.assertRaises(ConversionError):
            body("text\n\n    ![a](b.png){: width=\"7\"}\n")
        with self.assertRaises(ConversionError):
            body("text\n\n    {::nomarkdown}<b>x</b>{:/}\n")

    def test_inline_code_untouched(self):
        md = 'use `![a](b c.png){: width="7"}` and `{:target="_blank"}` here\n'
        self.assertEqual(body(md), md)

    def test_unknown_kramdown_fails(self):
        with self.assertRaises(ConversionError):
            body("para\n{: .class}\n")
        with self.assertRaises(ConversionError):
            body("{::comment}\nx\n{:/comment}\n")

    def test_crlf_preserved(self):
        md = '![a](/x.png){: width="7"}\r\n\r\n## H\r\n'
        self.assertEqual(
            body(md, [("h", "H")]),
            '<img src="/x.png" alt="a" width="7" loading="lazy">\r\n\r\n## H {#h}\r\n',
        )

    def test_change_notes(self):
        _, notes = cp.convert_body('![a](/x.png){: width="7"}\n## H\n', [("h", "H")])
        self.assertTrue(any("width" in n for n in notes))
        self.assertTrue(any("heading" in n for n in notes))


class FrontMatterTest(unittest.TestCase):
    SRC = (
        "---\n"
        "layout:     post\n"
        'title:      "메타 객체 프로토콜(Meta Object Protocol)에 대하여"\n'
        "date:       2022-01-10\n"
        "author:     권 진영 (gc757489@gmail.com)\n"
        "categories: blog\n"
        "tags:       MOP \n"
        'cover:\t    "/assets/MOP/MOP_cover.png"\n'
        'main:       "/assets/MOP/MOP_cover.png"\n'
        "---\n"
    )

    def test_parse_front_matter(self):
        fm, rest = cp.split_front_matter(self.SRC + "body\n")
        self.assertEqual(rest, "body\n")
        self.assertEqual(fm["title"], '"메타 객체 프로토콜(Meta Object Protocol)에 대하여"')
        self.assertEqual(fm["tags"], "MOP")
        self.assertEqual(fm["cover"], '"/assets/MOP/MOP_cover.png"')

    def test_scalar_tags(self):
        self.assertEqual(cp.raw_tags("MOP"), ["MOP"])
        self.assertEqual(cp.raw_tags("[a, b c,d, ]"), ["a", "b c", "d"])
        fm, _ = cp.split_front_matter(self.SRC)
        out = cp.convert_front_matter(fm, "/blog/2022/01/10/MOP.html", ["MOP"], None)
        self.assertIn('tags: ["MOP"]\n', out)
        self.assertIn("legacy_tags: MOP\n", out)
        self.assertNotIn("layout", out)
        self.assertNotIn("categories", out)
        self.assertIn('url: "/blog/2022/01/10/MOP.html"\n', out)
        self.assertIn("date: 2022-01-10\n", out)
        self.assertIn('title: "메타 객체 프로토콜(Meta Object Protocol)에 대하여"\n', out)
        self.assertIn('author: "권 진영 (gc757489@gmail.com)"\n', out)
        self.assertIn('cover: "/assets/MOP/MOP_cover.png"\n', out)
        self.assertTrue(out.startswith("---\n") and out.endswith("---\n"))

    def test_legacy_tags_verbatim_list(self):
        fm = {"title": '"t"', "date": "2020-01-01", "author": "a", "cover": '"c"',
              "main": '"m"', "tags": "[스토리지, Storage, ]"}
        out = cp.convert_front_matter(fm, "/u", ["스토리지", "Storage"], ("S", 2))
        self.assertIn("legacy_tags: [스토리지, Storage, ]\n", out)
        self.assertIn('tags: ["스토리지", "Storage"]\n', out)
        self.assertIn('series: "S"\nseries_order: 2\n', out)

    def test_series_yaml(self):
        series = cp.load_series(TOOLS.parent / "data" / "series.yaml")
        self.assertEqual(series["storage_1_intro"], ("스토리지 기초 지식", 1))
        self.assertEqual(series["storage_11_DR"], ("스토리지 기초 지식", 11))
        self.assertEqual(series["Lustre_FID_2"], ("Lustre 분석", 2))
        self.assertEqual(len(series), 24)


class PostTest(unittest.TestCase):
    POST = (
        "---\n"
        "layout:     post\n"
        'title:      "T"\n'
        "date:       2020-04-16 14:01:00\n"
        "author:     a (b@c)\n"
        "categories: blog\n"
        "tags:       [x, y]\n"
        'cover:      "/c.png"\n'
        'main:       "/m.png"\n'
        "---\n"
        "\n"
        "## H\n"
        '![a](/x y.png){: width="7"}\n'
    )

    def test_idempotent(self):
        a = cp.convert_post(self.POST, "2020-04-13-p.markdown", [("h", "H")], None, None)
        b = cp.convert_post(self.POST, "2020-04-13-p.markdown", [("h", "H")], None, None)
        self.assertEqual(a, b)
        text, url, notes = a
        self.assertEqual(url, "/blog/2020/04/16/p.html")
        self.assertIn('<img src="/x%20y.png" alt="a" width="7" loading="lazy">', text)
        self.assertIn("## H {#h}\n", text)

    def test_cli_rerun_identical(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            src = d / "src"
            snap = d / "snap"
            src.mkdir()
            (snap / "posts/blog/2020/04/16").mkdir(parents=True)
            (src / "2020-04-13-p.markdown").write_text(self.POST, encoding="utf-8")
            (snap / "urls.txt").write_text("/blog/2020/04/16/p.html\n", encoding="utf-8")
            (snap / "posts/blog/2020/04/16/p.html").write_text(
                '<div class="post-content"><h2 id="h">H</h2></div>', encoding="utf-8")
            args = ["--src", str(src), "--snapshot", str(snap), "--out", str(d / "out"),
                    "--no-tag-map", "--series", str(d / "none.yaml")]
            (d / "none.yaml").write_text("[]\n", encoding="utf-8")
            self.assertEqual(cp.main(args), 0)
            first = (d / "out/2020-04-13-p.md").read_bytes()
            self.assertEqual(cp.main(args), 0)
            self.assertEqual((d / "out/2020-04-13-p.md").read_bytes(), first)
            # CRLF sources keep CRLF in the output body and front matter
            (src / "2020-04-13-p.markdown").write_bytes(
                self.POST.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(cp.main(args), 0)
            out = (d / "out/2020-04-13-p.md").read_bytes()
            self.assertIn(b"## H {#h}\r\n", out)
            self.assertTrue(out.startswith(b"---\r\nurl: "))
            self.assertNotIn(b"\n", out.replace(b"\r\n", b""))
            # a stray .md in --out that no source produced must fail the run
            stray = d / "out/2001-01-01-stray.md"
            stray.write_text("x\n", encoding="utf-8")
            self.assertEqual(cp.main(args), 1)
            self.assertTrue(stray.exists())     # reported, not deleted
            stray.unlink()
            # a live url not produced by any post must fail the run
            (snap / "urls.txt").write_text(
                "/blog/2020/04/16/p.html\n/blog/2099/01/01/q.html\n", encoding="utf-8")
            self.assertEqual(cp.main(args), 1)


if __name__ == "__main__":
    unittest.main()
