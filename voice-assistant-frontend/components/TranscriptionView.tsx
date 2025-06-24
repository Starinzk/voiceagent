"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Participant } from "livekit-client";

export type CustomChatMessage = {
  id: string;
  message: string;
  from?: Participant;
  timestamp: number;
  is_final: boolean;
};

const formatTimestamp = (timestamp: number) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export default function TranscriptionView({
  chatMessages = [],
}: {
  chatMessages: CustomChatMessage[];
}) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    if (!isScrolled) {
      scrollToBottom();
    }
  }, [chatMessages, isScrolled]);

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        scrollContainerRef.current;
      const atBottom = scrollHeight - scrollTop <= clientHeight + 1;
      setIsScrolled(!atBottom);
    }
  };

  return (
    <div className="relative w-full h-full">
      <div
        ref={scrollContainerRef}
        className="w-full h-full p-4 space-y-4 overflow-y-auto"
        onScroll={handleScroll}
      >
        <AnimatePresence>
          {chatMessages.map((message) => (
            <ThoughtCard key={message.id} message={message} />
          ))}
        </AnimatePresence>
      </div>
      {isScrolled && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 bg-gray-800 text-white p-2 rounded-full shadow-lg hover:bg-gray-700 transition-colors"
        >
          ↓
        </button>
      )}
    </div>
  );
}

const ThoughtCard = ({ message }: { message: CustomChatMessage }) => {
  const isAgent = message.from?.identity?.startsWith("agent_");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={`p-4 rounded-lg shadow-md border border-white/10 relative ${
        isAgent ? "bg-white/5" : "bg-white/10"
      }`}
    >
      <div className="flex justify-between items-start">
        <p className={`font-serif ${isAgent ? "text-lg" : "text-base"}`}>
          {message.message}
          {!message.is_final && <span className="typing-indicator" />}
        </p>
        <span className="text-xs text-gray-400 absolute top-2 right-2">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
};
