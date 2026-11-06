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

const LATIN_DIGIT = /[a-z0-9]/;

/**
 * Does `tok` occur in `title` (both lower case)? A token that starts with a
 * Latin letter or digit must not start inside a longer Latin word ("raid" does
 * not match "graid"); any other token (Hangul, punctuation) matches anywhere.
 * No regex lookbehind: Safari before 16.4 throws on it.
 */
function hasToken(title: string, tok: string): boolean {
  const needsBoundary = LATIN_DIGIT.test(tok[0]);
  let from = 0;
  for (;;) {
    const i = title.indexOf(tok, from);
    if (i < 0) return false;
    if (!needsBoundary || i === 0 || !LATIN_DIGIT.test(title[i - 1])) return true;
    from = i + 1;
  }
}

/** True when every whitespace-separated token of some variant occurs in the title (see hasToken). */
export function titleMatches(title: string, variants: string[]): boolean {
  const t = title.toLowerCase();
  return variants.some((v) => {
    const tokens = v.toLowerCase().split(/\s+/).filter(Boolean);
    return tokens.length > 0 && tokens.every((tok) => hasToken(t, tok));
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
