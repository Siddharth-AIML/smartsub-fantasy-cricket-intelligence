/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cricket: {
          pitch: "#14452F",
          field: "#0E281E",
          gold: "#FACC15",
          csk: "#F9CD05",
          mi: "#004BA0",
          card: "#1E293B",
          dark: "#0F172A",
          border: "#334155"
        }
      }
    },
  },
  plugins: [],
}
