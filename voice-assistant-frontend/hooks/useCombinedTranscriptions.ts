import { useState, useCallback, useRef } from "react";
import { useDataChannel } from "@livekit/components-react";
import { nanoid } from "nanoid";

export interface CustomChatMessage {
  id: string;
  from?: {
    identity?: string;
    name?: string;
  };
  message: string;
  timestamp: number;
  is_final: boolean;
}

export const useCombinedTranscriptions = () => {
  const [chatMessages, setChatMessages] = useState<CustomChatMessage[]>([]);
  const activeMessageIdRef = useRef<string | null>(null);

  const onDataMessage = useCallback((packet: any) => {
    const decoder = new TextDecoder();
    const rawMsg = decoder.decode(packet.payload);
    try {
      const msg = JSON.parse(rawMsg);

      setChatMessages((currentMessages) => {
        if (msg.is_final) {
          if (activeMessageIdRef.current) {
            const newMessages = currentMessages.map((m) =>
              m.id === activeMessageIdRef.current
                ? { ...msg, id: m.id, is_final: true }
                : m
            );
            activeMessageIdRef.current = null;
            return newMessages;
          } else {
            return [
              ...currentMessages,
              { ...msg, id: nanoid(), is_final: true },
            ];
          }
        } else {
          if (activeMessageIdRef.current) {
            return currentMessages.map((m) =>
              m.id === activeMessageIdRef.current
                ? { ...m, message: m.message + msg.message }
                : m
            );
          } else {
            const newId = nanoid();
            activeMessageIdRef.current = newId;
            return [
              ...currentMessages,
              { ...msg, id: newId, is_final: false },
            ];
          }
        }
      });
    } catch (e) {
      console.error("Failed to parse chat message:", rawMsg, e);
    }
  }, []);

  useDataChannel("lk-chat-topic", onDataMessage);

  return { chatMessages };
};
