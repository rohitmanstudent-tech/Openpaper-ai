import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          50: "#f5f5f5",
          100: "#e5e5e5",
          200: "#c8c8c8",
          300: "#a8a8a8",
          400: "#888888",
          500: "#666666",
          600: "#484848",
          700: "#2a2a2a",
          800: "#1a1a1a",
          850: "#111111",
          900: "#0a0a0a",
          950: "#000000",
        },
        accent: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#b0c4ff",
          300: "#7a9eff",
          400: "#4d78f0",
          500: "#3b6ae8",
          600: "#2d55c9",
          700: "#253f9a",
          800: "#1e2d6e",
          900: "#141f4a",
        },
        emerald: {
          400: "#3bae7a",
          500: "#2e9d6b",
        },
        amber: {
          400: "#c6923d",
          500: "#b07d2e",
        },
        surface: {
          50: "#f5f5f5",
          100: "#e5e5e5",
          200: "#c8c8c8",
          300: "#a8a8a8",
          400: "#888888",
          500: "#666666",
          600: "#484848",
          700: "#2a2a2a",
          800: "#1a1a1a",
          850: "#0f0f0f",
          900: "#0a0a0a",
          950: "#000000",
        },
        primary: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#b0c4ff",
          300: "#7a9eff",
          400: "#4d78f0",
          500: "#3b6ae8",
          600: "#2d55c9",
          700: "#253f9a",
          800: "#1e2d6e",
          900: "#141f4a",
          950: "#0d1533",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "SF Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "6px",
        lg: "8px",
        xl: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
