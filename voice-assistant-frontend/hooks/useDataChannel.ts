import { Room, RoomEvent, DataPacket_Kind, RemoteParticipant } from 'livekit-client';
import { useEffect } from 'react';

export function useDataChannel(
  room: Room, 
  onMessage: (msg: { payload: Uint8Array; topic?: string }) => void,
  topic?: string
) {
  useEffect(() => {
    const handleData = (
      payload: Uint8Array, 
      p?: RemoteParticipant, 
      kind?: DataPacket_Kind, 
      _topic?: string
    ) => {
      if (kind === DataPacket_Kind.RELIABLE) {
        if (!topic || _topic === topic) {
          onMessage({ payload: payload, topic: _topic });
        }
      }
    };

    room.on(RoomEvent.DataReceived, handleData);
    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room, onMessage, topic]);
} 