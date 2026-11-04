import { test } from "node:test";
import assert from "node:assert/strict";
import { lensOffset, lensScale } from "../image-zoom.ts";

test("lens shows the file's own detail between 2x and 4x", () => {
  assert.equal(lensScale(2160, 720), 3);
  assert.equal(lensScale(900, 720), 2); // barely shrunk: still magnifies 2x
  assert.equal(lensScale(5000, 720), 4); // huge file: capped
  assert.equal(lensScale(1000, 0), 2);
});

test("lens centre sits on the pointed spot", () => {
  // point (100, 50) at 2x lies at (200, 100) in the magnified image; a 220px lens centres it
  assert.deepEqual(lensOffset(100, 50, 2, 220), { x: -90, y: 10 });
  assert.deepEqual(lensOffset(0, 0, 3, 220), { x: 110, y: 110 });
});
