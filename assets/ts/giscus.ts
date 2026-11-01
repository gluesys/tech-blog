import { giscusAttributes, giscusEnabled, giscusThemeMessage } from "./lib/giscus-core.ts";
import type { GiscusConfig } from "./lib/giscus-core.ts";
import { getTheme } from "./theme.ts";

// Injects the giscus client once the comment area is within 600px of the
// viewport, so pages that are never scrolled that far make no giscus.app
// request. Theme changes are forwarded to the iframe once it exists; before
// that, the script simply starts with the theme current at injection time.
export function initGiscus(): void {
  const host = document.querySelector<HTMLElement>("#comments[data-giscus]");
  if (!host) return;
  let cfg: GiscusConfig;
  try {
    cfg = JSON.parse(host.dataset.giscus ?? "null");
  } catch (_) {
    return;
  }
  if (!giscusEnabled(cfg)) return;

  let injected = false;
  const inject = () => {
    if (injected) return;
    injected = true;
    const script = document.createElement("script");
    script.async = true;
    for (const [k, v] of Object.entries(giscusAttributes(cfg, getTheme()))) script.setAttribute(k, v);
    host.appendChild(script);
  };

  document.addEventListener("themechange", (e) => {
    const theme = (e as CustomEvent<{ theme: "light" | "dark" }>).detail.theme;
    const frame = host.querySelector<HTMLIFrameElement>("iframe.giscus-frame");
    frame?.contentWindow?.postMessage(giscusThemeMessage(theme), "https://giscus.app");
  });

  if (!("IntersectionObserver" in window)) {
    inject();
    return;
  }
  const io = new IntersectionObserver((entries) => {
    if (entries.some((en) => en.isIntersecting)) {
      io.disconnect();
      inject();
    }
  }, { rootMargin: "600px 0px" });
  io.observe(host);
}
