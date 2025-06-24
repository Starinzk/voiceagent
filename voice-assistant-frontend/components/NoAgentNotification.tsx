import { ConnectionState } from "livekit-client";

interface NoAgentNotificationProps {
  roomState: ConnectionState;
}

/**
 * Renders some user info when no agent connects to the room after a certain time.
 */
export function NoAgentNotification({ roomState }: NoAgentNotificationProps) {
  let message = "Waiting for the agent to connect...";
  if (roomState === "connecting") {
    message = "Connecting to the room...";
  } else if (roomState === "disconnected") {
    message = "Agent has disconnected. Please refresh the page.";
  }

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="text-gray-400">{message}</div>
    </div>
  );
}
