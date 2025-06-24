import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(0 0% 8%)',
        foreground: 'hsl(0 0% 98%)',
        card: 'hsl(0 0% 12%)',
        border: 'hsl(0 0% 18%)',
        primary: {
          DEFAULT: 'hsl(0 0% 98%)',
          foreground: 'hsl(0 0% 8%)',
        },
        agent: {
          coach: '#3B82F6',     // Blue
          strategist: '#10B981', // Green
          evaluator: '#8B5CF6',  // Purple
        },
        "enso-green": "#00C800",
        "enso-magenta": "#E37ED0",
        "charcoal-start": "#2C2C2C",
        "charcoal-end": "#1A1A1A",
      },
      borderRadius: {
        lg: `1rem`,
        md: `calc(1rem - 4px)`,
        sm: `calc(1rem - 8px)`,
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        serif: ["var(--font-georgia)"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
