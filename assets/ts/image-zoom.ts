// Click (or Enter/Space) on a body image that is shown smaller than its file opens it
// in a full-window <dialog>, fitted to the window. A click anywhere or Esc closes it.
// Images that are already links keep their link.
const SHRUNK = 1.15; // natural width / shown width above which zoom is offered

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
  };
  prose.querySelectorAll<HTMLImageElement>("img").forEach((img) => {
    if (img.complete && img.naturalWidth) setup(img);
    else img.addEventListener("load", () => setup(img), { once: true });
  });
}
