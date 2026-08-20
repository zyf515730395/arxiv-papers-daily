const body = document.body;
const sidebar = document.querySelector("#paper-sidebar");
const toggle = document.querySelector(".sidebar-toggle");
const themeToggle = document.querySelector(".theme-toggle");
const themeIcon = themeToggle?.querySelector("[data-theme-icon]");
const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
const themeStorageKey = "arxiv-theme";

function storedTheme() {
  try {
    const theme = window.localStorage.getItem(themeStorageKey);
    return theme === "light" || theme === "dark" ? theme : null;
  } catch (error) {
    return null;
  }
}

let followsSystemTheme = storedTheme() === null;

function updateThemeControl(theme) {
  const isDark = theme === "dark";
  if (themeIcon) themeIcon.textContent = isDark ? "☀" : "☾";
  themeToggle?.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} theme`);
  themeToggle?.setAttribute("title", `Switch to ${isDark ? "light" : "dark"} theme`);
  themeToggle?.setAttribute("aria-pressed", String(isDark));
}

function applyTheme(theme, persist = false) {
  document.documentElement.dataset.theme = theme;
  updateThemeControl(theme);
  if (!persist) return;
  try {
    window.localStorage.setItem(themeStorageKey, theme);
  } catch (error) {
    // The current page can still switch themes when storage is unavailable.
  }
}

themeToggle?.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  followsSystemTheme = false;
  applyTheme(nextTheme, true);
});

themeMedia.addEventListener("change", (event) => {
  if (followsSystemTheme) applyTheme(event.matches ? "dark" : "light");
});

updateThemeControl(document.documentElement.dataset.theme || (themeMedia.matches ? "dark" : "light"));

function setSidebar(open) {
  body.classList.toggle("sidebar-open", open);
  toggle?.setAttribute("aria-expanded", String(open));
}

function revealHashTarget() {
  if (!window.location.hash) return;
  const target = document.querySelector(window.location.hash);
  if (!target) return;
  let parent = target;
  while (parent) {
    if (parent.tagName === "DETAILS") parent.open = true;
    parent = parent.parentElement;
  }
}

toggle?.addEventListener("click", () => setSidebar(!body.classList.contains("sidebar-open")));
document.querySelector("[data-sidebar-close]")?.addEventListener("click", () => setSidebar(false));
sidebar?.addEventListener("click", (event) => {
  if (event.target.closest("a")) setSidebar(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setSidebar(false);
});

document.querySelectorAll("[data-sidebar-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const shouldOpen = button.dataset.sidebarAction === "expand";
    sidebar.querySelectorAll("details").forEach((details) => { details.open = shouldOpen; });
  });
});

window.addEventListener("hashchange", revealHashTarget);
revealHashTarget();
