import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#050507",
          deep: "#050507",
          dark: "#08090D",
          elevated: "#0D0F14",
        },
        surface: {
          DEFAULT: "#11131A",
          hover: "#151822",
          card: "#161924",
          border: "#222634",
          "border-subtle": "#1B1E2B",
          "border-glow": "rgba(139, 92, 246, 0.25)",
        },
        accent: {
          violet: "#8B5CF6",
          indigo: "#6366F1",
          cyan: "#38BDF8",
          blue: "#3B82F6",
          emerald: "#10B981",
          rose: "#F43F5E",
          amber: "#F59E0B",
        },
        evidence: {
          verified: "#10B981",
          unverified: "#F43F5E",
          investigating: "#F59E0B",
          proposal: "#8B5CF6",
        },
        nvidia: "#76B900",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.45)",
        "glow-violet": "0 0 35px -5px rgba(139, 92, 246, 0.35)",
        "glow-cyan": "0 0 35px -5px rgba(56, 189, 248, 0.35)",
        "glow-emerald": "0 0 35px -5px rgba(16, 185, 129, 0.35)",
        "glow-rose": "0 0 35px -5px rgba(244, 63, 94, 0.35)",
      },
      animation: {
        "pulse-subtle": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float-slow": "float 6s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
