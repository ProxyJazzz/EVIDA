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
          DEFAULT: "#090B0E",
          deep: "#050608",
          dark: "#0C0E13",
          elevated: "#11141B",
        },
        surface: {
          DEFAULT: "#131720",
          card: "#171B26",
          panel: "#1A1F2C",
          border: "#252B3A",
          "border-subtle": "#1B202B",
          hover: "#1D2330",
        },
        accent: {
          blue: "#3B82F6",
          emerald: "#10B981",
          rose: "#EF4444",
          amber: "#F59E0B",
          violet: "#8B5CF6",
          cyan: "#06B6D4",
        },
        evidence: {
          verified: "#10B981",
          unverified: "#EF4444",
          investigating: "#F59E0B",
          proposal: "#8B5CF6",
          execution: "#3B82F6",
          integrity: "#06B6D4",
        },
        nvidia: "#76B900",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
