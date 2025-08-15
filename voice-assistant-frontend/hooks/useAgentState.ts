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
      _p?: RemoteParticipant,
      _kind?: DataPacket_Kind,
      topic?: string,
    ) => {
      if (topic !== 'lk-chat-topic') return;
      try {
        const jsonStr = new TextDecoder().decode(payload);
        const data = JSON.parse(jsonStr);
        if (data?.type === 'agent_state') {
          const nextState: AgentState = {
            current_agent_name: data.current_agent_name,
            agent_sequence: Array.isArray(data.agent_sequence) ? data.agent_sequence : [],
            loop_reason: data.loop_reason ?? null,
            loop_counts: typeof data.loop_counts === 'object' && data.loop_counts !== null ? data.loop_counts : {},
          };
          setAgentState(nextState);
        }
      } catch (e) {
        console.error('Failed to parse agent state from data packet', e);
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  return agentState;
}; 