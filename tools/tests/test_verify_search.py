import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify_search as vsr  # noqa: E402


class CaseTests(unittest.TestCase):
    def test_parse_cases_skips_blank_and_comments(self):
        text = "# note\n\nZFS\t/blog/a.html\n씬 프로비저닝\t/blog/b.html\n"
        self.assertEqual(vsr.parse_cases(text),
                         [("ZFS", "/blog/a.html"), ("씬 프로비저닝", "/blog/b.html")])

    def test_parse_cases_rejects_bad_line(self):
        with self.assertRaises(ValueError):
            vsr.parse_cases("ZFS /blog/a.html\n")

    def test_judge_top_five_only(self):
        top = [f"/p{i}" for i in range(6)]
        self.assertEqual(vsr.judge("/p4", top), "PASS")
        self.assertEqual(vsr.judge("/p5", top), "FAIL")
        self.assertEqual(vsr.judge("/x", []), "FAIL")

    def test_shipped_cases_cover_spec_queries(self):
        cases = vsr.parse_cases((vsr.ROOT / "tools" / "search_cases.txt").read_text(encoding="utf-8"))
        queries = {q for q, _ in cases}
        spec = {"ZFS", "Lustre", "스냅샷", "스냅샷을", "중복 제거", "중복제거", "이중화", "NVMe-oF",
                "씬 프로비저닝", "재해복구", "재해 복구", "pNFS", "CXL", "RAID", "백업 방식"}
        self.assertLessEqual(spec, queries)

    def test_render_table_marks_status(self):
        rows = [{"query": "q", "variants": ["q"], "expected": "/e", "top": ["/e"], "status": "PASS"}]
        self.assertIn("| PASS |", vsr.render_table(rows))


if __name__ == "__main__":
    unittest.main()
