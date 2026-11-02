// One share button per spot. On touch devices with the Web Share API it opens the
// system share sheet ("공유"); everywhere else it copies the canonical URL ("링크 복사").
// The URL stays clean (no utm_*); GA4 records a recommended `share` event instead.
import { writeClipboard } from "./code-copy.ts";

type Gtag = (cmd: "event", name: string, params: Record<string, string>) => void;

function track(method: string, url: string): void {
  const gtag = (window as unknown as { gtag?: Gtag }).gtag;
  if (typeof gtag === "function") gtag("event", "share", { method, content_type: "article", item_id: new URL(url).pathname });
}

export function initShare(): void {
  const native = typeof navigator.share === "function" && matchMedia("(pointer: coarse)").matches;
  document.querySelectorAll<HTMLButtonElement>("[data-share]").forEach((btn) => {
    const label = native ? "공유" : "링크 복사";
    btn.textContent = label;
    const url = btn.dataset.url ?? location.href;
    let timer: number | undefined;
    const flash = (msg: string) => {
      btn.textContent = msg;
      window.clearTimeout(timer);
      timer = window.setTimeout(() => (btn.textContent = label), 2000);
    };
    btn.addEventListener("click", async () => {
      if (native) {
        try {
          await navigator.share({ title: btn.dataset.title, url });
          track("web_share", url);
        } catch { /* cancelled */ }
        return;
      }
      try {
        await writeClipboard(url);
        flash("복사됨");
        track("copy_link", url);
      } catch {
        flash("복사 실패");
      }
    });
  });
}
