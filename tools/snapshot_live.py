#!/usr/bin/env python3
"""Snapshot the live Jekyll site (the migration baseline). Stdlib only."""
import argparse
import re
import sys
import time
import xml.etree.ElementTree as ET
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse


def fetch(url, retries=3, timeout=30):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tech-blog-snapshot/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    base = args.base.rstrip("/")
    out = Path(args.out)

    sitemap = fetch(base + "/sitemap.xml")
    root = ET.fromstring(sitemap)
    locs = [(e.text or "").strip() for e in root.iter() if e.tag.endswith("}loc") or e.tag == "loc"]
    raw_paths = sorted({urlparse(u).path for u in locs if u})
    if not raw_paths:
        print("sitemap has no entries", file=sys.stderr)
        return 1
    paths = sorted(unquote(p) for p in raw_paths)

    out.mkdir(parents=True, exist_ok=True)
    (out / "sitemap.xml").write_bytes(sitemap)
    (out / "feed.xml").write_bytes(fetch(base + "/feed.xml"))

    posts = [p for p in raw_paths if p.startswith("/blog/") and p.endswith(".html")]
    for p in posts:
        dest = out / "posts" / unquote(p).lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(fetch(base + p))
    (out / "urls.txt").write_text("".join(p + "\n" for p in paths), encoding="utf-8")
    print(f"saved {len(posts)} posts, {len(paths)} urls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
