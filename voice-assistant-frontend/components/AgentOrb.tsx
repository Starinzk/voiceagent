"use client";

import {
  ParticipantName,
  useIsSpeaking,
} from "@livekit/components-react";
import { Participant } from "livekit-client";
import { motion } from "framer-motion";

export const getAgentColor = (
  participant?: Participant
): "blue" | "green" | "orange" => {
  if (!participant) {
    return "blue";
  }
  switch (participant.identity) {
    case "design_coach":
      return "blue";
    case "design_strategist":
      return "green";
    case "design_evaluator":
      return "orange";
    default:
      return "blue";
  }
};

export const AgentOrb = ({ agent }: { agent: Participant }) => {
  const isSpeaking = useIsSpeaking(agent);

  return (
    <div className="flex flex-col items-center space-y-4">
      <motion.div
        className="w-36 h-36 rounded-full bg-gradient-to-br from-enso-green to-enso-magenta"
        animate={{
          scale: isSpeaking ? 1.05 : 1,
          opacity: isSpeaking ? 1 : 0.8,
        }}
        transition={{
          duration: 0.4,
          ease: "easeInOut",
          repeat: isSpeaking ? Infinity : 0,
          repeatType: "reverse",
        }}
      />
      <div className="text-center">
        <div className="font-serif text-lg">
          <ParticipantName participant={agent} />
        </div>
        <div className="text-sm text-gray-400">
          {isSpeaking ? "is speaking..." : "is listening..."}
        </div>
      </div>
    </div>
  );
}; 