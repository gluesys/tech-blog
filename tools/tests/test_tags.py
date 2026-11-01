import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import tags  # noqa: E402

ALIASES = ROOT / "data" / "tag_aliases.yaml"


class TagTests(unittest.TestCase):
    def setUp(self):
        self.aliases = tags.load_aliases(ALIASES)

    def canon(self, raw):
        return tags.canonical_tags(raw, self.aliases)

    def test_bilingual_merge(self):
        self.assertEqual(self.canon(["Storage", "스토리지"]), ["스토리지"])

    def test_case_merge(self):
        got = self.canon(["file system", "File System", "Filesystem", "파일시스템"])
        self.assertEqual(got, ["파일 시스템"])

    def test_dedupe_keeps_order(self):
        got = self.canon(["ZFS", "Backup", "zfs", "백업", "Lustre"])
        self.assertEqual(got, ["ZFS", "백업", "Lustre"])

    def test_unknown_tag_passthrough(self):
        self.assertEqual(self.canon(["Brand New  Tag"]), ["Brand New Tag"])

    def test_distinct_concepts_stay_distinct(self):
        self.assertEqual(self.canon(["NVMe", "NVMe over Fabrics"]), ["NVMe", "NVMe-oF"])

    def test_no_canonical_slug_collisions(self):
        seen = {}
        for canon in sorted(set(self.aliases.values())):
            key = tags.tag_slug(canon).lower()
            self.assertNotIn(key, seen, f"{canon!r} and {seen.get(key)!r} collide")
            seen[key] = canon

    def test_every_alias_target_is_a_fixed_point(self):
        for canon in set(self.aliases.values()):
            self.assertEqual(self.canon([canon]), [canon])

    def test_slug_matches_hugo(self):
        # Observed with Hugo 0.169, disablePathToLower = true, taxonomy tags.
        cases = {
            "NVMe-oF": "NVMe-oF",
            "NVMe over Fabrics": "NVMe-over-Fabrics",
            "파일 시스템": "파일-시스템",
            "C++": "C++",
            "C#": "C#",
            "Lustre": "Lustre",
            "I/O": "I/O",
            "NVMe 2.0": "NVMe-2.0",
            "R&D": "RD",
            "Q&A?": "QA",
            "File  System": "File-System",
            "a_b": "a_b",
        }
        for tag, slug in cases.items():
            self.assertEqual(tags.tag_slug(tag), slug, tag)

    def test_scalar_and_loader_quoting(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.yaml"
            p.write_text('# c\n\n"A \\"q\\"": "B: c"\n', encoding="utf-8")
            self.assertEqual(tags.load_aliases(p), {'a "q"': "B: c"})


if __name__ == "__main__":
    unittest.main()
