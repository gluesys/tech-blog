// Marks the TOC entry of the heading currently being read with aria-current.
export function initToc(): void {
  const toc = document.querySelector<HTMLElement>(".toc .toc-nav");
  if (!toc) return;
  const items = new Map<string, HTMLLIElement>();
  toc.querySelectorAll<HTMLAnchorElement>("a[href^='#']").forEach((a) => {
    const li = a.closest("li");
    if (!li) return;
    let id = a.getAttribute("href")!.slice(1);
    try { id = decodeURIComponent(id); } catch { /* keep raw */ }
    items.set(id, li);
  });
  const headings = [...items.keys()]
    .map((id) => document.getElementById(id))
    .filter((h): h is HTMLElement => h !== null);
  if (headings.length === 0) return;

  const visible = new Set<Element>();
  const mark = (current: HTMLElement | undefined) => {
    items.forEach((li) => li.removeAttribute("aria-current"));
    if (current) items.get(current.id)?.setAttribute("aria-current", "true");
  };
  const update = () => {
    // The current heading is the first visible one, else the last one above the viewport.
    const first = headings.find((h) => visible.has(h));
    if (first) return mark(first);
    const above = headings.filter((h) => h.getBoundingClientRect().top < 0);
    mark(above.length ? above[above.length - 1] : headings[0]);
  };
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
      update();
    },
    { rootMargin: "0px 0px -70% 0px" },
  );
  headings.forEach((h) => io.observe(h));
  update();
}
