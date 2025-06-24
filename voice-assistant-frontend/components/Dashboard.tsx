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
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-charcoal-start to-charcoal-end text-white">
      <div className="text-center">
        <Image
          src="/Enso.png"
          alt="Enso Logo"
          width={150}
          height={150}
          className="mx-auto mb-8"
        />
        <h1 className="text-5xl font-serif mb-4">Enso</h1>
        <p className="text-lg text-gray-300 mb-8">Your AI Design Partner</p>
        <button
          onClick={handleStartSession}
          disabled={isConnecting}
          className="px-8 py-3 bg-enso-green text-black font-bold rounded-full hover:bg-enso-magenta hover:text-white transition-colors duration-300 disabled:bg-gray-500 disabled:cursor-not-allowed"
        >
          {isConnecting ? "Connecting..." : "Start Session"}
        </button>
      </div>
    </main>
  );
} 