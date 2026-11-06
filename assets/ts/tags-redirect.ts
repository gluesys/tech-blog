// Old tag links looked like /tags#<raw tag>. On the /tags/ page, map such a
// hash to the canonical tag page. The lookup table is emitted by Hugo into
// <script type="application/json" id="tag-map">: normalized raw tag (also
// every alias in data/tag_aliases.yaml) -> "/tags/<slug>/".

// Same normalization as tools/tags.py norm_key: whitespace collapsed, case
// folded; NFC added because browsers may deliver hashes decomposed.
export function normalize(tag: string): string {
  return tag.normalize("NFC").replace(/\s+/g, " ").trim().toLowerCase();
}

/**
 * Return the path to redirect to for a location hash, or null when the hash
 * is empty, malformed, or names no known tag. `aliases` maps normalized tag
 * names to a tag value and `slug` turns that value into the target path.
 */
export function targetFor(
  hash: string,
  aliases: Record<string, string>,
  slug: (tag: string) => string,
): string | null {
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!raw) return null;
  let decoded: string;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return null;
  }
  const key = normalize(decoded);
  if (!Object.prototype.hasOwnProperty.call(aliases, key)) return null;
  return slug(aliases[key]);
}

interface Page {
  location?: { hash: string; replace(url: string): void };
  document?: { getElementById(id: string): { textContent: string | null } | null };
}

const page = globalThis as unknown as Page;
if (page.location && page.document && page.location.hash) {
  const el = page.document.getElementById("tag-map");
  if (el && el.textContent) {
    try {
      const target = targetFor(
        page.location.hash,
        JSON.parse(el.textContent),
        (path) => path,
      );
      if (target) page.location.replace(target);
    } catch {
      // A broken map must never break the tag index itself.
    }
  }
}
