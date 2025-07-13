"use client";

import { useSpeakingParticipants } from "@livekit/components-react";
import { motion } from "framer-motion";

export function Waveform() {
  const speakingParticipants = useSpeakingParticipants();
  const isSomeoneSpeaking = speakingParticipants.length > 0;

  return (
    <div className="w-full flex justify-center items-center h-10 my-2">
      <motion.div
        className="w-full max-w-sm h-1 bg-enso-pink/20"
        animate={{
          scaleX: isSomeoneSpeaking ? 1 : 0.8,
          opacity: isSomeoneSpeaking ? 1 : 0.5,
        }}
        transition={{
          type: "spring",
          stiffness: 400,
          damping: 20,
        }}
      >
        <motion.div
          className="w-full h-full bg-gradient-to-r from-enso-pink to-enso-green"
          style={{
            transformOrigin: "center",
          }}
          animate={
            isSomeoneSpeaking
              ? {
                  scaleX: [1, 0.9, 1.1, 0.95, 1],
                  transition: {
                    duration: 1,
                    repeat: Infinity,
                    ease: "easeInOut",
                  },
                }
              : { scaleX: 1 }
          }
        />
      </motion.div>
    </div>
  );
} 