/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Extra neutral shade used in history table rows
        neutral: {
          850: "#1c1c1c",
        },
      },
      fontFamily: {
        sans: ["'Segoe UI'", "system-ui", "-apple-system", "sans-serif"],
        mono: ["'Cascadia Code'", "'Fira Code'", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
