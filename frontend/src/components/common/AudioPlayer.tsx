import React, { useRef, useState, useEffect } from "react";
import { Play, Pause, Volume2, VolumeX, RotateCcw } from "lucide-react";

interface AudioPlayerProps {
  audioUrl: string;
  isPlaying: boolean;
  onTogglePlay: () => void;
}

export default function AudioPlayer({
  audioUrl,
  isPlaying,
  onTogglePlay
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [muted, setMuted] = useState(false);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    const onLoadedMetadata = () => setDuration(audio.duration);
    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onEnded = () => {
      setCurrentTime(0);
      if (isPlaying) {
        onTogglePlay();
      }
    };

    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);

    if (isPlaying) {
      audio.play().catch((e) => console.warn("Audio playback blocked:", e));
    }

    return () => {
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
      audio.pause();
    };
  }, [audioUrl]);

  useEffect(() => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.play().catch((e) => console.warn("Playback error:", e));
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying]);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setCurrentTime(val);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !muted;
      setMuted(!muted);
    }
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setCurrentTime(0);
      if (!isPlaying) {
        onTogglePlay();
      }
    }
  };

  const formatTime = (time: number) => {
    if (isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
  };

  return (
    <div className="flex flex-col w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
      <div className="flex items-center gap-3">
        {/* Play/Pause Button */}
        <button
          onClick={onTogglePlay}
          className="p-2.5 bg-green-600 hover:bg-green-700 active:scale-95 text-white rounded-full transition-all"
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>

        {/* Restart Button */}
        <button
          onClick={handleRestart}
          className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition-all"
          title="Restart Audio"
        >
          <RotateCcw size={14} />
        </button>

        {/* Progress bar */}
        <div className="flex-grow flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-400">{formatTime(currentTime)}</span>
          <input
            type="range"
            min="0"
            max={duration || 100}
            value={currentTime}
            onChange={handleSliderChange}
            className="flex-grow h-1.5 bg-slate-150 rounded-lg appearance-none cursor-pointer accent-green-600"
          />
          <span className="text-[10px] font-bold text-slate-400">{formatTime(duration)}</span>
        </div>

        {/* Mute Button */}
        <button
          onClick={toggleMute}
          className="p-2 bg-slate-50 hover:bg-slate-100 border border-slate-250 text-slate-500 rounded-lg transition-all"
        >
          {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
        </button>
      </div>
    </div>
  );
}
