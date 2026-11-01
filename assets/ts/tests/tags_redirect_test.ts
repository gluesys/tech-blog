import { targetFor } from "../tags-redirect.ts";

// Keys are normalized raw tags (NFC, collapsed whitespace, lower case); values
// are the tag page paths Hugo emitted into the /tags/ page.
const map: Record<string, string> = {
  "스토리지": "/tags/스토리지/",
  "storage": "/tags/스토리지/",
  "nvme over fabrics": "/tags/NVMe-oF/",
};
const slug = (v: string) => v;

function eq(actual: unknown, expected: unknown) {
  if (actual !== expected) {
    throw new Error(`expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

Deno.test("raw Korean hash", () => {
  eq(targetFor("#스토리지", map, slug), "/tags/스토리지/");
});

Deno.test("percent-encoded Korean hash", () => {
  eq(targetFor("#%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80", map, slug), "/tags/스토리지/");
});

Deno.test("alias hash", () => {
  eq(targetFor("#Storage", map, slug), "/tags/스토리지/");
});

Deno.test("case variant hash", () => {
  eq(targetFor("#storage", map, slug), "/tags/스토리지/");
  eq(targetFor("#STORAGE", map, slug), "/tags/스토리지/");
});

Deno.test("whitespace and encoded spaces collapse", () => {
  eq(targetFor("#NVMe%20over%20%20Fabrics", map, slug), "/tags/NVMe-oF/");
});

Deno.test("NFD input matches NFC key", () => {
  eq(targetFor("#" + "스토리지".normalize("NFD"), map, slug), "/tags/스토리지/");
});

Deno.test("unknown hash is null", () => {
  eq(targetFor("#nothing-here", map, slug), null);
});

Deno.test("empty hash is null", () => {
  eq(targetFor("", map, slug), null);
  eq(targetFor("#", map, slug), null);
});

Deno.test("keys of Object.prototype are not tags", () => {
  eq(targetFor("#constructor", map, slug), null);
  eq(targetFor("#__proto__", map, slug), null);
});

Deno.test("malformed percent-encoding is null and does not throw", () => {
  eq(targetFor("#%E0%A4%A", map, slug), null);
  eq(targetFor("#%", map, slug), null);
});
