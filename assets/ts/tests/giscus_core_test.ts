import { giscusAttributes, giscusEnabled, giscusThemeMessage } from "../lib/giscus-core.ts";

function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

const full = { repo: "gluesys/tech-blog", repoId: "R_x", category: "Comments", categoryId: "DIC_x", mapping: "pathname", lang: "ko" };

Deno.test("disabled when ids are empty or missing", () => {
  eq(giscusEnabled(null), false);
  eq(giscusEnabled({ ...full, repoId: "" }), false);
  eq(giscusEnabled({ ...full, categoryId: "  " }), false);
  eq(giscusEnabled({ ...full, repo: "" }), false);
});

Deno.test("enabled when repo and both ids are set", () => {
  eq(giscusEnabled(full), true);
});

Deno.test("attributes match the agreed values", () => {
  const a = giscusAttributes(full, "dark");
  eq(a, {
    "src": "https://giscus.app/client.js",
    "data-repo": "gluesys/tech-blog",
    "data-repo-id": "R_x",
    "data-category": "Comments",
    "data-category-id": "DIC_x",
    "data-mapping": "pathname",
    "data-strict": "1",
    "data-reactions-enabled": "1",
    "data-emit-metadata": "0",
    "data-input-position": "top",
    "data-theme": "dark",
    "data-lang": "ko",
    "data-loading": "lazy",
    "crossorigin": "anonymous",
  });
});

Deno.test("mapping and lang default", () => {
  const a = giscusAttributes({ ...full, mapping: "", lang: "" }, "light");
  eq([a["data-mapping"], a["data-lang"], a["data-theme"]], ["pathname", "ko", "light"]);
});

Deno.test("theme message shape", () => {
  eq(giscusThemeMessage("dark"), { giscus: { setConfig: { theme: "dark" } } });
});
