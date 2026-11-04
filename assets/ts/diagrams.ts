// Draws ```mermaid blocks with pele (static/third-party/pele-*, loaded before this script only on pages
// that have one). pele follows the container width and colours from CSS variables (prose.css), so
// theme switches need no redraw. A diagram it cannot draw shows pele's error in place of it.
declare const pele: { mount(el: HTMLElement, text: string, options?: object): unknown } | undefined;

export function initDiagrams(): void {
  if (typeof pele === "undefined") return;
  document.querySelectorAll<HTMLElement>(".diagram[data-mermaid]").forEach((box) => {
    const src = box.querySelector("pre")?.textContent ?? "";
    box.replaceChildren();
    pele.mount(box, src);
  });
}

initDiagrams();
