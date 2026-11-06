import { initToc } from "./toc.ts";
import { initCodeCopy } from "./code-copy.ts";
import { initShare } from "./share.ts";
import { initSearch } from "./search.ts";
import { initTheme } from "./theme.ts";
import { initGiscus } from "./giscus.ts";
import { initImageZoom } from "./image-zoom.ts";
import { initAboutSort } from "./about-sort.ts";
import { initPlaceholderMarquee } from "./placeholder-marquee.ts";
import { initNotFound } from "./not-found.ts";

// Mobile menu: the button toggles the .open class on the header bar and aria-expanded.
const menuBtn = document.querySelector<HTMLButtonElement>(".menu-btn");
const bar = document.querySelector<HTMLElement>(".site-header .bar");
if (menuBtn && bar) {
  menuBtn.addEventListener("click", () => {
    const open = bar.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (e) => {
    if (bar.classList.contains("open") && !bar.contains(e.target as Node)) {
      bar.classList.remove("open");
      menuBtn.setAttribute("aria-expanded", "false");
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && bar.classList.contains("open")) {
      bar.classList.remove("open");
      menuBtn.setAttribute("aria-expanded", "false");
      menuBtn.focus();
    }
  });
}

initToc();
initCodeCopy();
initShare();
initSearch();
initTheme();
initGiscus();
initImageZoom();
initAboutSort();
initPlaceholderMarquee();
initNotFound();
