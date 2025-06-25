"use client";
import { motion } from "framer-motion";

export function Waveform() {
  return (
    <div className="w-full max-w-2xl h-24 flex items-center justify-center opacity-50">
      <motion.svg
        width="100%"
        height="100%"
        viewBox="0 0 500 100"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="ensoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: "#00C800" }} />
            <stop offset="100%" style={{ stopColor: "#E37ED0" }} />
          </linearGradient>
        </defs>
        <motion.path
          d="M 0 50 Q 125 25, 250 50 T 500 50"
          stroke="url(#ensoGradient)"
          strokeWidth="2"
          fill="none"
          animate={{
            d: [
              "M 0 50 Q 125 25, 250 50 T 500 50",
              "M 0 50 Q 125 75, 250 50 T 500 50",
              "M 0 50 Q 125 25, 250 50 T 500 50",
            ],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.svg>
    </div>
  );
} 