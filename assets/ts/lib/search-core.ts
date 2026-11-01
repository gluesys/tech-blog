// DOM-free search core shared by the site UI and tools/verify_search.py.
import { queryVariants } from "./korean-query.ts";

export interface Hit {
  id: string;
  url: string;
  title: string;
  date: string;
  excerpt: string; // Pagefind HTML: escaped text with <mark> around matches
  tags: string[];
}

interface PagefindData {
  url: string;
  excerpt: string;
  meta?: Record<string, string>;
  filters?: Record<string, string[]>;
}
export interface PagefindLike {
  search(q: string): Promise<{ results: { id: string; data(): Promise<PagefindData> }[] }>;
}

const escapeRe = (t: string) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * True when every whitespace-separated token of some variant occurs in the
 * title. A Latin token must not start inside a longer word ("RAID" does not
 * match "GRAID"); Hangul tokens match anywhere (no word spacing in compounds).
 */
export function titleMatches(title: string, variants: string[]): boolean {
  const t = title.toLowerCase();
  return variants.some((v) => {
    const tokens = v.toLowerCase().split(/\s+/).filter(Boolean);
    return tokens.length > 0 &&
      tokens.every((tok) => new RegExp(`(?<![a-z0-9])${escapeRe(tok)}`).test(t));
  });
}

/**
 * Enter opens the active result only when the list belongs to what is typed now.
 * Otherwise the caller must run the typed query first.
 */
export function shouldNavigate(inputValue: string, renderedFor: string | null, pending: boolean): boolean {
  return !pending && renderedFor !== null && inputValue.trim() === renderedFor;
}

/**
 * Run every query variant and merge by result id (original query first), then
 * move title matches to the front, keeping Pagefind's order within each group
 * (Pagefind weighs the body only; the title sits outside the indexed scope).
 * `total` counts every merged hit; `hits` holds at most `limit`.
 */
export async function searchMerged(
  pf: PagefindLike,
  q: string,
  limit = 20,
): Promise<{ hits: Hit[]; total: number }> {
  const variants = queryVariants(q);
  const merged: { id: string; data(): Promise<PagefindData> }[] = [];
  const seen = new Set<string>();
  for (const v of variants) {
    if (!v) continue;
    const res = await pf.search(v);
    for (const r of res.results) {
      if (!seen.has(r.id)) {
        seen.add(r.id);
        merged.push(r);
      }
    }
  }
  const datas = await Promise.all(merged.map((r) => r.data()));
  const all: Hit[] = merged.map((r, i) => {
    const d = datas[i];
    return {
      id: r.id,
      url: d.url,
      title: d.meta?.title ?? d.url,
      date: d.meta?.date ?? "",
      excerpt: d.excerpt,
      tags: d.filters?.tag ?? [],
    };
  });
  const boosted = [
    ...all.filter((h) => titleMatches(h.title, variants)),
    ...all.filter((h) => !titleMatches(h.title, variants)),
  ];
  return { hits: boosted.slice(0, limit), total: all.length };
}
