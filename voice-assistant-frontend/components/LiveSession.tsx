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
  Participant,
  Track,
} from "livekit-client";
import { AgentOrb } from "./AgentOrb";
import TranscriptionView from "./TranscriptionView";
import { useState } from "react";
import { useCombinedTranscriptions } from "../hooks/useCombinedTranscriptions";
import { NoAgentNotification } from "./NoAgentNotification";
import { Waveform } from "./Waveform";
import { useAgentState } from "../hooks/useAgentState";
import { LoopNotice } from "./LoopNotice";
import { AgentBreadcrumbs } from "./AgentBreadcrumbs";
import { ClarityCapsule, ClarityCapsuleView } from "./ClarityCapsuleView";
import { useDataChannel } from "../hooks/useDataChannel";

function LiveSessionContent({ onDisconnect }: { onDisconnect: () => void }) {
  const participants = useParticipants();
  const { chatMessages } = useCombinedTranscriptions();
  const room = useRoomContext();
  const { current_agent_name, loop_reason } = useAgentState();
  const [clarityCapsule, setClarityCapsule] = useState<ClarityCapsule | null>(null);
  
  useDataChannel(room, (msg: { payload: Uint8Array }) => {
    const json = JSON.parse(new TextDecoder().decode(msg.payload));
    if (json.type === 'clarity_capsule') {
      setClarityCapsule(json);
    }
  }, 'lk-chat-topic');

  const agent = participants.find((p: Participant) =>
    p.identity.startsWith("design_")
  );

  const user = participants.find((p: Participant) =>
    !p.identity.startsWith("design_")
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full h-full flex flex-col p-6 font-sans bg-enso-background"
    >
      {/* Top Section */}
      <div className="w-full">
        <LoopNotice reason={loop_reason} />
        <AgentBreadcrumbs currentAgentName={current_agent_name} />
      </div>

      {/* Middle Section */}
      <div className="flex-grow w-full flex flex-col items-center justify-center text-center">
        {agent ? (
          <>
            <AgentOrb agent={agent} user={user} />
            <div className="w-full max-w-2xl h-80 mt-4">
              {clarityCapsule ? (
                <ClarityCapsuleView capsule={clarityCapsule} />
              ) : (
                <TranscriptionView
                  chatMessages={chatMessages}
                />
              )}
            </div>
          </>
        ) : (
          <div className="flex-grow flex items-center justify-center">
            <NoAgentNotification roomState={room.state} />
          </div>
        )}
      </div>

      {/* Bottom Section */}
      <div className="w-full flex flex-col items-center">
        <Waveform />
        <div className="w-full max-w-2xl flex justify-center items-center mt-6 space-x-4 text-enso-text">
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
      <div className="w-full h-screen bg-enso-background">
        <LiveSessionContent onDisconnect={onDisconnect} />
      </div>
    </RoomContext.Provider>
  );
}
