"use client";
import { motion } from "framer-motion";

interface LoopNoticeProps {
  reason: string | null;
}

// Map of reasons to user-friendly messages
const reasonMessages: Record<string, string> = {
  clarify_problem: "The strategist wants to revisit your challenge for more clarity.",
  refine_solution: "The evaluator feels the solution needs a bit more detail.",
};

export function LoopNotice({ reason }: LoopNoticeProps) {
  if (!reason) {
    return null;
  }

  const message = reasonMessages[reason] || "The agent is revisiting a previous step.";

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute top-4 left-1/2 -translate-x-1/2 bg-enso-card border border-enso-text/10 text-enso-text text-sm rounded-full px-4 py-2 shadow-lg"
    >
      ⚠️ {message}
    </motion.div>
  );
} 