// Deno helper for tools/verify_search.py: runs the built Pagefind index through
// the same merge code the site UI uses and prints one JSON line per query.
//   deno run -A tools/verify_search.ts <build dir> <query>...
import { queryVariants } from "../assets/ts/lib/korean-query.ts";
import { type PagefindLike, searchMerged } from "../assets/ts/lib/search-core.ts";

const [build, ...queries] = Deno.args;
const abs = await Deno.realPath(build);
const pf = await import(`file://${abs}/pagefind/pagefind.js`) as PagefindLike & { destroy?: () => Promise<void> };
// Pagefind derives result URLs from the file:// location; strip that prefix.
const prefix = `/file:${abs}`;
for (const q of queries) {
  const hits = await searchMerged(pf, q, 5);
  console.log(JSON.stringify({
    query: q,
    variants: queryVariants(q),
    top: hits.map((h) => h.url.startsWith(prefix) ? h.url.slice(prefix.length) : h.url),
  }));
}
await pf.destroy?.();
