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

  // The placeholder colour follows the theme; reading it never touches the animation.
  const paint = () => {
    const scrolling = input.classList.contains("ph-scroll");
    input.classList.remove("ph-scroll"); // read the real placeholder colour, not the transparent one
    box.style.color = getComputedStyle(input, "::placeholder").color;
    input.classList.toggle("ph-scroll", scrolling);
  };
  // Geometry and text. The cycles restart only when the text or the scroll distance changes,
  // so a theme switch or an unrelated resize leaves a running animation where it is.
  let planned = "";
  const layout = () => {
    const text = input.placeholder;
    const cs = getComputedStyle(input);
    const padL = parseFloat(cs.paddingLeft), padR = parseFloat(cs.paddingRight);
    box.style.left = `${input.offsetLeft + input.clientLeft + padL - FADE_PX}px`;
    box.style.top = `${input.offsetTop}px`;
    box.style.height = `${input.offsetHeight}px`;
    box.style.width = `${Math.max(0, input.clientWidth - padL - padR + 2 * FADE_PX)}px`;
    box.style.padding = `0 ${FADE_PX}px`;
    box.style.setProperty("--ph-fade", `${FADE_PX}px`);
    box.style.font = cs.font;
    const probe = document.createElement("span");
    probe.textContent = text;
    probe.style.cssText = "position:absolute;visibility:hidden;white-space:nowrap";
    box.append(probe);
    const plan = marqueePlan(probe.offsetWidth, box.clientWidth - 2 * FADE_PX);
    probe.remove();
    const key = plan ? `${text}|${plan.shift}` : "";
    if (key === planned) return;
    planned = key;
    paint();
    input.classList.toggle("ph-scroll", plan !== null);
    track.textContent = "";
    if (!plan) return;
    const second = document.createElement("span");
    second.textContent = text;
    second.style.paddingLeft = `${GAP_PX}px`;
    track.append(text, second);
    track.style.setProperty("--ph-shift", `-${plan.shift}px`);
    track.style.animationDuration = `${plan.seconds}s`;
    track.style.animationName = "none";
    void track.offsetWidth;
    track.style.animationName = "";
  };
  const sync = () => box.classList.toggle("ph-off", input.value !== "");

  input.addEventListener("input", sync);
  new ResizeObserver(layout).observe(input);
  new MutationObserver(layout).observe(input, { attributes: true, attributeFilter: ["placeholder"] });
  document.addEventListener("themechange", paint); // theme.ts: effective theme changed
  document.fonts?.ready.then(layout);
  paint();
  layout();
  sync();
}

export function initPlaceholderMarquee() {
  document.querySelectorAll<HTMLInputElement>(".hero-search input, .page-search input").forEach(attachPlaceholderMarquee);
}
