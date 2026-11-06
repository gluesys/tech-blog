// Theme toggle. The pre-paint snippet in head.html applies a stored choice as
// <html data-theme="light|dark"> before CSS loads; with no stored choice the
// attribute is absent and dark.css follows prefers-color-scheme.
//
// Event contract (used by the comments embed): whenever the EFFECTIVE theme
// changes (toggle click, OS change while following the OS, or another tab's
// choice) this dispatches on `document`:
//   new CustomEvent("themechange", { detail: { theme: "light" | "dark" } })
// It is not dispatched on page load; read getTheme() for the initial value.

export type Theme = "light" | "dark";

const KEY = "theme";
const mq = matchMedia("(prefers-color-scheme: dark)");

export function getTheme(): Theme {
  const attr = document.documentElement.dataset.theme;
  if (attr === "light" || attr === "dark") return attr;
  return mq.matches ? "dark" : "light";
}

function store(theme: Theme): void {
  try {
    localStorage.setItem(KEY, theme);
  } catch (_) { /* storage blocked: the choice lasts for this page view */ }
}

export function initTheme(): void {
  const btn = document.querySelector<HTMLButtonElement>(".theme-btn");
  let current = getTheme();

  const sync = () => {
    if (!btn) return;
    const dark = current === "dark";
    btn.setAttribute("aria-pressed", String(dark));
  };
  const apply = (next: Theme, explicit: boolean) => {
    if (explicit) document.documentElement.dataset.theme = next;
    if (next === current) return;
    current = next;
    sync();
    document.dispatchEvent(new CustomEvent("themechange", { detail: { theme: next } }));
  };

  sync();
  btn?.addEventListener("click", () => {
    const next: Theme = getTheme() === "dark" ? "light" : "dark";
    store(next);
    apply(next, true);
  });
  mq.addEventListener("change", () => {
    const attr = document.documentElement.dataset.theme;
    if (attr === "light" || attr === "dark") return; // explicit choice wins
    apply(getTheme(), false);
  });
  addEventListener("storage", (e) => {
    if (e.key !== KEY) return;
    if (e.newValue === "light" || e.newValue === "dark") apply(e.newValue, true);
  });
}
