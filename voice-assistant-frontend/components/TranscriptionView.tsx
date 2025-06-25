"use client";

import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

export interface CustomChatMessage {
  id: string;
  from: {
    identity: string;
    name: string;
  };
  message: string;
  timestamp: number;
}

const ChatBubble = ({ msg }: { msg: CustomChatMessage }) => {
  const isAgent = !msg.from.identity.startsWith("user-");
  const bubbleAlignment = isAgent ? "self-start" : "self-end";
  const bubbleBg = isAgent ? "bg-enso-card-bg" : "bg-enso-card";
  const bubbleTextColor = "text-enso-text";

  const time = new Date(msg.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`w-full flex ${isAgent ? "justify-start" : "justify-end"}`}
    >
      <div
        className={`relative max-w-lg rounded-2xl py-3 px-5 m-2 shadow-sm ${bubbleBg} ${bubbleTextColor}`}
      >
        <p className="font-sans pr-12">{msg.message}</p>
        <span className="absolute top-3 right-4 text-xs text-enso-text/40">
          {time}
        </span>
      </div>
    </motion.div>
  );
};

export default function TranscriptionView({
  chatMessages,
}: {
  chatMessages: CustomChatMessage[];
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  return (
    <div
      ref={scrollRef}
      className="w-full h-full flex flex-col space-y-2 p-4 overflow-y-auto"
    >
      {chatMessages.map((msg) => (
        <ChatBubble key={msg.id} msg={msg} />
      ))}
    </div>
  );
}
