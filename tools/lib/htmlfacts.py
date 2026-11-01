"""Fact extraction from rendered blog HTML (stdlib only).

Every function takes full page HTML and a root CSS class; only content inside
the first element carrying that class is considered.
"""
import re
from html.parser import HTMLParser
from urllib.parse import unquote

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style"}
BLOCK = {"p", "li", "ul", "ol", "div", "h1", "h2", "h3", "h4", "h5", "h6",
         "pre", "blockquote", "table", "tr", "td", "th", "br", "hr", "figure",
         "figcaption", "dl", "dt", "dd", "section", "article", "header",
         "footer", "center"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _Facts(HTMLParser):
    def __init__(self, root):
        super().__init__(convert_charrefs=True)
        self.root = root
        self.depth = 0          # nesting depth inside root (0 = not inside)
        self.done = False
        self.stack = []         # open non-void tags inside root
        self.headings = []      # (id, text)
        self.imgs = []
        self.fn_defs = []
        self.fn_refs = []
        self.hrefs = []
        self.text = []
        self._heading = None    # [id, [text parts], tag]
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.done:
            return
        if self.depth and tag in BLOCK:
            self.text.append(" ")
        if not self.depth:
            if self.root in (a.get("class") or "").split():
                self.depth = 1
                self.stack = [tag]
                if tag in VOID:
                    self.depth = 0
                    self.done = True
                self._record(tag, a)
            return
        if tag not in VOID:
            self.stack.append(tag)
            self.depth += 1
            if tag in SKIP_TEXT:
                self._skip += 1
        self._record(tag, a)

    def handle_startendtag(self, tag, attrs):
        if self.depth and not self.done:
            if tag in BLOCK:
                self.text.append(" ")
            self._record(tag, dict(attrs))

    def _record(self, tag, a):
        i = a.get("id")
        if i:
            if i.startswith("fn:"):
                self.fn_defs.append(i)
            elif i.startswith("fnref:"):
                self.fn_refs.append(i)
            if tag in HEADINGS:
                self._heading = [i, [], tag]
        if tag == "img" and a.get("src") is not None:
            self.imgs.append(unquote(a["src"]))
        if tag == "a" and a.get("href") is not None:
            self.hrefs.append(a["href"])

    def handle_endtag(self, tag):
        if not self.depth or tag in VOID:
            return
        if tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            self.depth -= 1
            if t in SKIP_TEXT:
                self._skip = max(0, self._skip - 1)
            if t in BLOCK:
                self.text.append(" ")
            if self._heading and t == self._heading[2]:
                self.headings.append(
                    (self._heading[0], _norm("".join(self._heading[1]))))
                self._heading = None
            if t == tag:
                break
        if self.depth == 0:
            self.done = True

    def handle_data(self, data):
        if not self.depth or self._skip:
            return
        self.text.append(data)
        if self._heading:
            self._heading[1].append(data)


def _norm(s):
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def _parse(html, root):
    p = _Facts(root)
    p.feed(html)
    p.close()
    return p


def has_root(html, root):
    """True if some element carries the root class."""
    p = _parse(html, root)
    return p.done or p.depth > 0


def heading_ids(html, root):
    return _parse(html, root).headings


def img_srcs(html, root):
    return _parse(html, root).imgs


def footnotes(html, root):
    p = _parse(html, root)
    return p.fn_defs, p.fn_refs


def links(html, root):
    return _parse(html, root).hrefs


def body_text(html, root):
    return _norm("".join(_parse(html, root).text))
