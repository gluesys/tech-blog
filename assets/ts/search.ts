// Site search: header overlay (press "/" or click the button) and the /search/ page.
// Pagefind is loaded lazily, on first use only.
import { type Hit, type PagefindLike, searchMerged, shouldNavigate } from "./lib/search-core.ts";

const PLACEHOLDER = "ZFS, Lustre, 스냅샷처럼 주제로 검색";
const MSG_EMPTY = "검색어를 입력하세요";
const MSG_ERROR = "검색을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
const noResults = (q: string) => `'${q}'에 대한 글을 찾지 못했습니다. 다른 낱말로 검색해 보세요.`;
const countOf = (n: number) => `${n}개의 글`;

let pagefind: Promise<PagefindLike> | undefined;
function loadPagefind(): Promise<PagefindLike> {
  // A variable keeps the bundler from resolving the URL at build time.
  const url = "/pagefind/pagefind.js";
  pagefind ??= import(url).catch((e) => {
    pagefind = undefined;
    throw e;
  });
  return pagefind;
}

function formatDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[1]}년 ${Number(m[2])}월 ${Number(m[3])}일` : iso;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

interface View {
  status: HTMLElement;
  list: HTMLUListElement;
  active: number;
  renderedFor: string | null; // trimmed query the list was built from
}

function render(view: View, q: string, found: { hits: Hit[]; total: number } | "error" | null, idPrefix: string): void {
  view.list.replaceChildren();
  view.active = -1;
  view.renderedFor = q;
  const hits = found === "error" || found === null ? found : found.hits;
  if (hits === "error") { view.status.textContent = MSG_ERROR; return; }
  if (hits === null) { view.status.textContent = MSG_EMPTY; return; }
  if (!hits.length) { view.status.textContent = noResults(q); return; }
  view.status.textContent = countOf((found as { total: number }).total);
  hits.forEach((h, i) => {
    const li = el("li", "sr-item");
    li.id = `${idPrefix}-${i}`;
    li.setAttribute("role", "option");
    const a = el("a", "sr-link");
    a.href = h.url;
    a.append(el("time", "sr-date", formatDate(h.date)), el("span", "sr-title", h.title));
    const ex = el("span", "sr-excerpt");
    ex.innerHTML = h.excerpt; // Pagefind escapes the text and only adds <mark>
    a.append(ex);
    if (h.tags.length) {
      const t = el("span", "sr-tags");
      h.tags.slice(0, 3).forEach((tag) => t.append(el("span", "sr-tag", tag)));
      a.append(t);
    }
    li.append(a);
    view.list.append(li);
  });
  setActive(view, 0);
}

function setActive(view: View, i: number, input?: HTMLInputElement): void {
  const items = Array.from(view.list.children) as HTMLElement[];
  if (!items.length) return;
  view.active = (i + items.length) % items.length;
  items.forEach((li, n) => li.classList.toggle("active", n === view.active));
  const cur = items[view.active];
  cur.scrollIntoView({ block: "nearest" });
  input?.setAttribute("aria-activedescendant", cur.id);
}

/** Wire an input to a results view; returns a function that runs a query immediately. */
function bind(input: HTMLInputElement, view: View, idPrefix: string, onQuery?: (q: string) => void): (q: string) => void {
  let seq = 0;
  let timer: number | undefined;
  let pending = false; // a debounce timer or a search is outstanding
  const run = async (raw: string) => {
    const q = raw.trim();
    const my = ++seq;
    pending = true;
    onQuery?.(q);
    input.removeAttribute("aria-activedescendant");
    if (!q) { render(view, q, null, idPrefix); pending = false; return; }
    try {
      const pf = await loadPagefind();
      const found = await searchMerged(pf, q);
      if (my === seq) { render(view, q, found, idPrefix); pending = false; }
    } catch {
      if (my === seq) { render(view, q, "error", idPrefix); pending = false; }
    }
  };
  input.addEventListener("input", () => {
    window.clearTimeout(timer);
    pending = true;
    timer = window.setTimeout(() => run(input.value), 150);
  });
  input.addEventListener("keydown", (e) => {
    if (e.isComposing || e.keyCode === 229) return; // 229: Safari reports IME Enter as keyCode 229
    if (e.key === "ArrowDown") { e.preventDefault(); setActive(view, view.active + 1, input); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive(view, view.active - 1, input); }
    else if (e.key === "Enter") {
      if (!shouldNavigate(input.value, view.renderedFor, pending)) {
        // The list is for an older query: run the typed one now instead of opening a stale hit.
        e.preventDefault();
        window.clearTimeout(timer);
        void run(input.value);
        return;
      }
      const a = view.list.children[view.active]?.querySelector("a");
      if (a) { e.preventDefault(); location.assign(a.href); }
    }
  });
  return (q) => { window.clearTimeout(timer); void run(q); };
}

function makeResultsView(idPrefix: string): { view: View; wrap: HTMLElement } {
  const wrap = el("div", "sr-body");
  const status = el("p", "sr-status", MSG_EMPTY);
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  const list = el("ul", "sr-list");
  list.id = `${idPrefix}-list`;
  list.setAttribute("role", "listbox");
  list.setAttribute("aria-label", "검색 결과");
  wrap.append(status, list);
  return { view: { status, list, active: -1, renderedFor: null }, wrap };
}

// ---------------------------------------------------------------- overlay

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';

function buildOverlay(): { root: HTMLElement; input: HTMLInputElement } {
  const root = el("div", "search-overlay");
  root.hidden = true;
  const panel = el("div", "search-panel");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "true");
  panel.setAttribute("aria-label", "글 검색");

  const head = el("div", "search-head");
  const input = el("input", "search-input");
  input.type = "search";
  input.placeholder = PLACEHOLDER;
  input.autocomplete = "off";
  input.setAttribute("aria-label", "글 검색");
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-expanded", "true");
  input.setAttribute("aria-controls", "ov-list");
  const close = el("button", "search-close", "닫기");
  close.type = "button";
  head.append(input, close);

  const { view, wrap } = makeResultsView("ov");
  panel.append(head, wrap);
  root.append(panel);
  document.body.append(root);

  bind(input, view, "ov");
  close.addEventListener("click", () => root.dispatchEvent(new Event("search-close")));
  root.addEventListener("mousedown", (e) => {
    if (e.target === root) root.dispatchEvent(new Event("search-close"));
  });
  return { root, input };
}

function initOverlay(): void {
  const trigger = document.querySelector<HTMLButtonElement>(".nav-search");
  let ov: { root: HTMLElement; input: HTMLInputElement } | undefined;
  let returnTo: HTMLElement | null = null;

  const close = () => {
    if (!ov || ov.root.hidden) return;
    ov.root.hidden = true;
    document.documentElement.classList.remove("search-open");
    trigger?.setAttribute("aria-expanded", "false");
    (returnTo && document.contains(returnTo) ? returnTo : trigger)?.focus();
    returnTo = null;
  };
  const open = (from: HTMLElement | null) => {
    if (!ov) {
      ov = buildOverlay();
      ov.root.addEventListener("search-close", close);
    }
    if (!ov.root.hidden) return;
    returnTo = from && from !== document.body ? from : trigger;
    ov.root.hidden = false;
    document.documentElement.classList.add("search-open");
    trigger?.setAttribute("aria-expanded", "true");
    ov.input.focus();
    ov.input.select();
    void loadPagefind().catch(() => {}); // warm up while the user types
  };

  trigger?.addEventListener("click", () => open(trigger));
  trigger?.setAttribute("aria-haspopup", "dialog");
  trigger?.setAttribute("aria-expanded", "false");

  document.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement | null;
    if (ov && !ov.root.hidden) {
      if (e.key === "Escape") { e.preventDefault(); close(); return; }
      if (e.key === "Tab") {
        const f = Array.from(ov.root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((n) => n.offsetParent !== null);
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        const inside = ov.root.contains(document.activeElement);
        if (e.shiftKey && (document.activeElement === first || !inside)) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && (document.activeElement === last || !inside)) { e.preventDefault(); first.focus(); }
      }
      return;
    }
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey || e.isComposing) return;
    if (t && (t.closest("input, textarea, select") || t.isContentEditable)) return;
    e.preventDefault();
    open(document.activeElement as HTMLElement | null);
  });
}

// ---------------------------------------------------------------- /search/ page

function initPage(): void {
  const root = document.getElementById("search-page");
  if (!root) return;
  const input = root.querySelector<HTMLInputElement>("input[name=q]");
  const slot = root.querySelector<HTMLElement>("[data-results]");
  if (!input || !slot) return;
  const { view, wrap } = makeResultsView("pg");
  slot.append(wrap);
  const run = bind(input, view, "pg", (q) => {
    const u = new URL(location.href);
    if (q) u.searchParams.set("q", q); else u.searchParams.delete("q");
    history.replaceState(null, "", u);
  });
  root.querySelector("form")?.addEventListener("submit", (e) => { e.preventDefault(); run(input.value); });
  const q = new URL(location.href).searchParams.get("q") ?? "";
  input.value = q;
  if (q.trim()) run(q);
}

export function initSearch(): void {
  initOverlay();
  initPage();
}
