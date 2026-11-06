// Body images stay inside the text column. One shown smaller than its file is "zoomable":
// - with a mouse, resting the pointer on it for a moment shows a round magnifier (lens) that
//   follows the pointer; moving off the image, scrolling, clicking or Esc hides it;
// - a click (or Enter/Space, or a tap on touch screens) opens the image in a full-window
//   <dialog>, fitted to the window. A click anywhere or Esc closes it.
// Images that are already links keep their link.
const SHRUNK = 1.15; // natural width / shown width above which zoom is offered
const LENS_PX = 320; // lens diameter
const REST_MS = 300; // the pointer must rest this long before the lens shows (not while skimming past)
const MIN_SCALE = 2;
const MAX_SCALE = 4;

/** Lens magnification against the shown image: the file's own detail, at least 2x, at most 4x. */
export function lensScale(naturalWidth: number, shownWidth: number): number {
  if (shownWidth <= 0) return MIN_SCALE;
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, naturalWidth / shownWidth));
}

/** Background offset that puts the point (x, y) of the shown image at the lens centre. */
export function lensOffset(x: number, y: number, scale: number, lens: number): { x: number; y: number } {
  return { x: lens / 2 - x * scale, y: lens / 2 - y * scale };
}

function initLens(): ((img: HTMLImageElement) => void) | null {
  if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return null;
  const lens = document.createElement("div");
  lens.className = "zoom-lens";
  lens.setAttribute("aria-hidden", "true");
  lens.style.width = lens.style.height = `${LENS_PX}px`;
  document.body.append(lens);

  let current: HTMLImageElement | null = null;
  let timer = 0;
  let last = { x: 0, y: 0 };
  const hide = () => {
    window.clearTimeout(timer);
    lens.classList.remove("on");
    current = null;
  };
  const place = () => {
    if (!current) return;
    const r = current.getBoundingClientRect();
    const scale = lensScale(current.naturalWidth, r.width);
    const o = lensOffset(last.x - r.left, last.y - r.top, scale, LENS_PX);
    lens.style.left = `${last.x - LENS_PX / 2}px`;
    lens.style.top = `${last.y - LENS_PX / 2}px`;
    lens.style.backgroundSize = `${r.width * scale}px ${r.height * scale}px`;
    lens.style.backgroundPosition = `${o.x}px ${o.y}px`;
  };
  const show = (img: HTMLImageElement) => {
    current = img;
    lens.style.backgroundImage = `url("${img.currentSrc || img.src}")`;
    place();
    lens.classList.add("on");
  };
  addEventListener("scroll", hide, { passive: true });
  addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });

  return (img) => {
    img.addEventListener("pointermove", (e) => {
      last = { x: e.clientX, y: e.clientY };
      if (current === img) { place(); return; }
      window.clearTimeout(timer);
      timer = window.setTimeout(() => show(img), REST_MS);
    });
    img.addEventListener("pointerleave", hide);
    img.addEventListener("click", hide);
  };
}

export function initImageZoom(): void {
  const prose = document.querySelector(".prose");
  if (!prose || typeof HTMLDialogElement !== "function") return;
  const dialog = document.createElement("dialog");
  dialog.className = "zoom";
  dialog.setAttribute("aria-label", "이미지 크게 보기");
  const big = document.createElement("img");
  big.alt = "";
  dialog.append(big);
  document.body.append(dialog);
  let opener: HTMLElement | null = null;
  dialog.addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => { big.removeAttribute("src"); opener?.focus(); });
  const addLens = initLens();

  const open = (img: HTMLImageElement) => {
    opener = img;
    big.src = img.currentSrc || img.src;
    big.alt = img.alt;
    dialog.showModal();
  };
  const setup = (img: HTMLImageElement) => {
    if (img.closest("a")) return;
    const shown = img.getBoundingClientRect().width;
    if (!shown || img.naturalWidth < shown * SHRUNK) return;
    img.classList.add("zoomable");
    img.tabIndex = 0;
    img.setAttribute("role", "button");
    img.setAttribute("aria-label", `${img.alt || "이미지"} 크게 보기`);
    img.addEventListener("click", () => open(img));
    img.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(img); }
    });
    addLens?.(img);
  };
  prose.querySelectorAll<HTMLImageElement>("img").forEach((img) => {
    if (img.complete && img.naturalWidth) setup(img);
    else img.addEventListener("load", () => setup(img), { once: true });
  });
}
