import type { Config } from "tailwindcss";

// Warm, trustworthy, government-grade palette with delight.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#1A1714", soft: "#4A453E", faint: "#8A8378" },
        paper: { DEFAULT: "#FBF7F0", card: "#FFFFFF", sunk: "#F2EBDF" },
        saffron: { DEFAULT: "#E8730C", deep: "#C25A00", soft: "#FDEBD8" },
        leaf: { DEFAULT: "#1B873F", soft: "#E3F3E8" },
        amber: { DEFAULT: "#B26A00", soft: "#FBEFD6" },
        flag: { DEFAULT: "#C62828", soft: "#FBE3E3" },
        indigo: { DEFAULT: "#2A3B8F", soft: "#E7EAF6" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(26,23,20,0.04), 0 8px 24px -12px rgba(26,23,20,0.18)",
        lift: "0 12px 40px -12px rgba(26,23,20,0.28)",
        glow: "0 0 0 4px rgba(232,115,12,0.12)",
      },
      borderRadius: { xl2: "1.25rem" },
      keyframes: {
        scanline: { "0%": { top: "0%" }, "100%": { top: "100%" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        pulsering: { "0%": { transform: "scale(1)", opacity: "0.6" }, "100%": { transform: "scale(2.4)", opacity: "0" } },
      },
      animation: {
        scanline: "scanline 2.2s ease-in-out infinite alternate",
        shimmer: "shimmer 1.6s infinite",
        pulsering: "pulsering 1.8s ease-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
