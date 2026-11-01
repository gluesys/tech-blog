# Self-hosted fonts

Both families are licensed under the SIL Open Font License 1.1 (license files next to the fonts).
No font is loaded from a CDN.

## Pretendard Variable (Korean and Latin text)

- Version: v1.3.9, https://github.com/orioncactus/pretendard (release tag `v1.3.9`)
- Files: `pretendard/PretendardVariable.subset.{0..91}.woff2` (92 dynamic-subset files, 2.96 MB in total;
  a page downloads only the unicode-range slices it uses). Taken unmodified from
  `packages/pretendard/dist/web/variable/woff2-dynamic-subset/` at tag `v1.3.9`, e.g.
  https://raw.githubusercontent.com/orioncactus/pretendard/v1.3.9/packages/pretendard/dist/web/variable/woff2-dynamic-subset/PretendardVariable.subset.0.woff2
- `@font-face` rules with the unicode ranges: `assets/css/fonts.css`, derived from
  `pretendardvariable-dynamic-subset.css` of the same tag (font family renamed to `Pretendard`, URLs
  rewritten to `/fonts/pretendard/`).
- License: `pretendard/OFL.txt` (from `LICENSE.txt` in `Pretendard-1.3.9.zip`).
- SHA-256 of the release archive https://github.com/orioncactus/pretendard/releases/download/v1.3.9/Pretendard-1.3.9.zip:
  `04be351a74d6bf7d60c480a3087e51d185485d35a52023142af1df19eb8c428a`
- SHA-256 of committed files: run `sha256sum static/fonts/pretendard/*`
  (e.g. `PretendardVariable.subset.0.woff2` = `8713e83342c3f5ed316bf22bf50a3d991a5b5dd16c0c45c54a6ad81f62be7df3`,
  `OFL.txt` = `b04538c9abec39a3db75108cf0af0fd9c77032fe8aa2cf38345b4d250e98e38e`).

## Saira (the "TECH-G" name only)

- Source: https://github.com/google/fonts/tree/main/ofl/saira, commit
  `6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec` (main at download time, 2026-11-02),
  file `Saira[wdth,wght].ttf` (variable, wdth and wght axes).
  SHA-256 of the source TTF: `9d050fc5a01c85f74c4257c207d50b55d1e40c37308c642f974a2c5003231dde`
- License: `saira/OFL.txt` (same repository directory).
- Committed file: `saira/Saira-TECH-G.woff2`, 928 bytes, instanced at wdth 125 / wght 700 and
  subset to the glyphs `TECH-G`. SHA-256:
  `f1d3d51446abca1aaddfa3bf049cf02632f1796b1632fb7538821582e07ccf34`

Subset command (fonttools and brotli in a throwaway venv):

    fonttools varLib.instancer "Saira[wdth,wght].ttf" wdth=125 wght=700 -o saira-inst.ttf
    pyftsubset saira-inst.ttf --text="TECH-G" --flavor=woff2 --layout-features='' \
      --no-hinting --output-file=static/fonts/saira/Saira-TECH-G.woff2

Because only `TECH-G` is embedded, any other text set in Saira falls back to the next family.
