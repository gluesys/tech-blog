#!/usr/bin/env python3
"""Warn when posts use tags that are not canonical (stdlib only).

    python3 tools/check_tags.py content/blog [--strict]

Exit 0 with warnings by default; --strict exits 1 on any non-canonical tag.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tags  # noqa: E402


def front_matter_tags(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return []
    t = re.search(r"^tags:[ \t]*(.*)$", m.group(1), re.M)
    if not t:
        return []
    raw = t.group(1).strip()
    if raw.startswith("["):
        raw = raw[1:-1] if raw.endswith("]") else raw[1:]
        return [x for x in (tags._parse_scalar(p, 0) for p in _split(raw)) if x]
    return [tags._parse_scalar(raw, 0)] if raw else []


def _split(s):
    """Split a flow list on commas outside double quotes."""
    parts, cur, q, esc = [], [], False, False
    for ch in s:
        if esc:
            cur.append(ch); esc = False
        elif ch == "\\" and q:
            cur.append(ch); esc = True
        elif ch == '"':
            cur.append(ch); q = not q
        elif ch == "," and not q:
            parts.append("".join(cur).strip()); cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("content_dir")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--aliases", default=str(tags.DEFAULT_ALIASES))
    a = ap.parse_args(argv)
    aliases = tags.load_aliases(a.aliases)
    canon = tags.canonical_set(aliases)
    bad = 0
    for p in sorted(Path(a.content_dir).rglob("*.md")):
        for t in front_matter_tags(p.read_text(encoding="utf-8")):
            if t not in canon:
                bad += 1
                hint = tags.canonical_tag(t, aliases)
                extra = f" (use {hint!r})" if hint != t else ""
                print(f"warning: {p}: non-canonical tag {t!r}{extra}")
    if bad:
        print(f"{bad} non-canonical tag use(s)", file=sys.stderr)
    return 1 if (bad and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
