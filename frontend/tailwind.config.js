/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        panel: "#161922",
        panelSoft: "#1e2230",
      },
      boxShadow: {
        soft: "0 16px 50px rgba(0, 0, 0, 0.28)",
      },
    },
  },
  plugins: [],
};