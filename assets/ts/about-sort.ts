// About page: reorder the author list by the pressed sort button. The server
// renders 가나다순; ties in the other orders fall back to the name.
type Key = "name" | "last" | "first";

export function compareAuthors(key: Key, a: DOMStringMap, b: DOMStringMap): number {
  const byName = (a.name ?? "").localeCompare(b.name ?? "", "ko");
  switch (key) {
    case "last": return (b.last ?? "").localeCompare(a.last ?? "") || byName;   // newest first
    case "first": return (a.first ?? "").localeCompare(b.first ?? "") || byName; // oldest first
    default: return byName;
  }
}

export function initAboutSort(): void {
  const group = document.querySelector<HTMLElement>(".authors-head .sort");
  const list = document.querySelector<HTMLUListElement>("ul.authors");
  if (!group || !list) return;
  group.hidden = false;
  const buttons = [...group.querySelectorAll<HTMLButtonElement>("button[data-sort]")];
  for (const btn of buttons) {
    btn.addEventListener("click", () => {
      const key = btn.dataset.sort as Key;
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      const items = [...list.children] as HTMLElement[];
      items.sort((x, y) => compareAuthors(key, x.dataset, y.dataset));
      list.append(...items);
    });
  }
}
