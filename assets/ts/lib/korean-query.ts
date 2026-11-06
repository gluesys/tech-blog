// Korean particle handling for Pagefind queries. Pagefind splits on spaces and
// has no Korean stemmer, so "스냅샷을" never matches "스냅샷". The UI therefore
// also searches a variant with one trailing particle stripped from each token.

// Longest first, so "에서" wins over "에".
export const PARTICLES = [
  "에서", "으로", "까지", "부터",
  "은", "는", "이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "만",
];

const HANGUL_WORD = /^[가-힣]{2,}$/;
// Verb and adjective stems: "백업하는" is "백업하" + "는", not a noun + particle.
const STEM_ENDINGS = ["하", "되"];

export function stripParticles(token: string): string {
  for (const p of PARTICLES) {
    if (!token.endsWith(p)) continue;
    const rest = token.slice(0, -p.length);
    if (!HANGUL_WORD.test(rest)) continue;
    if (STEM_ENDINGS.some((s) => rest.endsWith(s))) continue;
    return rest;
  }
  return token;
}

export function queryVariants(q: string): string[] {
  const tokens = q.trim().split(/\s+/).filter(Boolean);
  const original = tokens.join(" ");
  const stripped = tokens.map(stripParticles).join(" ");
  return stripped === original ? [original] : [original, stripped];
}
