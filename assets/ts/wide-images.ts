// Wide images (natural width >= 1080px) are shrunk hard by the 720px body column,
// so on screens with the sidebar they spread into the sidebar's space (CSS: .wide).
// The sticky TOC fades out only while a wide image actually overlaps it.
const MIN_NATURAL = 1080;

function widen(img: HTMLImageElement): HTMLElement | null {
  if (img.naturalWidth < MIN_NATURAL) return null;
  // Widen the block that holds only this image (and its caption) so the caption
  // stays centered under it; an image inside running text is widened alone.
  const parent = img.parentElement;
  const alone = parent && (parent.matches("center, figure") ||
    (parent.matches("p") && parent.textContent?.trim() === "" && parent.querySelectorAll("img").length === 1));
  const box = alone && parent!.parentElement?.classList.contains("prose") ? parent! : img;
  const nw = `${img.naturalWidth}px`;
  box.classList.add("wide");
  box.style.setProperty("--nw", nw);
  // Converted posts put the caption in a <center> right after the image: match its width.
  const caption = box.nextElementSibling;
  if (caption?.matches("center") && !caption.querySelector("img")) {
    caption.classList.add("wide");
    caption.style.setProperty("--nw", nw);
  }
  return box;
}

export function initWideImages(): void {
  const prose = document.querySelector(".prose");
  const toc = document.querySelector<HTMLElement>(".toc");
  if (!prose) return;
  const onScreen = new Set<Element>();
  let frame = 0;
  // The TOC keeps its box while faded (opacity), so its rect is valid either way.
  const update = () => {
    frame = 0;
    if (!toc) return;
    const t = toc.getBoundingClientRect();
    let hit = false;
    for (const el of onScreen) {
      const r = el.getBoundingClientRect();
      if (r.right > t.left && r.left < t.right && r.bottom > t.top && r.top < t.bottom) { hit = true; break; }
    }
    toc.classList.toggle("toc-yield", hit);
  };
  const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
  const io = toc
    ? new IntersectionObserver((entries) => {
      for (const e of entries) e.isIntersecting ? onScreen.add(e.target) : onScreen.delete(e.target);
      schedule();
    })
    : null;
  if (toc) {
    addEventListener("scroll", schedule, { passive: true });
    addEventListener("resize", schedule);
  }
  prose.querySelectorAll<HTMLImageElement>("img").forEach((img) => {
    const apply = () => {
      const box = widen(img);
      if (box && io) io.observe(box);
    };
    if (img.complete && img.naturalWidth) apply();
    else img.addEventListener("load", apply, { once: true });
  });
}
