import { test } from "node:test";
import { guessQuery } from "../not-found.ts";

function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

test("a mistyped post address keeps its slug", () => {
  eq(guessQuery("/blog/2019/04/08/LVMM.html"), "LVMM");
});

test("separators become spaces, dates and filler segments are dropped", () => {
  eq(guessQuery("/2022/09/21/truenas-scale_install/"), "truenas scale install");
  eq(guessQuery("/blog/page/3/"), "");
  eq(guessQuery("/index.html"), "");
});

test("percent-encoded Korean comes back as text, broken encoding is ignored", () => {
  eq(guessQuery("/tags/%ED%8C%8C%EC%9D%BC-%EC%8B%9C%EC%8A%A4%ED%85%9C/"), "파일 시스템");
  eq(guessQuery("/tags/%E0%A4%A/"), "");
});

test("long guesses are cut to a few words", () => {
  eq(guessQuery("/a-b-c-d-e-f-g-h"), "a b c d e f");
});
