import { test } from "node:test";
import { compareAuthors } from "../about-sort.ts";

function order(key: "name" | "last" | "first" | "count", rows: Record<string, string>[]): string[] {
  return [...rows].sort((a, b) => compareAuthors(key, a, b)).map((r) => r.name);
}
function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}
const rows = [
  { name: "이헌제", last: "2026-06-24", first: "2024-06-03", count: "2" },
  { name: "고경훈", last: "2021-05-20", first: "2021-05-20", count: "1" },
  { name: "박주형", last: "2024-06-10", first: "2019-11-22", count: "26" },
  { name: "김경표", last: "2018-11-02", first: "2018-11-02", count: "1" },
];

test("name: 가나다순", () => eq(order("name", rows), ["고경훈", "김경표", "박주형", "이헌제"]));
test("last: newest post first", () => eq(order("last", rows), ["이헌제", "박주형", "고경훈", "김경표"]));
test("first: earliest first post first", () => eq(order("first", rows), ["김경표", "박주형", "고경훈", "이헌제"]));
test("count: most posts first, ties by name", () => eq(order("count", rows), ["박주형", "이헌제", "고경훈", "김경표"]));
