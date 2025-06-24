import { useIsSpeaking, useTracks } from "@livekit/components-react";
import { Participant, Track } from "livekit-client";
import { useMemo } from "react";

export const useVoiceAssistant = (participant: Participant | undefined) => {
  const isSpeaking = useIsSpeaking(participant);
  const allTracks = useTracks();

  const audioTrack = useMemo(() => {
    if (!participant) return;
    const track = allTracks.find(
      (t) =>
        t.participant.identity === participant.identity &&
        t.source === Track.Source.Unknown
    );
    return track?.publication.track;
  }, [allTracks, participant]);

  const state = useMemo(() => {
    if (isSpeaking) {
      return "speaking";
    }
    if (participant) {
      return "connected";
    }
    return "connecting";
  }, [isSpeaking, participant]);

  return {
    state,
    assistant: participant,
    audioTrack,
  };
}; 