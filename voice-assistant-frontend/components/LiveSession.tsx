"use client";

import {
  RoomAudioRenderer,
  RoomContext,
  useParticipants,
  TrackToggle,
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
  Track,
} from "livekit-client";
import { AgentOrb } from "./AgentOrb";
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
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full flex-grow flex flex-col items-center justify-center p-6 font-sans"
    >
      {agent ? (
        <AgentOrb agent={agent} />
      ) : (
        <NoAgentNotification roomState={room.state} />
      )}

      <div className="w-full max-w-2xl h-96 my-8">
        <TranscriptionView chatMessages={chatMessages as CustomChatMessage[]} />
      </div>

      <Waveform />

      <div className="w-full max-w-2xl flex justify-center items-center mt-8 space-x-4 text-enso-text">
        <TrackToggle
          source={Track.Source.Microphone}
          className="px-8 py-3 bg-enso-card text-enso-text font-bold rounded-full border border-enso-text/10 shadow-md transform hover:scale-105 transition-transform duration-300 hover:bg-enso-gradient hover:text-white"
        />
        <DisconnectButton
          onClick={onDisconnect}
          className="px-8 py-3 bg-enso-card text-enso-text font-bold rounded-full border border-enso-text/10 shadow-md transform hover:scale-105 transition-transform duration-300 hover:bg-enso-gradient hover:text-white"
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
