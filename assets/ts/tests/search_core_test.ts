import { test } from "node:test";
import { type PagefindLike, searchMerged, shouldNavigate, titleMatches } from "../lib/search-core.ts";

function eq(actual: unknown, expected: unknown) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

test("shouldNavigate: stale list or pending search must not navigate", () => {
  eq(shouldNavigate("스냅샷", "스냅샷", false), true);
  eq(shouldNavigate("스냅샷 백업", "스냅샷", false), false); // typed after the list rendered
  eq(shouldNavigate("스냅샷", "스냅샷", true), false); // search in flight
  eq(shouldNavigate("  스냅샷 ", "스냅샷", false), true);
  eq(shouldNavigate("스냅샷", null, false), false); // nothing rendered yet
});

test("titleMatches: Latin tokens need a word start, Hangul tokens match anywhere", () => {
  eq(titleMatches("ZFS스냅샷", ["스냅샷"]), true);
  eq(titleMatches("스토리지 1편", ["편"]), true);
  eq(titleMatches("RAIDZ 구성", ["raid"]), true); // prefix of a longer word is fine
  eq(titleMatches("xiRAID", ["raid"]), false);
  eq(titleMatches("GRAID", ["raid"]), false);
  eq(titleMatches("GRAID와 RAID", ["raid"]), true); // second occurrence starts a word
  eq(titleMatches("NVMe-oF 소개", ["nvme-of"]), true);
  eq(titleMatches("2편", ["2"]), true);
  eq(titleMatches("v12", ["2"]), false);
});

test("titleMatches: all tokens of a variant", () => {
  eq(titleMatches("ZFS 파일 시스템", ["zfs"]), true);
  eq(titleMatches("스토리지 이중화 1편", ["이중화를", "이중화"]), true);
  eq(titleMatches("재해복구", ["재해 복구"]), true);
  eq(titleMatches("재해복구", ["백업 복구"]), false);
  eq(titleMatches("NVMe 시대의 RAID: GRAID", ["raid"]), true);
  eq(titleMatches("NVMe 시대의 GRAID", ["raid"]), false);
  eq(titleMatches("xiRAID", ["raid"]), false);
  eq(titleMatches("a (b) c", ["(b)"]), true);
  eq(titleMatches("anything", [""]), false);
});

function fake(map: Record<string, string[]>, titles: Record<string, string>): PagefindLike {
  return {
    search: (q) => Promise.resolve({
      results: (map[q] ?? []).map((id) => ({
        id,
        data: () => Promise.resolve({ url: `/${id}`, excerpt: "", meta: { title: titles[id] } }),
      })),
    }),
  };
}

test("searchMerged: title matches first, count is the true total", async () => {
  const ids = Array.from({ length: 25 }, (_, i) => `p${i}`);
  const titles: Record<string, string> = Object.fromEntries(ids.map((i) => [i, `post ${i}`]));
  titles["p7"] = "ZFS intro";
  const r = await searchMerged(fake({ "ZFS": ids }, titles), "ZFS", 20);
  eq(r.total, 25);
  eq(r.hits.length, 20);
  eq(r.hits[0].id, "p7");
  eq(r.hits[1].id, "p0");
});

test("searchMerged: original-query hits stay ahead of variant-only hits", async () => {
  const pf = fake({ "스냅샷을": ["a"], "스냅샷": ["b", "a"] }, { a: "x", b: "y" });
  const r = await searchMerged(pf, "스냅샷을");
  eq(r.hits.map((h) => h.id), ["a", "b"]);
  eq(r.total, 2);
});
