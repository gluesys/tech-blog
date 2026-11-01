// Adds a language label and a copy button to every code block in the article body.
async function writeClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try { await navigator.clipboard.writeText(text); return; } catch { /* fall through */ }
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.cssText = "position:fixed;top:0;left:0;opacity:0";
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand("copy");
  ta.remove();
  if (!ok) throw new Error("copy failed");
}

export { writeClipboard };

export function initCodeCopy(): void {
  const root = document.querySelector(".prose");
  if (!root) return;
  const blocks: HTMLElement[] = [];
  root.querySelectorAll<HTMLElement>(".highlight").forEach((el) => blocks.push(el));
  // Indented or language-less blocks have no .highlight wrapper: wrap them.
  root.querySelectorAll<HTMLPreElement>("pre").forEach((pre) => {
    if (pre.closest(".highlight")) return;
    const wrap = document.createElement("div");
    wrap.className = "highlight";
    pre.replaceWith(wrap);
    wrap.appendChild(pre);
    blocks.push(wrap);
  });
  for (const block of blocks) {
    const pre = block.querySelector("pre");
    if (!pre) continue;
    const lang = block.querySelector("code")?.getAttribute("data-lang");
    if (lang) {
      const label = document.createElement("span");
      label.className = "code-lang";
      label.textContent = lang;
      block.prepend(label);
    }
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-copy";
    btn.textContent = "복사";
    let timer: number | undefined;
    btn.addEventListener("click", async () => {
      try {
        await writeClipboard((pre.querySelector("code") ?? pre).textContent ?? "");
        btn.textContent = "복사됨";
      } catch {
        btn.textContent = "복사 실패";
      }
      window.clearTimeout(timer);
      timer = window.setTimeout(() => (btn.textContent = "복사"), 2000);
    });
    block.prepend(btn);
  }
}
