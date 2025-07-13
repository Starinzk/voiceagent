"use client";

import { useIsSpeaking } from "@livekit/components-react";
import { motion } from "framer-motion";
import { Participant } from "livekit-client";
import { formatAgentName } from "../lib/utils";

export function AgentOrb({ agent, user }: { agent: Participant, user?: Participant }) {
  const isAgentSpeaking = useIsSpeaking(agent);
  const isUserSpeaking = useIsSpeaking(user);
  const agentName = formatAgentName(agent.identity);

  return (
    <div className="relative flex flex-col items-center">
      <motion.div
        className="w-28 h-28 rounded-full bg-enso-gradient shadow-lg"
        animate={{
          scale: isAgentSpeaking ? 1.05 : 1,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 20,
        }}
      >
        {/* Optional: Add a glowing ring for speaking state */}
        {isAgentSpeaking && (
          <motion.div
            className="absolute top-0 left-0 w-full h-full rounded-full border-2 border-enso-pink"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0, 0.7, 0],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        )}
      </motion.div>
      <div className="mt-4 text-center h-10">
        <p className="font-serif text-xl text-enso-text/90">
          {isAgentSpeaking
            ? `🎙️ ${agentName} is speaking...`
            : isUserSpeaking
            ? `Listening...`
            : `${agentName} is ready.`}
        </p>
      </div>
    </div>
  );
} 