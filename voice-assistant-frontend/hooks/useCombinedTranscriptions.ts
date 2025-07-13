import { useState, useCallback, useMemo } from "react";
import { useDataChannel } from "@livekit/components-react";
import { nanoid } from "nanoid";
import { Participant } from "livekit-client";

export interface CustomChatMessage {
  id: string;
  from?: Participant;
  message: string;
  timestamp: number;
}

export const useCombinedTranscriptions = () => {
  const [chatMessages, setChatMessages] = useState<CustomChatMessage[]>([]);

  const onDataMessage = useCallback((packet: any) => {
    const decoder = new TextDecoder();
    const rawMsg = decoder.decode(packet.payload);
    try {
      const msg = JSON.parse(rawMsg);

      if (msg.type === "context" || msg.type === "agent_state" || msg.type === "clarity_capsule") {
        return;
      }

      setChatMessages((currentMessages) => {
        const lastMessage = currentMessages[currentMessages.length - 1];

        if (
          !msg.is_final &&
          lastMessage &&
          lastMessage.from?.identity === msg.from.identity &&
          !lastMessage.id.startsWith("final-")
        ) {
          return currentMessages.map((m, i) =>
            i === currentMessages.length - 1
              ? { ...m, message: m.message + msg.message }
              : m
          );
        } else {
          return [
            ...currentMessages,
            {
              id: msg.is_final
                ? `final-${nanoid()}`
                : `interim-${nanoid()}`,
              from: msg.from,
              message: msg.message,
              timestamp: msg.timestamp,
            },
          ];
        }
      });
    } catch (e) {
      console.error("Failed to parse chat message:", rawMsg, e);
    }
  }, []);

  useDataChannel("lk-chat-topic", onDataMessage);

  return useMemo(() => {
    return { chatMessages };
  }, [chatMessages]);
};
