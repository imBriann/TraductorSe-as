// Utilidades de UI: tema (modo oscuro), toasts, navegación y animaciones.
(function () {
  const cfg = window.LSC.config;

  // -------------------------------------------------------------- Tema
  const Theme = {
    init() {
      const saved = localStorage.getItem(cfg.THEME_KEY);
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (saved === "dark" || (!saved && prefersDark)) {
        document.documentElement.classList.add("dark");
      }
    },
    toggle() {
      const isDark = document.documentElement.classList.toggle("dark");
      localStorage.setItem(cfg.THEME_KEY, isDark ? "dark" : "light");
      window.LSC.api.updateSettings({ dark_mode: isDark }).catch(() => {});
      const lbl = document.getElementById("themeLabel");
      if (lbl) lbl.textContent = isDark ? "Modo claro" : "Modo oscuro";
      return isDark;
    },
  };

  // ------------------------------------------------------------ Toasts
  function toast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      document.body.appendChild(container);
    }
    const colors = {
      info: "bg-slate-800", success: "bg-emerald-600",
      error: "bg-rose-600", warn: "bg-amber-500",
    };
    const el = document.createElement("div");
    el.className = `toast ${colors[type] || colors.info}`;
    el.setAttribute("role", "status");
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateY(8px)"; }, 3200);
    setTimeout(() => el.remove(), 3800);
  }

  // -------------------------------------------------------- Navegación
  const BASE_LINKS = [
    { href: "index.html", label: "Inicio", icon: "􀎟", emoji: "🏠" },
    { href: "translator.html", label: "Traductor", icon: "", emoji: "🤟" },
    { href: "history.html", label: "Historial", icon: "", emoji: "🕑" },
    { href: "configuracion.html", label: "Ajustes", icon: "", emoji: "⚙️" },
    { href: "info.html", label: "Sistema", icon: "", emoji: "ℹ️" },
  ];
  const DEV_LINKS = [
    { href: "dataset.html", label: "Dataset", emoji: "🗂️", dev: true },
    { href: "training.html", label: "Entrenar", emoji: "🧠", dev: true },
  ];

  function renderSidebar(active, links) {
    const items = links.map((l) => `
      <a href="${l.href}" class="nav-link ${active === l.href ? "active" : ""}">
        <span aria-hidden="true">${l.emoji}</span><span>${l.label}</span>
        ${l.dev ? '<span class="ml-auto rounded-md bg-amber-100 px-1.5 text-[10px] font-bold text-amber-700 dark:bg-amber-900/60 dark:text-amber-300">DEV</span>' : ''}
      </a>`).join("");

    return `
      <aside class="glass hidden md:flex w-64 flex-col p-4 sticky top-0 h-screen" style="border-width:0 1px 0 0;">
        <a href="index.html" class="mb-7 flex items-center gap-2.5 px-2 pt-2">
          <span class="grid h-9 w-9 place-items-center rounded-2xl text-lg" style="background:var(--accent-soft)">🇨🇴</span>
          <span class="text-[17px] font-bold tracking-tight">LSC <span class="text-gradient">i5.0</span></span>
        </a>
        <nav class="flex-1 space-y-1">${items}</nav>
        <div class="mt-4 border-t pt-3" style="border-color:var(--border)">
          <button id="themeToggle" class="nav-link w-full" aria-label="Cambiar tema">
            <span aria-hidden="true">🌓</span><span id="themeLabel">Modo oscuro</span>
          </button>
          <p class="px-3 pt-3 text-[11px]" style="color:var(--text-2)">Acceso anónimo · sin registro</p>
        </div>
      </aside>`;
  }

  function renderTabbar(active, links) {
    const items = links.map((l) => `
      <a href="${l.href}" class="${active === l.href ? "active" : ""}">
        <span class="ic" aria-hidden="true">${l.emoji}</span><span>${l.label}</span>
      </a>`).join("");
    return `<nav class="tabbar glass md:hidden" style="border-width:1px 0 0 0;">${items}</nav>`;
  }

  // Animación de entrada escalonada para el contenido principal
  function revealMain() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const main = document.querySelector("main");
    if (!main) return;
    const targets = main.querySelectorAll(":scope > header, :scope > section, :scope .card, :scope > h1");
    let i = 0;
    targets.forEach((el) => {
      if (el.closest(".card") && !el.classList.contains("card")) return; // evita doble animación
      el.style.animationDelay = (i * 70) + "ms";
      el.classList.add("reveal");
      i++;
    });
  }

  async function mountNav(active) {
    let devMode = false;
    try {
      const info = await window.LSC.api.systemInfo();
      devMode = !!info.dev_mode;
      const s = await window.LSC.api.settings().catch(() => null);
      if (s && s.dark_mode && !document.documentElement.classList.contains("dark")) {
        document.documentElement.classList.add("dark");
      }
    } catch (e) { /* backend offline: nav base */ }

    const links = devMode ? [...BASE_LINKS, ...DEV_LINKS] : BASE_LINKS;
    const slot = document.getElementById("nav-slot");
    if (slot) {
      slot.innerHTML = renderSidebar(active, links);
      // barra inferior móvil (solo enlaces base para mantenerla limpia)
      document.body.insertAdjacentHTML("beforeend", renderTabbar(active, BASE_LINKS));
    }
    const tt = document.getElementById("themeToggle");
    if (tt) {
      tt.addEventListener("click", () => Theme.toggle());
      const lbl = document.getElementById("themeLabel");
      if (lbl) lbl.textContent = document.documentElement.classList.contains("dark") ? "Modo claro" : "Modo oscuro";
    }
    revealMain();
    return { devMode };
  }

  window.LSC.ui = { Theme, toast, mountNav, revealMain };
  Theme.init();
})();
