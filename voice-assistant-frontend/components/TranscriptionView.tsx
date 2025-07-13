"use client";

import { useMemo, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { formatAgentName } from "../lib/utils";
import { CustomChatMessage } from "@/hooks/useCombinedTranscriptions";

const AGENT_IDENTITIES = [
  "design_coach",
  "design_strategist",
  "design_evaluator",
];

export default function TranscriptionView({
  chatMessages,
}: {
  chatMessages: CustomChatMessage[];
}) {
  const messageGroups = useMemo(() => {
    // This is a simple implementation that can be improved.
    return chatMessages;
  }, [chatMessages]);

  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messageGroups]);

  return (
    <div className="flex-grow flex flex-col overflow-y-auto p-4 space-y-4 bg-white/50 rounded-lg shadow-inner">
      <AnimatePresence>
        {messageGroups.map((msg) => {
          if (!msg.from?.identity) return null; // Defensive check

          const isAgent = AGENT_IDENTITIES.includes(msg.from.identity);
          const agentName = isAgent ? formatAgentName(msg.from.identity) : "You";

          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex flex-col w-full ${
                isAgent ? "items-start" : "items-end"
              }`}
            >
              <p className="font-bold text-sm px-4 py-1">
                {agentName}
              </p>
              <div
                className={`w-fit max-w-xl px-4 py-3 rounded-2xl ${
                  isAgent
                    ? "bg-white/80 text-gray-800 rounded-bl-none"
                    : "bg-blue-500 text-white rounded-br-none"
                }`}
              >
                <p className="text-base">{msg.message}</p>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
      <div ref={messagesEndRef} />
    </div>
  );
}
