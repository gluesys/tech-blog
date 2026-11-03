import { test } from "node:test";
import { marqueePlan } from "../placeholder-marquee.ts";

function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

test("text that fits does not scroll", () => eq(marqueePlan(240, 400), null));
test("text exactly as wide as the field does not scroll", () => eq(marqueePlan(240, 240), null));
test("hidden field (zero width) does not scroll", () => eq(marqueePlan(240, 0), null));
test("wider text scrolls by its width plus the gap", () => eq(marqueePlan(372, 240), { shift: 420, seconds: 9.3 }));
