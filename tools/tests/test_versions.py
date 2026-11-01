import re
import unittest
from pathlib import Path

VERSIONS = Path(__file__).resolve().parent.parent / "versions.env"


def parse(path):
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


class VersionsTest(unittest.TestCase):
    def test_versions_env_is_complete(self):
        env = parse(VERSIONS)
        for key in ("HUGO_VERSION", "HUGO_SHA256", "PAGEFIND_VERSION", "PAGEFIND_SHA256"):
            self.assertIn(key, env)
        for key in ("HUGO_VERSION", "PAGEFIND_VERSION"):
            self.assertRegex(env[key], r"^\d+\.\d+\.\d+$")
        for key in ("HUGO_SHA256", "PAGEFIND_SHA256"):
            self.assertRegex(env[key], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
