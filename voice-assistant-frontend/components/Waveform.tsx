"use client";
import { useTracks } from "@livekit/components-react";
import { Track } from "livekit-client";
import { useEffect, useRef } from "react";

export function Waveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioTracks = useTracks([Track.Source.Microphone]);
  const audioTrack = audioTracks[0]?.publication.track as any;

  useEffect(() => {
    if (!audioTrack || !audioTrack.mediaStreamTrack) {
      return;
    }
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(
      new MediaStream([audioTrack.mediaStreamTrack])
    );
    source.connect(analyser);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const canvas = canvasRef.current;
    const canvasCtx = canvas?.getContext("2d");

    let animationFrameId: number;

    const draw = () => {
      animationFrameId = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);

      if (canvasCtx && canvas) {
        canvasCtx.fillStyle = "rgb(10 10 10 / 0%)";
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = "#E37ED0";
        canvasCtx.beginPath();

        const sliceWidth = (canvas.width * 1.0) / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * canvas.height) / 2;

          if (i === 0) {
            canvasCtx.moveTo(x, y);
          } else {
            canvasCtx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        canvasCtx.lineTo(canvas.width, canvas.height / 2);
        canvasCtx.stroke();
      }
    };

    draw();

    return () => {
      cancelAnimationFrame(animationFrameId);
      source.disconnect();
      audioContext.close();
    };
  }, [audioTrack]);

  return (
    <div className="w-full h-24 relative">
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  );
} 