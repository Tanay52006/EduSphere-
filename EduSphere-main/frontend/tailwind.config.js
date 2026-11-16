/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--text)",
        muted: "var(--muted)",
        border: "var(--border)",
        blue: "var(--blue-solid)",
        purple: "var(--purple-solid)",
        green: "var(--green-solid)",
        yellow: "var(--yellow-solid)",
        red: "var(--red-solid)",
      },
    },
  },
  plugins: [],
};
