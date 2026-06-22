import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#0f0f0f",
          1: "#161616",
          2: "#1e1e1e",
          3: "#252525",
        },
        border: "#2a2a2a",
        accent: {
          DEFAULT: "#7c6af7",
          hover: "#9d95f5",
        },
      },
      animation: {
        "fade-in": "fadeIn 0.15s ease-in-out",
        "slide-up": "slideUp 0.2s ease-out",
        "blink": "blink 1s step-end infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { transform: "translateY(8px)", opacity: "0" }, to: { transform: "translateY(0)", opacity: "1" } },
        blink: { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0" } },
      },
    },
  },
  plugins: [],
};
export default config;
