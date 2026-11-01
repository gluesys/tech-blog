#!/usr/bin/env python3
"""Convert Jekyll (kramdown) posts to Hugo (Goldmark) content.

Usage:
    python3 tools/convert_posts.py --src _posts/blog --snapshot migration/snapshot \
        --out content/blog [--no-tag-map]

Per post this applies the rules of spec section 5.1 and nothing else:
front matter rewrite, heading IDs from the live snapshot, `{: width}` images,
space-encoded link/image paths, `{::nomarkdown}` unwrapping and
`{:target="_blank"}` links, plus blank lines around `<center>` caption lines
(controller ruling: keeps CommonMark HTML blocks from swallowing Markdown),
and three fixes found by tools/verify_migration.py where CommonMark and
kramdown disagree: non-flanking `**` pairs become <strong>, closing `"` the
Goldmark typographer cannot see become U+201D, and lines after a list item
followed directly by a column-0 fence are indented into the item.
Any other kramdown syntax, a heading mismatch against the snapshot, a stray
.md in the output directory, or a live URL not covered by exactly one post
makes the
run exit 1 without writing anything. Output is deterministic, so re-running
is idempotent. Python 3 standard library only.
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from lib import htmlfacts  # noqa: E402

LIVE_ROOT = "post-content"
FM_KEYS = ("layout", "title", "date", "author", "categories", "tags", "cover", "main")


class ConversionError(Exception):
    pass


# --------------------------------------------------------------------------
# Front matter

def split_front_matter(text):
    """Return ({key: raw value string}, body). Raw values keep their quotes."""
    m = re.match(r"---\r?\n", text)
    if not m:
        raise ConversionError("missing front matter")
    pos = m.end()
    fm = {}
    while True:
        nl = text.find("\n", pos)
        if nl < 0:
            raise ConversionError("unterminated front matter")
        line = text[pos:nl].rstrip("\r")
        pos = nl + 1
        if line.rstrip() == "---":
            return fm, text[pos:]
        if not line.strip():
            continue
        km = re.match(r"([A-Za-z_]+):(.*)$", line)
        if not km or km.group(1) not in FM_KEYS:
            raise ConversionError(f"unknown front matter line: {line!r}")
        if km.group(1) in fm:
            raise ConversionError(f"duplicate front matter key: {km.group(1)}")
        fm[km.group(1)] = km.group(2).strip()


def scalar(raw):
    """Decode a simple YAML scalar (plain, "double" or 'single' quoted)."""
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        inner = raw[1:-1]
        if re.search(r'\\[^"\\]', inner):
            raise ConversionError(f"unsupported escape in {raw!r}")
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if raw[:1] in ("'", '"', "[", "{", "&", "*", "!", "|", ">"):
        raise ConversionError(f"unsupported scalar {raw!r}")
    return raw


def raw_tags(raw):
    """Jekyll `tags` value (flow list or scalar) -> list of tag strings."""
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ConversionError(f"bad tag list {raw!r}")
        return [scalar(t.strip()) for t in raw[1:-1].split(",") if t.strip()]
    return [scalar(raw)] if raw else []


DATE_RE = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})"
    r"(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?)?"
    r"\s*(Z|[+-]\d{2}:?\d{2})?$")


def live_url(fm, filename):
    """Live Jekyll URL: /blog/<front-matter date in UTC>/<filename slug>.html."""
    m = re.match(r"\d{4}-\d{2}-\d{2}-(.+)\.(?:markdown|md)$", filename)
    if not m:
        raise ConversionError(f"unexpected post filename {filename!r}")
    slug = m.group(1)
    d = DATE_RE.match(scalar(fm["date"]).strip())
    if not d:
        raise ConversionError(f"unparsable date {fm['date']!r}")
    y, mo, da, hh, mi, ss, tz = d.groups()
    when = dt.datetime(int(y), int(mo), int(da), int(hh or 0), int(mi or 0),
                       int(ss or 0))
    if tz and tz != "Z":
        sign = 1 if tz[0] == "+" else -1
        digits = tz[1:].replace(":", "")
        offset = dt.timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
        when -= sign * offset
    return f"/blog/{when:%Y/%m/%d}/{slug}.html"


def _q(s):
    return json.dumps(s, ensure_ascii=False)


def convert_front_matter(fm, url, tags, series):
    """Hugo front matter (YAML, with --- fences, '\\n' line endings)."""
    for k in ("title", "date", "author", "tags", "cover", "main"):
        if k not in fm:
            raise ConversionError(f"front matter lacks {k!r}")
    out = [
        "---",
        f"url: {_q(url)}",
        f"title: {_q(scalar(fm['title']))}",
        f"date: {fm['date']}",
        f"author: {_q(scalar(fm['author']))}",
        "tags: [" + ", ".join(_q(t) for t in tags) + "]",
        f"legacy_tags: {fm['tags']}",
        f"cover: {_q(scalar(fm['cover']))}",
        f"main: {_q(scalar(fm['main']))}",
    ]
    if series:
        out += [f"series: {_q(series[0])}", f"series_order: {series[1]}"]
    out.append("---")
    return "\n".join(out) + "\n"


def load_series(path):
    """Parse data/series.yaml -> {slug: (series name, 1-based order)}."""
    result = {}
    name = None
    order = 0
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        s = line.rstrip()
        if not s.strip() or s.lstrip().startswith("#") or s.strip() == "[]":
            continue
        m = re.match(r"- name: (.+)$", s)
        if m:
            name, order = scalar(m.group(1).strip()), 0
            continue
        if re.match(r"  posts:$", s):
            continue
        m = re.match(r"    - (\S+)$", s)
        if m and name is not None:
            order += 1
            slug = m.group(1)
            if slug in result:
                raise ConversionError(f"{path}:{n}: {slug} listed twice")
            result[slug] = (name, order)
            continue
        raise ConversionError(f"{path}:{n}: unexpected line {line!r}")
    return result


# --------------------------------------------------------------------------
# Body

FENCE_RE = re.compile(r"[ \t]*(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"( {0,3})(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
WIDTH_IMG_RE = re.compile(
    r'!\[([^\[\]]*)\]\(([^()"]*)\)\{:\s*width="([0-9]+%?)"\s*\}')
TARGET_RE = re.compile(
    r'(?<!!)\[([^\[\]]*)\]\(([^()\s"]*)\)\{:\s*target="_blank"\s*\}')
LINK_RE = re.compile(r"(!?)\[([^\[\]]*)\]\(([^()]*)\)")
NOMD_RE = re.compile(r"\{::nomarkdown\}|\{:/\}")
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
KRAMDOWN_IN_CODE_RE = re.compile(r"\{::?")
UNKNOWN_RES = [
    (re.compile(r"\{:"), "kramdown IAL/extension"),
    (re.compile(r"^\*\[[^\]]+\]:"), "kramdown abbreviation"),
    (re.compile(r"^:[ \t]"), "kramdown definition list"),
    (re.compile(r"\{#[^}]*\}"), "explicit header id"),
    (re.compile(r"^\^\s*$"), "kramdown block end marker"),
]


def _enc_spaces(dest):
    return dest.replace(" ", "%20")


def _attr(s):
    return html.escape(s, quote=True)


def plain_heading(md, fn_nums=None):
    """Render heading Markdown to the visible text kramdown would produce.

    fn_nums maps footnote labels to the numbers kramdown shows for them.
    """
    codes = []

    def keep(text):
        codes.append(text)
        return f"\x00{len(codes) - 1}\x00"

    s = CODE_SPAN_RE.sub(lambda m: keep(m.group(2).strip()), md)
    s = re.sub(r"\\([!-/:-@\[-`{-~])", lambda m: keep(m.group(1)), s)
    s = FOOTNOTE_REF_RE.sub(
        lambda m: keep((fn_nums or {}).get(m.group(1), "?")), s)
    s = re.sub(r"!\[[^\[\]]*\]\([^()]*\)", "", s)          # images: no text
    s = re.sub(r"\[([^\[\]]*)\]\([^()]*\)", r"\1", s)        # links -> text
    s = re.sub(r"<[^>]+>", "", s)                            # raw HTML tags
    for _ in range(3):
        s = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", r"\2", s)
        s = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"\1", s)
        s = re.sub(r"\*(?=\S)(.+?)(?<=\S)\*", r"\1", s)
        s = re.sub(r"(?<![0-9A-Za-z])_(?=\S)(.+?)(?<=\S)_(?![0-9A-Za-z])", r"\1", s)
    # kramdown typographic symbols
    s = s.replace("...", "\u2026").replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("<<", "\u00ab").replace(">>", "\u00bb")
    s = html.unescape(s)
    s = re.sub("\x00(\\d+)\x00", lambda m: codes[int(m.group(1))], s)
    return norm_text(s)


def norm_text(s):
    s = unicodedata.normalize("NFC", s.replace("\xa0", " "))
    return re.sub(r"\s+", " ", s).strip()


def _goldmark_id(i):
    # Goldmark's {#id} shorthand stops at ASCII punctuation other than _-:.
    if re.search(r"[!-,/;-@\[-^`{-~]", i) or re.search(r"\s", i):
        return "{id=" + _q(i) + "}"
    return "{#" + i + "}"


def _lines(md):
    for raw in re.split(r"(?<=\n)", md):
        if not raw:
            continue
        if raw.endswith("\r\n"):
            yield raw[:-2], "\r\n"
        elif raw.endswith("\n"):
            yield raw[:-1], "\n"
        else:
            yield raw, ""


def _transform_line(line, notes):
    """Apply rules 3-6 to the parts of a line outside inline code spans."""
    parts = []
    pos = 0
    for m in CODE_SPAN_RE.finditer(line):
        parts.append(_transform_text(line[pos:m.start()], notes))
        parts.append(m.group(0))
        pos = m.end()
    parts.append(_transform_text(line[pos:], notes))
    return "".join(parts)


def _transform_text(line, notes):
    def nomd(m):
        notes.append(f"nomarkdown: {m.group(0)}")
        return ""
    line = NOMD_RE.sub(nomd, line)

    def width(m):
        alt, src, w = m.groups()
        notes.append(f"width: {src} width={w}")
        if " " in src:
            notes.append(f"space_path: {src}")
        return (f'<img src="{_attr(_enc_spaces(src))}" alt="{_attr(alt)}" '
                f'width="{w}" loading="lazy">')
    line = WIDTH_IMG_RE.sub(width, line)

    def target(m):
        text, href = m.groups()
        notes.append(f"target_blank: {href}")
        return f'<a href="{_attr(href)}" target="_blank" rel="noopener">{text}</a>'
    line = TARGET_RE.sub(target, line)

    def spaces(m):
        bang, text, dest = m.groups()
        if not bang and text.startswith("^"):
            return m.group(0)            # footnote ref followed by "(...)"
        if " " not in dest.strip():
            return m.group(0)
        if '"' in dest or "'" in dest:
            raise ConversionError(f"link title not supported: {m.group(0)!r}")
        notes.append(f"space_path: {dest}")
        return f"{bang}[{text}]({_enc_spaces(dest.strip())})"
    return LINK_RE.sub(spaces, line)


def _classify(md):
    """Split md into [line, ending, kind]; kind is fence|code|blank|text."""
    rows = []
    fence = None            # (char, length) while inside a fenced block
    prev_blank = True
    in_icode = False
    for line, end in _lines(md):
        fm = FENCE_RE.match(line)
        if fence:
            if (fm and fm.group(1)[0] == fence[0] and len(fm.group(1)) >= fence[1]
                    and not fm.group(2).strip()):
                fence = None
            rows.append([line, end, "fence"])
            continue
        if fm and not (fm.group(1)[0] == "`" and "`" in fm.group(2)):
            fence = (fm.group(1)[0], len(fm.group(1)))
            rows.append([line, end, "fence"])
            prev_blank = in_icode = False
            continue
        blank = not line.strip()
        if not blank:
            in_icode = bool(re.match(r"(    |\t)", line)) and (prev_blank or in_icode)
        prev_blank = blank
        rows.append([line, end, "blank" if blank else "code" if in_icode else "text"])
    if fence:
        raise ConversionError("unterminated fenced code block")
    return rows


FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
SETEXT_RE = re.compile(r" {0,3}(=+|-+)[ \t]*$")
LIST_ITEM_RE = re.compile(r" {0,3}([-+*]|\d+[.)])([ \t]|$)")


def _footnote_numbers(rows):
    """kramdown/Goldmark number footnotes by order of first reference."""
    nums = {}
    for line, _, kind in rows:
        if kind != "text":
            continue
        for m in FOOTNOTE_REF_RE.finditer(CODE_SPAN_RE.sub("", line)):
            nums.setdefault(m.group(1), str(len(nums) + 1))
    return nums


def convert_body(md, heading_ids):
    """Apply body rules; return (new body, change notes).

    heading_ids: [(id, visible text)] of the live page, in document order.
    """
    rows = _classify(md)
    fn_nums = _footnote_numbers(rows)
    notes = []
    headings = list(heading_ids)
    hi = 0

    def take_heading(n, content):
        nonlocal hi
        if hi >= len(headings):
            raise ConversionError(
                f"line {n}: heading {content!r} has no live counterpart "
                f"(live page has {len(headings)} headings)")
        hid, live_text = headings[hi]
        hi += 1
        mine = plain_heading(content, fn_nums)
        if mine != norm_text(live_text):
            raise ConversionError(
                f"line {n}: heading text mismatch: markdown {mine!r} "
                f"vs live {norm_text(live_text)!r} (id {hid!r})")
        notes.append(f"heading: {hid}")
        return _goldmark_id(hid)

    for i, row in enumerate(rows):
        line, end, kind = row
        n = i + 1
        if kind == "code" and KRAMDOWN_IN_CODE_RE.search(line):
            raise ConversionError(
                f"line {n}: kramdown syntax in an indented code line: {line!r}")
        if kind != "text":
            continue
        new = _transform_line(line, notes)
        masked = CODE_SPAN_RE.sub("", new)
        for rx, what in UNKNOWN_RES:
            if rx.search(masked):
                raise ConversionError(f"line {n}: unsupported {what}: {line!r}")
        hm = HEADING_RE.match(line)
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if hm:
            content = re.sub(r"[ \t]+#+$", "", hm.group(3) or "")
            attr = take_heading(n, content)
            prefix = line[: hm.start(3)] if hm.group(3) else line.rstrip()
            new = f"{prefix}{_transform_line(content, [])} {attr}"
        elif (nxt and nxt[2] == "text" and SETEXT_RE.match(nxt[0])
              and not LIST_ITEM_RE.match(line) and not line.lstrip().startswith(("|", "<", ">"))):
            if i > 0 and rows[i - 1][2] == "text":
                raise ConversionError(
                    f"line {n}: multi-line setext heading not supported: {line!r}")
            attr = take_heading(n, line.strip())
            new = f"{new.rstrip()} {attr}"
        if not line.lstrip().startswith("<"):
            new = _cjk_inline(new, notes)
        row[0] = new
    if hi != len(headings):
        raise ConversionError(
            f"heading count mismatch: markdown has {hi}, live has {len(headings)}")
    _indent_lazy_list_fences(rows, notes)
    return _isolate_centers(rows, notes), notes


# Inline spans whose neighbours CommonMark treats as punctuation; masked so the
# CJK rules below never look inside them. Group 1 marks an inline HTML tag.
_MASK_RE = re.compile(
    r"(`+).+?\1"                               # code span
    r"|(<[A-Za-z/!?][^>]*>)"                    # inline HTML tag
    r"|\\[!-/:-@\[-`{-~]"                     # backslash escape
    r"|(?<=\])\([^()]*\)"                       # link destination
    r"|\{(?:#|id=)[^}]*\}[ \t]*$")              # heading attribute
_PH = 0xE000            # first private-use code point used as a placeholder


def _is_ph(ch):
    return ch is not None and _PH <= ord(ch) < _PH + 0x1900


def _ws(ch):
    return ch is None or ch.isspace()


def _punct(ch):
    return ch is not None and (_is_ph(ch) or unicodedata.category(ch)[0] in "PS")


def _left_flanking(prev, nxt):
    return not _ws(nxt) and (not _punct(nxt) or _ws(prev) or _punct(prev))


def _right_flanking(prev, nxt):
    return not _ws(prev) and (not _punct(prev) or _ws(nxt) or _punct(nxt))


def _cjk_inline(line, notes):
    """Rule 10: keep kramdown's emphasis and closing quotes under CommonMark.

    CommonMark delimiter rules make `**(x)**이` (closer between punctuation
    and a letter) and `"x"이` / `"x!"이` (Goldmark typographer) differ from
    kramdown, which is common in Korean text. Such `**` pairs become
    <strong>, and such closing `"` become a literal U+201D, matching what
    kramdown rendered. Lines with unbalanced or 3+ star runs are left alone.
    """
    saved, html_ph = [], set()

    def mask(m):
        ch = chr(_PH + len(saved))
        saved.append(m.group(0))
        if m.group(2):
            html_ph.add(ch)
        return ch
    s = _MASK_RE.sub(mask, line)

    def at(i):
        return s[i] if 0 <= i < len(s) else None

    # ** pairs
    marker = re.match(r"[ \t]*(?:[*+-][ \t]+)?", s).end()   # skip a list marker
    runs = [m for m in re.finditer(r"\*+", s) if m.start() >= marker]
    if runs and all(len(m.group(0)) == 2 for m in runs) and len(runs) % 2 == 0:
        out, pos = [], 0
        for o, c in zip(runs[::2], runs[1::2]):
            if _ws(at(o.end())) or _ws(at(c.start() - 1)):
                break
            if (_left_flanking(at(o.start() - 1), at(o.end()))
                    and _right_flanking(at(c.start() - 1), at(c.end()))):
                continue
            out.append(s[pos:o.start()] + "<strong>" + s[o.end():c.start()] + "</strong>")
            pos = c.end()
            notes.append(f"cjk_strong: {s[o.start():c.end()][:40]}")
        else:
            s = "".join(out) + s[pos:]

    # closing double quotes
    chars = list(s)
    for i, ch in enumerate(chars):
        if ch != '"':
            continue
        prev, nxt = at(i - 1), at(i + 1)
        if _ws(prev) or prev in '\\[{(-*_"\'' or prev in html_ph:
            continue
        if re.match(r"[_*]{1,2}\S|'\w", s[i + 1:]):
            continue
        if _right_flanking(prev, nxt) and not _left_flanking(prev, nxt):
            continue                    # Goldmark already renders a closer
        chars[i] = "\u201d"
        notes.append(f"cjk_quote: {s[max(0, i - 15):i + 5]}")
    s = "".join(chars)
    return re.sub("[\ue000-\uf8ff]",
                  lambda m: saved[ord(m.group(0)) - _PH] if ord(m.group(0)) - _PH < len(saved)
                  else m.group(0), s)


def _indent_lazy_list_fences(rows, notes):
    """Rule 11: a column-0 list item followed directly by a column-0 fence.

    kramdown keeps the fence and the lines after it (up to a blank line or the
    next column-0 list item) inside the item; CommonMark ends the list. Indent
    those lines by the item's content offset so Goldmark nests them too.
    """
    i = 0
    while i < len(rows):
        m = re.match(r"((?:[-+*]|\d+[.)]) +)\S", rows[i][0]) if rows[i][2] == "text" else None
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if not (m and nxt and nxt[2] == "fence" and FENCE_RE.match(nxt[0])
                and not nxt[0][:1].isspace()):
            i += 1
            continue
        pad = " " * len(m.group(1))
        j = i + 1
        while j < len(rows):
            line, _, kind = rows[j]
            if kind == "blank" or (kind != "fence" and LIST_ITEM_RE.match(line)
                                   and not line[:1].isspace()):
                break
            if line.strip():
                rows[j][0] = pad + line
            j += 1
        notes.append(f"list_fence: {rows[i][0][:40]}")
        i = j


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _isolate_centers(rows, notes):
    """Rule 9: surround <center> caption lines with blank lines.

    A `<center>` line starts a CommonMark HTML block that would swallow the
    following lines up to the next blank line (and could interrupt the
    paragraph above), unlike kramdown. The caption line itself is unchanged.
    """
    out = []
    for i, (line, end, kind) in enumerate(rows):
        is_center = (kind == "text" and line.lstrip(" ").startswith("<center>")
                     and "</center>" in line)
        if (is_center and _indent(line) >= 4 and i > 0 and rows[i - 1][2] == "text"
                and _indent(rows[i - 1][0]) < 4):
            is_center = False   # paragraph continuation; isolating makes it code
        if is_center:
            blank_end = end or "\n"
            added = False
            if out and out[-1][2] != "blank":
                out.append(["", blank_end, "blank"])
                added = True
            out.append([line, end or "", kind])
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            if nxt and nxt[2] != "blank":
                if not end:
                    out[-1][1] = "\n"
                out.append(["", blank_end, "blank"])
                added = True
            if added:
                notes.append(f"center_isolated: {line.strip()[:60]}")
            continue
        out.append([line, end, kind])
    return "".join(line + end for line, end, _ in out)


# --------------------------------------------------------------------------
# Whole post / CLI

def convert_post(text, filename, heading_ids, tag_map, series_map):
    """Return (Hugo file text, live url, change notes)."""
    fm, rest = split_front_matter(text)
    url = live_url(fm, filename)
    tags = raw_tags(fm["tags"])
    if tag_map is not None:
        tags = tag_map(tags)
    slug = url.rsplit("/", 1)[1][: -len(".html")]
    series = (series_map or {}).get(slug)
    head = convert_front_matter(fm, url, tags, series)
    if text.startswith("---\r\n"):
        head = head.replace("\n", "\r\n")
    new_body, notes = convert_body(rest, heading_ids)
    return head + new_body, url, notes


CATEGORIES = ("heading", "width", "nomarkdown", "target_blank", "space_path",
              "center_isolated", "cjk_strong", "cjk_quote", "list_fence")


def _summary(notes):
    c = Counter(n.split(":", 1)[0] for n in notes)
    return c, " ".join(f"{k}={c.get(k, 0)}" for k in CATEGORIES)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--series", type=Path, default=REPO / "data" / "series.yaml")
    ap.add_argument("--no-tag-map", action="store_true",
                    help="keep raw tags instead of mapping through tools/tags.py")
    a = ap.parse_args(argv)

    tag_map = None
    if not a.no_tag_map:
        try:
            from tags import canonical_tags  # tools/tags.py (Task 4)
        except ImportError as e:
            print(f"error: tag alias map unavailable ({e}); "
                  "add tools/tags.py or pass --no-tag-map", file=sys.stderr)
            return 1
        tag_map = canonical_tags

    try:
        series_map = load_series(a.series)
    except (OSError, ConversionError) as e:
        print(f"error: series: {e}", file=sys.stderr)
        return 1
    live_urls = (a.snapshot / "urls.txt").read_text(encoding="utf-8").split()

    results = {}
    errors = []
    seen_urls = {}
    totals = Counter()
    posts = sorted(p for p in a.src.iterdir() if p.suffix in (".markdown", ".md"))
    for p in posts:
        try:
            # newline="" keeps CRLF files byte-for-byte
            with p.open(encoding="utf-8", newline="") as fh:
                source = fh.read()
            fm, _ = split_front_matter(source)
            url = live_url(fm, p.name)
            if url not in live_urls:
                raise ConversionError(f"url {url} is not a live url")
            if url in seen_urls:
                raise ConversionError(f"url {url} also produced by {seen_urls[url]}")
            seen_urls[url] = p.name
            snap = a.snapshot / "posts" / (url.lstrip("/"))
            ids = htmlfacts.heading_ids(snap.read_text(encoding="utf-8"), LIVE_ROOT)
            text, _, notes = convert_post(source, p.name, ids, tag_map, series_map)
        except (ConversionError, OSError) as e:
            errors.append(f"{p.name}: {e}")
            continue
        c, line = _summary(notes)
        totals.update(c)
        print(f"{p.name}: {line}")
        results[a.out / (p.stem + ".md")] = text
    missing = sorted(set(live_urls) - set(seen_urls))
    for u in missing:
        errors.append(f"live url {u} is not produced by any post")
    if a.out.is_dir():
        expected = {a.out / (p.stem + ".md") for p in posts}
        for stray in sorted(set(a.out.glob("*.md")) - expected):
            errors.append(f"{stray} was not produced by any source post")
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    a.out.mkdir(parents=True, exist_ok=True)
    written = 0
    for path, text in results.items():
        data = text.encode("utf-8")
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
            written += 1
    print(f"TOTAL posts={len(results)} " +
          " ".join(f"{k}={totals.get(k, 0)}" for k in CATEGORIES) +
          f" written={written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
