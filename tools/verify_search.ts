// Node helper for tools/verify_search.py: runs the built Pagefind index through
// the same merge code the site UI uses and prints one JSON line per query.
//   node tools/verify_search.ts <build dir> <query>...
import { readFile, realpath } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { queryVariants } from "../assets/ts/lib/korean-query.ts";
import { type PagefindLike, searchMerged } from "../assets/ts/lib/search-core.ts";

// Pagefind fetches its index chunks relative to pagefind.js; Node's fetch has no
// file: scheme, so serve those requests from disk.
const netFetch = globalThis.fetch;
globalThis.fetch = (async (input: string | URL | Request, init?: RequestInit) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  if (!url.startsWith("file:")) return netFetch(input, init);
  try {
    return new Response(await readFile(fileURLToPath(url)));
  } catch {
    return new Response(null, { status: 404 });
  }
}) as typeof fetch;

const [build, ...queries] = process.argv.slice(2);
const abs = await realpath(build);
const pf = await import(pathToFileURL(`${abs}/pagefind/pagefind.js`).href) as PagefindLike & { destroy?: () => Promise<void> };
// Pagefind derives result URLs from the file:// location; strip that prefix.
const prefix = `/file:${abs}`;
for (const q of queries) {
  const { hits } = await searchMerged(pf, q, 5);
  console.log(JSON.stringify({
    query: q,
    variants: queryVariants(q),
    top: hits.map((h) => h.url.startsWith(prefix) ? h.url.slice(prefix.length) : h.url),
  }));
}
await pf.destroy?.();
