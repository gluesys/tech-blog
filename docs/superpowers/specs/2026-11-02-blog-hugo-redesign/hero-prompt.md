# Hero art prompt record

- Date: 2026-11-02
- Tool: Grok Build, through the `grok-build:grok-delegate` agent
- Input: `static/public/slide01.jpg` (the old hero illustration), plus the design-time `hero_wide.png` as composition reference
- Post-processing: the Grok output was recolored to the CI palette by a script (left plain area forced to exactly `#163CCF`), then converted to WebP at quality 85
- Output: `static/brand/hero-wide.webp` (2560x900), `static/brand/hero-mobile.webp` (1200x1000)

## Rules

- No text and no text-like marks (including pseudo-text on panels).
- No product screens, no real hardware, no charts that could read as data.
- Palette: `#163CCF`, `#1775FD`, white, light gray-blue, small `#00C3D2` accents.
- Illustration objects must not sit under the navigation or the hero text at 390, 768, 1280, 1440 and 1920px.

## Prompt 1: desktop (wide)

Edit this isometric illustration: keep composition, characters, and style; recolor to a palette of #163CCF, #1775FD, white, and light gray-blue, with small #00C3D2 accents; remove all text and text-like marks; leave the left 45% as plain #163CCF background. Output 2560x900.

## Prompt 2: phone (portrait/stacked)

Same illustration and palette as prompt 1, recomposed for a phone: the same cube, characters and floating objects centered, plain #163CCF background around and above them (the top ~20% fully plain), no text or text-like marks on any panel. Output 1200x1000.

## Cleanup pass (v3)

The v2 art had blocky pixelated dark-navy patches (bottom-right of wide, left side of mobile). Cleanup prompts:

- Wide: "Clean up this illustration without changing composition, characters, objects, colors, or style: remove the blocky pixelated dark-navy artifact patches near the bottom-right edge, replacing them with the smooth background. No text, no new objects."
- Mobile: the same prompt, with the patches described as being along the left side.

Grok's image-edit mode failed the size and color constraints, so Grok produced a full-resolution cleanup of v2 instead. The result (v3) was used as is; the plain #163CCF area is now about 49% of the wide art's width.

- Mobile seam cleanup (v4): a deterministic NumPy/Pillow/SciPy masked-smoothing pass, run via the Grok delegate, with rows 0-210 locked to #163CCF; no generative edit.
- Mobile edge feather (v5): a deterministic Pillow/NumPy smoothstep blend of the right ~140 columns, the bottom ~120 rows and the left ~60 columns toward exactly #163CCF; pixels outside those bands are unchanged.

Note: the exact prompt strings sent to the delegate are not stored in the repo history; the two above are the spec 8.6 template adapted per format, as briefed.
