import { AccessToken, AccessTokenOptions, VideoGrant } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";
import { v4 as uuidv4 } from "uuid";

// NOTE: you are expected to define the following environment variables in `.env.local`:
const LIVEKIT_URL = process.env.LIVEKIT_URL ?? "";
const API_KEY = process.env.LIVEKIT_API_KEY ?? "";
const API_SECRET = process.env.LIVEKIT_API_SECRET ?? "";

if (!LIVEKIT_URL || !API_KEY || !API_SECRET) {
  throw new Error("Missing LiveKit environment variables");
}

async function createParticipantToken(userInfo: AccessTokenOptions, roomName: string) {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: "15m",
  });
  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  });
  return await at.toJwt();
}

async function dispatchAgentJob(roomName: string) {
  // The SDK's createJob is unreliable in Next.js, so we do it manually.
  // This requires creating a special token with agent permissions.
  const agentToken = new AccessToken(API_KEY, API_SECRET, {
    identity: "api-service",
    ttl: "10s",
  });
  agentToken.addGrant({ video: { agent: true } } as any);

  const job = {
    room: {
      name: roomName,
      empty_timeout: 30,
    },
    agent: {
      name: 'design_assistant',
    },
  };

  const livekitHost = LIVEKIT_URL.replace("wss://", "https://");
  const url = `${livekitHost}/twirp/livekit.JobService/CreateJob`;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${await agentToken.toJwt()}`,
  };

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(job),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Failed to dispatch agent job: ${response.status} ${errorBody}`);
  }

  console.log(`Successfully dispatched agent job for room: ${roomName}`);
}

export async function GET(req: NextRequest) {
  try {
    const roomName = `design-room-${uuidv4()}`;
    // Use a consistent identity for the user for now.
    const participantIdentity = `user-jane-doe`;

    // 1. Dispatch a job to an available agent.
    await dispatchAgentJob(roomName);
    
    // 2. Create a token for the user to join the now-active room.
    const userToken = await createParticipantToken(
      { identity: participantIdentity },
      roomName
    );

    const data = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: userToken,
      participantName: participantIdentity,
    };

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in connection-details API:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new NextResponse(message, { status: 500 });
  }
}
