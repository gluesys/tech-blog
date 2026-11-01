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

/** Run every query variant; merge by result id, first-seen order (original query first). */
export async function searchMerged(pf: PagefindLike, q: string, limit = 20): Promise<Hit[]> {
  const ids: { id: string; data(): Promise<PagefindData> }[] = [];
  const seen = new Set<string>();
  for (const v of queryVariants(q)) {
    if (!v) continue;
    const res = await pf.search(v);
    for (const r of res.results) {
      if (!seen.has(r.id)) {
        seen.add(r.id);
        ids.push(r);
      }
    }
  }
  const top = ids.slice(0, limit);
  const datas = await Promise.all(top.map((r) => r.data()));
  return top.map((r, i) => {
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
}
