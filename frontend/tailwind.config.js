/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        panel: "#f6f8fb",
        line: "#e5e7eb",
        accent: "#10a37f",
        ocean: "#2563eb",
        amber: "#f59e0b"
      },
      boxShadow: {
        soft: "0 8px 30px rgba(15, 23, 42, 0.08)",
        glow: "0 18px 50px rgba(16, 163, 127, 0.16)"
      }
    }
  },
  plugins: []
};
