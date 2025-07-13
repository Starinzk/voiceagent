import { RoomEvent, DataPacket_Kind, RemoteParticipant } from 'livekit-client';
import { useRoomContext } from '@livekit/components-react';
import { useEffect, useState } from 'react';

export interface AgentState {
  current_agent_name: string;
  agent_sequence: string[];
  loop_reason: string | null;
  loop_counts: Record<string, number>;
}

const INITIAL_STATE: AgentState = {
  current_agent_name: 'DesignCoachAgent',
  agent_sequence: ['DesignCoachAgent'],
  loop_reason: null,
  loop_counts: {},
};

export const useAgentState = () => {
  const room = useRoomContext();
  const [agentState, setAgentState] = useState<AgentState>(INITIAL_STATE);

  useEffect(() => {
    const handleDataReceived = (
      payload: Uint8Array,
      p?: RemoteParticipant,
    ) => {
      // We are interested in data packets from the agent.
      // This is a simple check, a more robust solution might involve
      // checking participant metadata or a specific topic.
      if (p?.identity.startsWith('agent-')) {
        const decoder = new TextDecoder();
        const jsonStr = decoder.decode(payload);
        try {
          const newState = JSON.parse(jsonStr) as AgentState;
          setAgentState(newState);
        } catch (e) {
          console.error('Failed to parse agent state from data packet', e);
        }
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  return agentState;
}; 