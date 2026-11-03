// Scrolls a search field's placeholder sideways, but only when it is wider than the field
// (e.g. on phones). Browsers cannot animate ::placeholder, so an aria-hidden copy is laid over
// the empty field while the real placeholder turns transparent; screen readers keep reading the
// real one. The copy holds the text twice, so one cycle ends where it started; it runs three
// cycles and stops (WCAG 2.2.2, cycle count in base.css), pauses on hover, and never runs under
// reduced motion. It keeps running while the empty field has focus, because the header overlay's
// field opens focused; typing hides it.

const GAP_PX = 48; // space between the two copies of the text
const SPEED_PX_PER_S = 45;
const FADE_PX = 10; // soft edges: the box reaches this far into the field's padding and fades out there

/** Distance and duration of one cycle, or null when the text fits and no scrolling is needed. */
export function marqueePlan(textWidth: number, boxWidth: number): { shift: number; seconds: number } | null {
  if (boxWidth <= 0 || textWidth <= boxWidth) return null;
  const shift = Math.ceil(textWidth + GAP_PX);
  return { shift, seconds: Math.round((shift / SPEED_PX_PER_S) * 10) / 10 };
}

/** Adds the scrolling hint to one search field (also used by search.ts for the overlay it builds). */
export function attachPlaceholderMarquee(input: HTMLInputElement) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const host = input.parentElement;
  if (!host) return;
  host.classList.add("ph-host");
  const box = document.createElement("span");
  box.className = "ph-marquee";
  box.setAttribute("aria-hidden", "true");
  const track = document.createElement("span");
  track.className = "ph-track";
  box.append(track);
  host.append(box);

  let text = "";
  const layout = () => {
    text = input.placeholder;
    input.classList.remove("ph-scroll"); // read the real placeholder colour, not the transparent one
    const cs = getComputedStyle(input);
    const padL = parseFloat(cs.paddingLeft), padR = parseFloat(cs.paddingRight);
    box.style.left = `${input.offsetLeft + input.clientLeft + padL - FADE_PX}px`;
    box.style.top = `${input.offsetTop}px`;
    box.style.height = `${input.offsetHeight}px`;
    box.style.width = `${Math.max(0, input.clientWidth - padL - padR + 2 * FADE_PX)}px`;
    box.style.padding = `0 ${FADE_PX}px`;
    box.style.setProperty("--ph-fade", `${FADE_PX}px`);
    box.style.font = cs.font;
    box.style.color = getComputedStyle(input, "::placeholder").color;
    track.textContent = text;
    const plan = marqueePlan(track.scrollWidth, box.clientWidth - 2 * FADE_PX);
    input.classList.toggle("ph-scroll", plan !== null);
    if (!plan) { track.textContent = ""; return; }
    const second = document.createElement("span");
    second.textContent = text;
    second.style.paddingLeft = `${GAP_PX}px`;
    track.append(second);
    track.style.setProperty("--ph-shift", `-${plan.shift}px`);
    track.style.animationDuration = `${plan.seconds}s`;
    // restart the cycles whenever the layout changes
    track.style.animationName = "none";
    void track.offsetWidth;
    track.style.animationName = "";
  };
  const sync = () => box.classList.toggle("ph-off", input.value !== "");

  input.addEventListener("input", sync);
  new ResizeObserver(layout).observe(input);
  new MutationObserver(layout).observe(input, { attributes: true, attributeFilter: ["placeholder"] });
  // the placeholder colour can change with the theme
  new MutationObserver(layout).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", layout);
  document.fonts?.ready.then(layout);
  layout();
  sync();
}

export function initPlaceholderMarquee() {
  document.querySelectorAll<HTMLInputElement>(".hero-search input, .page-search input").forEach(attachPlaceholderMarquee);
}
