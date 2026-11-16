export type Theme = "light" | "dark";

export function getInitialTheme(): Theme {
  const storedTheme = localStorage.getItem("edusphere-theme");
  if (storedTheme === "dark" || storedTheme === "light") return storedTheme;
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
    ? "dark"
    : "light";
}

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("edusphere-theme", theme);
}
