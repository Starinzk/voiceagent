"use client";

import { useIsSpeaking } from "@livekit/components-react";
import { motion } from "framer-motion";
import { Participant } from "livekit-client";

export const getAgentColor = (identity: string) => {
  if (identity.includes("coach")) return "bg-blue-500";
  if (identity.includes("strategist")) return "bg-green-500";
  if (identity.includes("evaluator")) return "bg-purple-500";
  return "bg-gray-500";
};

export function AgentOrb({ agent }: { agent: Participant }) {
  const isSpeaking = useIsSpeaking(agent);

  return (
    <div className="relative flex flex-col items-center">
      <motion.div
        className="w-32 h-32 rounded-full bg-enso-gradient shadow-lg"
        animate={{
          scale: isSpeaking ? 1.1 : 1,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 20,
        }}
      />
      <div className="mt-4 text-center">
        <p className="font-bold text-lg text-enso-text">{agent.name}</p>
        <p className="text-sm text-enso-text/70">
          {isSpeaking ? "is speaking..." : "is listening..."}
        </p>
      </div>
    </div>
  );
} 