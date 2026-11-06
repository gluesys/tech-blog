// About page: reorder the author list by the pressed sort button. The server renders 가나다순
// (what readers without JS get); with JS the list opens in a random order, so no author is always
// first, and 무작위 reshuffles. Ties in the other orders fall back to the name.
type Key = "random" | "name" | "last" | "first";

export function compareAuthors(key: Exclude<Key, "random">, a: DOMStringMap, b: DOMStringMap): number {
  const byName = (a.name ?? "").localeCompare(b.name ?? "", "ko");
  switch (key) {
    case "last": return (b.last ?? "").localeCompare(a.last ?? "") || byName;   // newest first
    case "first": return (a.first ?? "").localeCompare(b.first ?? "") || byName; // oldest first
    default: return byName;
  }
}

/** A shuffled copy (Fisher-Yates); `rand` returns [0, 1) like Math.random. */
export function shuffled<T>(items: readonly T[], rand: () => number = Math.random): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export function initAboutSort(): void {
  const group = document.querySelector<HTMLElement>(".authors-head .sort");
  const list = document.querySelector<HTMLUListElement>("ul.authors");
  if (!group || !list) return;
  const buttons = [...group.querySelectorAll<HTMLButtonElement>("button[data-sort]")];
  const apply = (btn: HTMLButtonElement) => {
    const key = btn.dataset.sort as Key;
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    const items = [...list.children] as HTMLElement[];
    list.append(...(key === "random" ? shuffled(items) : items.sort((x, y) => compareAuthors(key, x.dataset, y.dataset))));
  };
  for (const btn of buttons) btn.addEventListener("click", () => apply(btn));
  const start = buttons.find((b) => b.dataset.sort === "random");
  if (start) apply(start);
  group.hidden = false;
}
