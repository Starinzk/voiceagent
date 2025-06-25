"use client";
import { Room } from "livekit-client";
import { useState } from "react";
import { LiveSession } from "./LiveSession";
import Image from "next/image";

export default function Dashboard() {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const handleStartSession = async () => {
    setIsConnecting(true);
    try {
      const response = await fetch("/api/connection-details");
      if (!response.ok) {
        throw new Error("Failed to fetch connection details");
      }
      const data = await response.json();

      const newRoom = new Room();
      await newRoom.connect(data.url, data.token);
      setRoom(newRoom);
    } catch (error) {
      console.error("Error starting session:", error);
      alert("Could not start session. Please try again.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (room) {
      await room.disconnect();
    }
    setRoom(null);
  };

  if (room) {
    return <LiveSession room={room} onDisconnect={handleDisconnect} />;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-enso-background font-sans">
      <div className="text-center max-w-lg mx-auto">
        <Image
          src="/Enso.png"
          alt="Enso Logo"
          width={120}
          height={120}
          className="mx-auto mb-8"
        />
        <h1 className="text-5xl font-serif text-enso-text mb-4">
          Think Out Loud. Leave With Clarity.
        </h1>
        <p className="text-lg text-enso-text/80 mb-12">
          Your voice-first design assistant for instant creative clarity.
        </p>
        <button
          onClick={handleStartSession}
          disabled={isConnecting}
          className="px-12 py-4 bg-enso-card text-enso-text font-bold rounded-full border border-enso-text/10 shadow-md transform hover:scale-105 transition-transform duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-enso-gradient hover:text-white"
        >
          {isConnecting ? "Connecting..." : "Start Your Session"}
        </button>
      </div>
    </main>
  );
} 