"use client";

import {
  RoomAudioRenderer,
  RoomContext,
  useParticipants,
  VoiceAssistantControlBar,
  DisconnectButton,
  useRoomContext,
} from "@livekit/components-react";
import { motion } from "framer-motion";
import {
  Room,
  RoomEvent,
  DataPacket_Kind,
  RemoteParticipant,
  Participant,
  DataPacket,
} from "livekit-client";
import { AgentOrb, AgentColor } from "./AgentOrb";
import TranscriptionView, { CustomChatMessage } from "./TranscriptionView";
import { useCallback, useEffect, useState } from "react";
import { useCombinedTranscriptions } from "../hooks/useCombinedTranscriptions";
import { NoAgentNotification } from "./NoAgentNotification";
import { CloseIcon } from "./CloseIcon";
import { Waveform } from "./Waveform";

const AGENT_IDENTITIES = [
  "design_coach",
  "design_strategist",
  "design_evaluator",
];

function LiveSessionContent({ onDisconnect }: { onDisconnect: () => void }) {
  const participants = useParticipants();
  const { chatMessages } = useCombinedTranscriptions();
  const room = useRoomContext();
  
  // Find the agent by checking if its identity is one of the known agent names.
  const agent = participants.find((p: Participant) =>
    ["design_coach", "design_strategist", "design_evaluator"].includes(
      p.identity
    )
  );

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full flex-grow flex flex-col items-center justify-center p-8"
    >
      {agent ? (
        <AgentOrb agent={agent} />
      ) : (
        <NoAgentNotification roomState={room.state} />
      )}

      <div className="w-full max-w-2xl h-96 bg-card/50 backdrop-blur-sm border border-white/10 rounded-lg my-8">
        <TranscriptionView chatMessages={chatMessages as CustomChatMessage[]} />
      </div>

      <Waveform />

      <div className="w-full max-w-2xl flex justify-center mt-8">
        <DisconnectButton
          onClick={onDisconnect}
          className="px-6 py-2 bg-transparent border border-white/20 text-white rounded-full hover:bg-white/10 transition-colors duration-300"
        >
          End Session
        </DisconnectButton>
      </div>

      <RoomAudioRenderer />
    </motion.div>
  );
}

export function LiveSession({
  room,
  onDisconnect,
}: {
  room: Room;
  onDisconnect: () => void;
}) {
  return (
    <RoomContext.Provider value={room}>
      <LiveSessionContent onDisconnect={onDisconnect} />
    </RoomContext.Provider>
  );
}
