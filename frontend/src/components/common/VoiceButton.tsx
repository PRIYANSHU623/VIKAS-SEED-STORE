import { Mic, Square } from "lucide-react";

interface VoiceButtonProps {
  isRecording: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export default function VoiceButton({
  isRecording,
  onClick,
  disabled = false
}: VoiceButtonProps) {
  return (
    <div className="relative flex items-center justify-center">
      {/* Outer Pulse rings for Recording feedback */}
      {isRecording && (
        <>
          <div className="absolute inset-0 rounded-full bg-rose-500/30 animate-ping duration-1000 scale-150" />
          <div className="absolute inset-0 rounded-full bg-rose-400/20 animate-ping duration-1500 delay-300 scale-125" />
        </>
      )}

      <button
        onClick={onClick}
        disabled={disabled}
        className={`relative z-10 p-6 rounded-full text-white transition-all duration-300 shadow-lg ${
          isRecording
            ? "bg-rose-500 hover:bg-rose-600 scale-110 active:scale-100 border-4 border-rose-100 animate-pulse"
            : "bg-green-600 hover:bg-green-700 active:scale-95 border-4 border-green-50"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        aria-label={isRecording ? "Stop Recording" : "Start Recording"}
      >
        {isRecording ? (
          <Square size={28} className="text-white" />
        ) : (
          <Mic size={28} className="text-white hover:scale-110 transition-transform" />
        )}
      </button>
    </div>
  );
}
