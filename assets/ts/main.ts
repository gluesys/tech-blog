// Mobile menu: the button toggles the .open class on the header bar and aria-expanded.
const menuBtn = document.querySelector<HTMLButtonElement>(".menu-btn");
const bar = document.querySelector<HTMLElement>(".site-header .bar");
if (menuBtn && bar) {
  menuBtn.addEventListener("click", () => {
    const open = bar.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && bar.classList.contains("open")) {
      bar.classList.remove("open");
      menuBtn.setAttribute("aria-expanded", "false");
      menuBtn.focus();
    }
  });
}
