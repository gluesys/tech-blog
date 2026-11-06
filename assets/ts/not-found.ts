// 404 page: most misses are old or mistyped post addresses, and the slug in the
// address usually names the topic. Fill the search box with the words from the
// last meaningful path segment so one press of 검색 finds the post.
const FILLER = new Set(["blog", "posts", "page", "tags", "series", "categories", "category", "index", "assets"]);
const MAX_WORDS = 6;

/** Search words guessed from a path, or "" when nothing useful is in it. */
export function guessQuery(pathname: string): string {
  const segments = pathname.split("/").filter(Boolean).reverse();
  for (const seg of segments) {
    let text: string;
    try {
      text = decodeURIComponent(seg);
    } catch (_) {
      continue; // broken percent-encoding: try the segment before it
    }
    const words = text
      .replace(/\.[a-z0-9]+$/i, "")
      .split(/[-_.+\s]+/)
      .filter((w) => w && !/^\d+$/.test(w) && !FILLER.has(w.toLowerCase()));
    if (words.length) return words.slice(0, MAX_WORDS).join(" ");
  }
  return "";
}

export function initNotFound(): void {
  const input = document.querySelector<HTMLInputElement>("form[data-guess] input[name=q]");
  if (!input || input.value) return;
  input.value = guessQuery(location.pathname);
  // placeholder-marquee.ts hides its moving hint on "input"; a value set from code fires none
  input.dispatchEvent(new Event("input", { bubbles: true }));
}
