#!/usr/bin/env python3
"""Canonical tag aliases for the Gluesys tech blog (stdlib only).

    python3 tools/tags.py table [--src _posts/blog] [--aliases data/tag_aliases.yaml]

prints a Markdown table (raw tag, canonical tag, post count) for owner review.
"""
import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALIASES = ROOT / "data" / "tag_aliases.yaml"

_cache = {}


def norm_key(tag):
    """Comparison key: whitespace collapsed, case-folded."""
    return re.sub(r"\s+", " ", tag).strip().casefold()


def clean(tag):
    return re.sub(r"\s+", " ", tag).strip()


def _parse_scalar(s, lineno):
    s = s.strip()
    if s.startswith('"'):
        try:
            return json.loads(s)
        except ValueError as e:
            raise ValueError(f"line {lineno}: bad quoted scalar {s!r}") from e
    return s


def load_aliases(path=None):
    """Read `"raw": "canonical"` lines -> {norm_key(raw): canonical}."""
    path = Path(path) if path else DEFAULT_ALIASES
    out = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r'^("(?:[^"\\]|\\.)*"|[^":][^:]*?)\s*:\s+(.+)$', line)
        if not m:
            raise ValueError(f"{path}:{n}: cannot parse {line!r}")
        k = norm_key(_parse_scalar(m.group(1), n))
        v = clean(_parse_scalar(m.group(2), n))
        if out.get(k, v) != v:
            raise ValueError(f"{path}:{n}: conflicting mapping for {k!r}")
        out[k] = v
    return out


def _default_aliases():
    if "aliases" not in _cache:
        _cache["aliases"] = load_aliases()
    return _cache["aliases"]


def canonical_tag(tag, aliases):
    return aliases.get(norm_key(tag), clean(tag))


def canonical_tags(raw, aliases=None):
    """Map raw tags to canonical ones; order kept, duplicates removed."""
    if aliases is None:
        aliases = _default_aliases()
    out = []
    for t in raw:
        c = canonical_tag(t, aliases)
        if c and c not in out:
            out.append(c)
    return out


def tag_slug(tag):
    """Path segment Hugo generates for /tags/<term>/ with
    disablePathToLower = true (case kept; verified empirically, Hugo 0.169).

    Whitespace becomes '-' (runs collapse), letters, digits, combining marks
    and `@._~-+#/` are kept, everything else is dropped. '/' stays a path
    separator, so 'I/O' lands in tags/I/O/.
    """
    out = []
    for ch in unicodedata.normalize("NFC", tag.strip()):
        if ch.isspace():
            if not out or out[-1] != "-":
                out.append("-")
        elif ch.isalnum() or unicodedata.category(ch)[0] == "M" or ch in "@._~-+#/":
            out.append(ch)
    return "".join(out)


def canonical_set(aliases):
    return set(aliases.values())


def _count_raw(src):
    sys.path.insert(0, str(ROOT / "tools"))
    from convert_posts import raw_tags
    counts = collections.Counter()
    for p in sorted(Path(src).glob("*.markdown")):
        m = re.search(r"^tags:[ \t]*(.*)$", p.read_text(encoding="utf-8"), re.M)
        if m:
            counts.update(set(raw_tags(m.group(1))))
    return counts


def table(src, aliases):
    counts = _count_raw(src)
    rows = sorted(((canonical_tag(r, aliases), r, n) for r, n in counts.items()),
                  key=lambda x: (x[0].casefold(), x[1].casefold()))
    out = [f"Total: {len(counts)} raw tags, {len({c for c, _, _ in rows})} canonical tags.",
           "", "| Raw tag | Canonical tag | Posts |", "|---|---|---:|"]
    for c, r, n in rows:
        out.append(f"| {r} | {c} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table")
    t.add_argument("--src", default=str(ROOT / "_posts" / "blog"))
    t.add_argument("--aliases", default=str(DEFAULT_ALIASES))
    a = ap.parse_args(argv)
    sys.stdout.write(table(a.src, load_aliases(a.aliases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
