import { test } from "node:test";
import { compareAuthors, shuffled } from "../about-sort.ts";

function order(key: "name" | "last" | "first", rows: Record<string, string>[]): string[] {
  return [...rows].sort((a, b) => compareAuthors(key, a, b)).map((r) => r.name);
}
function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}
const rows = [
  { name: "이헌제", last: "2026-06-24", first: "2024-06-03" },
  { name: "고경훈", last: "2021-05-20", first: "2021-05-20" },
  { name: "박주형", last: "2024-06-10", first: "2019-11-22" },
  { name: "김경표", last: "2018-11-02", first: "2018-11-02" },
];

test("name: 가나다순", () => eq(order("name", rows), ["고경훈", "김경표", "박주형", "이헌제"]));
test("last: newest post first", () => eq(order("last", rows), ["이헌제", "박주형", "고경훈", "김경표"]));
test("first: earliest first post first", () => eq(order("first", rows), ["김경표", "박주형", "고경훈", "이헌제"]));

test("shuffled keeps every item and leaves the input alone", () => {
  const names = rows.map((r) => r.name);
  const out = shuffled(names);
  eq([...out].sort(), [...names].sort());
  eq(names, ["이헌제", "고경훈", "박주형", "김경표"]);
});
test("shuffled follows the random source (Fisher–Yates)", () => {
  // rand 0 always swaps index i with index 0:
  // i=3,j=0: [d,b,c,a]; i=2,j=0: [c,b,d,a]; i=1,j=0: [b,c,d,a]
  eq(shuffled(["a", "b", "c", "d"], () => 0), ["b", "c", "d", "a"]);
  // rand just under 1 always picks j=i: no swaps
  eq(shuffled(["a", "b", "c", "d"], () => 0.999), ["a", "b", "c", "d"]);
});
