// "링크 복사" copies the canonical URL; "공유" uses navigator.share when present, else copies.
import { writeClipboard } from "./code-copy";

export function initShare(): void {
  document.querySelectorAll<HTMLButtonElement>("[data-share]").forEach((btn) => {
    const label = btn.textContent ?? "";
    const url = btn.dataset.url ?? location.href;
    let timer: number | undefined;
    const flash = (msg: string) => {
      btn.textContent = msg;
      window.clearTimeout(timer);
      timer = window.setTimeout(() => (btn.textContent = label), 2000);
    };
    const copy = async () => {
      try { await writeClipboard(url); flash("복사됨"); } catch { flash("복사 실패"); }
    };
    btn.addEventListener("click", async () => {
      if (btn.dataset.share === "native" && typeof navigator.share === "function") {
        try { await navigator.share({ title: btn.dataset.title, url }); } catch { /* cancelled */ }
        return;
      }
      await copy();
    });
  });
}
