import { PARTICLES, queryVariants, stripParticles } from "../lib/korean-query.ts";

function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

Deno.test("queryVariants: trailing particle is stripped", () => {
  eq(queryVariants("스냅샷을"), ["스냅샷을", "스냅샷"]);
  eq(queryVariants("백업도"), ["백업도", "백업"]);
  eq(queryVariants("재해복구에서"), ["재해복구에서", "재해복구"]);
});

Deno.test("queryVariants: no variant when nothing to strip", () => {
  eq(queryVariants("이중화"), ["이중화"]);
  eq(queryVariants("와이"), ["와이"]);
  eq(queryVariants("NVMe-oF"), ["NVMe-oF"]);
  eq(queryVariants("ZFS"), ["ZFS"]);
});

Deno.test("queryVariants: per-token on multi-word queries", () => {
  eq(queryVariants("파일을 백업하는 방법"), ["파일을 백업하는 방법", "파일 백업하는 방법"]);
});

Deno.test("stripParticles: verb and adjective stems are kept", () => {
  eq(stripParticles("백업하는"), "백업하는");
  eq(stripParticles("이중화된"), "이중화된");
});

Deno.test("stripParticles: longest particle first, one only", () => {
  eq(stripParticles("재해복구에서"), "재해복구");
  eq(stripParticles("파일시스템으로"), "파일시스템");
  eq(stripParticles("스냅샷을"), "스냅샷");
});

Deno.test("stripParticles: non-Hangul remainder is untouched", () => {
  eq(stripParticles("ZFS를"), "ZFS를");
  eq(stripParticles("NVMe-oF"), "NVMe-oF");
});

Deno.test("PARTICLES is ordered longest first", () => {
  for (let i = 1; i < PARTICLES.length; i++) {
    if (PARTICLES[i].length > PARTICLES[i - 1].length) throw new Error("not longest first");
  }
});

Deno.test("queryVariants: empty and whitespace", () => {
  eq(queryVariants(""), [""]);
  eq(queryVariants("  재해   복구 "), ["재해 복구"]);
});
