// DOM-free giscus logic: deciding whether to render and building the script
// attributes. giscus.ts does the DOM work.

export interface GiscusConfig {
  repo?: string;
  repoId?: string;
  category?: string;
  categoryId?: string;
  mapping?: string;
  lang?: string;
}

export type GiscusTheme = "light" | "dark";

/** Comments render only when both GitHub ids are filled in. */
export function giscusEnabled(cfg: GiscusConfig | null | undefined): boolean {
  return !!cfg && !!cfg.repo?.trim() && !!cfg.repoId?.trim() && !!cfg.categoryId?.trim();
}

/** Attribute map for the giscus client script, in a stable order. */
export function giscusAttributes(cfg: GiscusConfig, theme: GiscusTheme): Record<string, string> {
  return {
    "src": "https://giscus.app/client.js",
    "data-repo": cfg.repo ?? "",
    "data-repo-id": cfg.repoId ?? "",
    "data-category": cfg.category ?? "",
    "data-category-id": cfg.categoryId ?? "",
    "data-mapping": cfg.mapping || "pathname",
    "data-strict": "1",
    "data-reactions-enabled": "1",
    "data-emit-metadata": "0",
    "data-input-position": "top",
    "data-theme": theme,
    "data-lang": cfg.lang || "ko",
    "data-loading": "lazy",
    "crossorigin": "anonymous",
  };
}

/** Message that switches the theme of an already loaded giscus iframe. */
export function giscusThemeMessage(theme: GiscusTheme) {
  return { giscus: { setConfig: { theme } } };
}
