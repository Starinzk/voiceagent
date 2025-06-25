import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "../../node_modules/@livekit/components-react/dist/index.mjs",
  ],
  theme: {
    extend: {
      colors: {
        "enso-green": "#00C800",
        "enso-pink": "#E37ED0",
        "enso-background": "#f9f9f9",
        "enso-text": "#1a1a1a",
        "enso-card": "#ffffff",
        "enso-card-bg": "#f2f2f2",
      },
      fontFamily: {
        serif: ["Playfair Display", "Georgia", "serif"],
        sans: ["Inter", "Helvetica Neue", "sans-serif"],
      },
      backgroundImage: {
        "enso-gradient": "linear-gradient(to right, #00C800, #E37ED0)",
      },
    },
  },
  plugins: [],
};
export default config;
