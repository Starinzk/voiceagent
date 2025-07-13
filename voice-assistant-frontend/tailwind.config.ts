import type { Config } from "tailwindcss";
import { fontFamily } from "tailwindcss/defaultTheme";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "../../node_modules/@livekit/components-react/dist/index.mjs",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", ...fontFamily.sans],
        serif: ["var(--font-playfair)", "Georgia", "serif"],
      },
      colors: {
        "enso-background": "#F5F5F5",
        "enso-text": "#333333",
        "enso-card": "#FFFFFF",
        "enso-pink": "#FFD5E5",
        "enso-green": "#B4FFD5",
      },
      backgroundImage: {
        "enso-gradient": "linear-gradient(135deg, #FFD5E5 0%, #B4FFD5 100%)",
      },
    },
  },
  plugins: [],
};
export default config;
