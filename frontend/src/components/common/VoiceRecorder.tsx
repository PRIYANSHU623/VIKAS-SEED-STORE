import { useState, useRef, useEffect } from "react";
import { 
  Sparkles, 
  Mic, 
  Square, 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  AlertTriangle, 
  Loader2, 
  CheckCircle, 
  Wifi, 
  X,
  Keyboard
} from "lucide-react";
import api from "../../api/axios";
import VoiceButton from "./VoiceButton";

interface VoiceRecorderProps {
  onTranscriptReceived: (transcript: string, botAnswer: string, toolResults?: any) => void;
  language?: "en" | "hi";
  conversationId?: string;
  isOpen: boolean;
  onClose: () => void;
}

type VoiceState = 
  | "idle" 
  | "listening" 
  | "recording" 
  | "processing" 
  | "thinking" 
  | "speaking" 
  | "completed" 
  | "error";

// Extend window interface for Web Speech API in TypeScript
declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

export default function VoiceRecorder({
  onTranscriptReceived,
  language = "en",
  conversationId,
  isOpen,
  onClose
}: VoiceRecorderProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSpeechPaused, setIsSpeechPaused] = useState(false);
  const [onlineStatus, setOnlineStatus] = useState(navigator.onLine);

  // References for Web Audio API
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // References for Speech Recognition
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const maxDurationTimerRef = useRef<any>(null);

  // References for Speech Synthesis
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const [lastBotAnswer, setLastBotAnswer] = useState("");

  // Keyboard accessibility helper states
  const cardRef = useRef<HTMLDivElement | null>(null);

  // Track network connectivity changes
  useEffect(() => {
    const handleOnline = () => setOnlineStatus(true);
    const handleOffline = () => {
      setOnlineStatus(false);
      triggerError("Network connection lost. Please check your internet.");
    };
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleClose = () => {
    cancelAllFlows();
    onClose();
  };

  // Prevent background page scrolling while modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Escape" && isOpen) {
        e.preventDefault();
        handleClose();
        return;
      }

      if (!cardRef.current?.contains(document.activeElement)) return;

      if (e.code === "Space") {
        e.preventDefault();
        // Space bar toggles recording
        if (voiceState === "idle" || voiceState === "completed" || voiceState === "error") {
          startListeningFlow();
        } else if (voiceState === "recording" || voiceState === "listening") {
          stopRecordingFlow();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [voiceState, language, isOpen]);

  // Clean up Web Audio, recognition, and speech synthesis on unmount
  useEffect(() => {
    return () => {
      cleanupAudio();
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      clearAllTimers();
    };
  }, []);

  // Automatically monitor audio device changes
  useEffect(() => {
    const handleDeviceChange = async () => {
      // Re-initialize audio if device changes during recording
      if (voiceState === "recording" || voiceState === "listening") {
        console.log("Audio input device changed. Restarting audio stream...");
        cleanupAudio();
        await startAudioStream();
      }
    };
    navigator.mediaDevices?.addEventListener("devicechange", handleDeviceChange);
    return () => {
      navigator.mediaDevices?.removeEventListener("devicechange", handleDeviceChange);
    };
  }, [voiceState]);

  const clearAllTimers = () => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (maxDurationTimerRef.current) clearTimeout(maxDurationTimerRef.current);
  };

  const triggerError = (msg: string) => {
    setErrorMessage(msg);
    setVoiceState("error");
    cleanupAudio();
    clearAllTimers();
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
  };

  const cleanupAudio = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      if (audioContextRef.current.state !== "closed") {
        audioContextRef.current.close();
      }
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  };

  // Web Audio Stream capture
  const startAudioStream = async (): Promise<MediaStream | null> => {
    try {
      cleanupAudio();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Setup audio analyzer node for visualizer
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass();
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 128;
      analyserRef.current = analyser;
      source.connect(analyser);

      // Start canvas visualization
      visualizeWaveform();
      return stream;
    } catch (err: any) {
      console.error("Audio capture failed:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        triggerError("Microphone permission denied. Please allow access in browser settings.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        triggerError("No microphone found. Please connect an audio input device.");
      } else {
        triggerError("Failed to access microphone: " + err.message);
      }
      return null;
    }
  };

  // Real-time Waveform visualizer drawing loop
  const visualizeWaveform = () => {
    const canvas = canvasRef.current;
    if (!canvas || !analyserRef.current) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      if (!analyserRef.current) return;
      animationFrameRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);



      // Draw custom wave aesthetics on Canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 3;
      
      // Beautiful gradient color matching premium dark-green theme
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
      gradient.addColorStop(0, "rgba(34, 197, 94, 0.2)");
      gradient.addColorStop(0.5, "rgba(34, 197, 94, 1)");
      gradient.addColorStop(1, "rgba(34, 197, 94, 0.2)");
      ctx.strokeStyle = gradient;

      ctx.beginPath();
      const sliceWidth = canvas.width / 60;
      let x = 0;

      for (let i = 0; i < 60; i++) {
        // Build waveform lines based on volume data index
        const dataVal = dataArray[i % bufferLength] / 255.0;
        const amplitude = dataVal * (canvas.height * 0.85);
        const y = (canvas.height / 2) + (i % 2 === 0 ? amplitude / 2 : -amplitude / 2) * Math.sin(Date.now() * 0.004 + i);
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      // Draw middle baseline
      ctx.strokeStyle = "rgba(34, 197, 94, 0.15)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
    };

    draw();
  };

  // Reset silence auto-stop timer (3 seconds)
  const resetSilenceTimer = () => {
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    
    silenceTimerRef.current = setTimeout(() => {
      console.log("3 seconds of silence detected. Auto-stopping recording...");
      stopRecordingFlow();
    }, 3000);
  };

  // Master start listening sequence
  const startListeningFlow = async () => {
    // 1. Interrupt previous Speech Synthesis immediately if speaking
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setIsSpeechPaused(false);
    }

    setErrorMessage(null);
    setLiveTranscript("");
    setVoiceState("listening");

    // 2. Initialize Audio Devices and stream permission
    const stream = await startAudioStream();
    if (!stream) return; // Error handled inside startAudioStream

    // 3. Check browser Web Speech API support
    const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionClass) {
      triggerError("Speech Recognition is not supported in this browser. Please use Chrome/Edge.");
      return;
    }

    // 4. Initialize recognition
    try {
      const rec = new SpeechRecognitionClass();
      recognitionRef.current = rec;
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = language === "hi" ? "hi-IN" : "en-IN";

      rec.onstart = () => {
        setVoiceState("recording");
        resetSilenceTimer();

        // Safety backup timer: automatically stop after 60 seconds maximum
        maxDurationTimerRef.current = setTimeout(() => {
          console.log("60 seconds maximum duration reached. Auto-stopping...");
          stopRecordingFlow();
        }, 60000);
      };

      rec.onresult = (event: any) => {
        // Reset auto stop countdown
        resetSilenceTimer();

        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const transcriptOutput = finalTranscript || interimTranscript;
        if (transcriptOutput.trim()) {
          setLiveTranscript(transcriptOutput);
        }
      };

      rec.onerror = (event: any) => {
        console.error("Speech Recognition error:", event.error);
        if (event.error === "no-speech") {
          // If no speech is caught at all, gracefully fallback
          triggerError("No speech detected. Please speak clearly into your mic.");
        } else if (event.error === "not-allowed") {
          triggerError("Browser blocked speech recognition. Enable mic permissions.");
        } else {
          triggerError("Speech recognition failed: " + event.error);
        }
      };

      rec.onend = () => {
        // When speech recognition ends, trigger sending the finalized transcript
        handleAutoSend();
      };

      rec.start();
    } catch (err: any) {
      triggerError("Failed to initiate Speech Recognition: " + err.message);
    }
  };

  const stopRecordingFlow = () => {
    clearAllTimers();
    cleanupAudio();
    if (recognitionRef.current) {
      recognitionRef.current.stop(); // Triggers recognition.onend -> handleAutoSend
    }
  };

  // Master auto-send callback once user finishes speaking
  const handleAutoSend = async () => {
    clearAllTimers();
    cleanupAudio();

    const finalizedText = liveTranscript.trim();
    if (!finalizedText) {
      setVoiceState("idle");
      return;
    }

    setVoiceState("processing");

    try {
      // Transition status to AI thinking
      setVoiceState("thinking");

      // Query AI assistant API route
      const response = await api.post("/ai/chat", {
        message: finalizedText,
        conversation_id: conversationId
      });

      const { answer, response: fallbackResponse, tool_results } = response.data;
      const botAnswer = answer || fallbackResponse;

      setLastBotAnswer(botAnswer);
      setVoiceState("speaking");

      // Bubble details into core App state conversation history
      onTranscriptReceived(finalizedText, botAnswer, tool_results);

      // Play synthesized natural audio
      speakBotResponse(botAnswer);
    } catch (err: any) {
      console.error("Failed to fetch AI query response:", err);
      triggerError("Failed to reach AI Server. Check network status and try again.");
    }
  };

  // Clean Markdown formatting for clean Text-to-Speech
  const cleanMarkdownForSpeech = (text: string): string => {
    return text
      .replace(/#+\s+/g, "") // Remove headers
      .replace(/\*+/g, "")   // Remove bold/italic markers
      .replace(/-\s+/g, "")  // Remove dashes
      .replace(/`+[^`]*`+/g, "") // Remove code chunks
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1") // Simplify links
      .replace(/₹/g, "Rupees ") // Convert currency symbol
      .trim();
  };

  // Speak response using browser Speech Synthesis (TTS)
  const speakBotResponse = (text: string) => {
    if (!window.speechSynthesis) {
      console.warn("Speech Synthesis is not supported in this browser.");
      setVoiceState("completed");
      return;
    }

    // Cancel any current speaking utterance
    window.speechSynthesis.cancel();
    setIsSpeechPaused(false);

    const cleanText = cleanMarkdownForSpeech(text);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    currentUtteranceRef.current = utterance;

    // Pick dynamic language matching Hindi/English
    utterance.lang = language === "hi" ? "hi-IN" : "en-IN";

    // Bind voices dynamically
    const selectVoice = () => {
      const voices = window.speechSynthesis.getVoices();
      let selectedVoice = null;

      if (language === "hi") {
        // Look for Google Hindi, hi-IN local voices
        selectedVoice = voices.find(v => v.lang.startsWith("hi"));
      } else {
        // Look for Google English (India / UK / US)
        selectedVoice = voices.find(v => v.lang.startsWith("en-IN")) || 
                         voices.find(v => v.lang.startsWith("en"));
      }

      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
    };

    selectVoice();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = selectVoice;
    }

    // Adjust rate and volume for organic, premium voice feedback
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => {
      setVoiceState("speaking");
    };

    utterance.onend = () => {
      setVoiceState("completed");
      currentUtteranceRef.current = null;
    };

    utterance.onerror = (e) => {
      console.error("Speech Synthesis Utterance failure:", e);
      // Completed fallback if speech failed/blocked
      setVoiceState("completed");
      currentUtteranceRef.current = null;
    };

    window.speechSynthesis.speak(utterance);
  };

  // Controls for Speech Synthesis
  const handlePauseResumeSpeech = () => {
    if (!window.speechSynthesis) return;
    if (isSpeechPaused) {
      window.speechSynthesis.resume();
      setIsSpeechPaused(false);
    } else {
      window.speechSynthesis.pause();
      setIsSpeechPaused(true);
    }
  };

  const handleStopSpeech = () => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setIsSpeechPaused(false);
    setVoiceState("completed");
  };

  const handleReplaySpeech = () => {
    if (lastBotAnswer) {
      speakBotResponse(lastBotAnswer);
    }
  };

  const cancelAllFlows = () => {
    clearAllTimers();
    cleanupAudio();
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeechPaused(false);
    setVoiceState("idle");
  };

  // Helper styles based on voiceState state-machine values
  const getStateConfig = () => {
    switch (voiceState) {
      case "listening":
        return {
          title: "Listening...",
          sub: "Waiting for speech input",
          color: "text-amber-600 border-amber-200 bg-amber-50/50",
          icon: <Loader2 size={16} className="animate-spin text-amber-500" />
        };
      case "recording":
        return {
          title: "Recording Live",
          sub: "Speak clearly into your microphone",
          color: "text-red-600 border-red-200 bg-red-50/40",
          icon: <span className="h-2 w-2 rounded-full bg-red-600 animate-ping" />
        };
      case "processing":
        return {
          title: "Processing Speech",
          sub: "Parsing voice patterns into query text",
          color: "text-blue-600 border-blue-200 bg-blue-50/50",
          icon: <Loader2 size={16} className="animate-spin text-blue-500" />
        };
      case "thinking":
        return {
          title: "AI is Thinking",
          sub: "Compiling farming advice and RAG checks",
          color: "text-purple-600 border-purple-200 bg-purple-50/50",
          icon: <Sparkles size={16} className="animate-pulse text-purple-500" />
        };
      case "speaking":
        return {
          title: "AI is Speaking",
          sub: "Playing synthesized voice advisory response",
          color: "text-green-600 border-green-200 bg-green-50/50",
          icon: <Volume2 size={16} className="animate-bounce text-green-500" />
        };
      case "completed":
        return {
          title: "Advisory Complete",
          sub: "Ready for your next question",
          color: "text-emerald-700 border-emerald-200 bg-emerald-50/40",
          icon: <CheckCircle size={16} className="text-emerald-600" />
        };
      case "error":
        return {
          title: "Voice Assistant Error",
          sub: errorMessage || "An unexpected error occurred",
          color: "text-rose-700 border-rose-200 bg-rose-50/50",
          icon: <AlertTriangle size={16} className="text-rose-600" />
        };
      default:
        return {
          title: onlineStatus ? "Voice Assistant Active" : "Voice Assistant Offline",
          sub: "Tap microphone and start talking",
          color: "text-slate-600 border-slate-200 bg-slate-50/40",
          icon: <Wifi size={14} className="text-green-600" />
        };
    }
  };

  const stateCfg = getStateConfig();

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 flex items-center justify-center p-4 z-50 bg-slate-950/65 backdrop-blur-md transition-all duration-300 animate-fade-in"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="voice-assistant-title"
    >
      <div 
        ref={cardRef}
        tabIndex={0}
        onClick={(e) => e.stopPropagation()}
        className="flex flex-col w-full max-w-md bg-white border border-slate-200 rounded-3xl p-6 shadow-2xl relative focus:outline-none focus:ring-2 focus:ring-green-500 transition-all duration-300 animate-scale-in"
        aria-label="KrishiSathi AI Voice Assistant Card. Press Space to toggle recording. Press Escape to cancel."
      >
        {/* Close Button in top right */}
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 p-1.5 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-50 transition-colors"
          title="Close Voice Assistant"
          aria-label="Close Voice Assistant"
        >
          <X size={18} />
        </button>
      {/* Upper header controls */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-green-600" />
          <span className="text-xs font-black text-slate-800 uppercase tracking-wider">
            KrishiSathi Live Voice
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Online status badge */}
          <span className={`inline-flex items-center gap-1 text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${
            onlineStatus 
              ? "bg-green-50 text-green-700 border-green-100" 
              : "bg-red-50 text-red-700 border-red-100"
          }`}>
            {onlineStatus ? "Connected" : "Offline"}
          </span>
          {/* Active Language Badge */}
          <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-600">
            {language === "hi" ? "Hindi (हिंदी)" : "English"}
          </span>
        </div>
      </div>

      {/* Voice Status Indicator Pill */}
      <div className={`flex items-start gap-2.5 px-3.5 py-2.5 border rounded-2xl text-xs font-medium mb-4 transition-all duration-300 ${stateCfg.color}`}>
        <div className="mt-0.5">{stateCfg.icon}</div>
        <div>
          <strong className="block font-black tracking-tight">{stateCfg.title}</strong>
          <span className="text-[11px] font-medium leading-relaxed opacity-90">{stateCfg.sub}</span>
        </div>
      </div>

      {/* Visual Live Waveform Canvas */}
      <div className="relative w-full h-24 bg-slate-50 border border-slate-100 rounded-2xl overflow-hidden mb-4 shadow-inner flex items-center justify-center">
        <canvas 
          ref={canvasRef} 
          width={380} 
          height={96} 
          className="w-full h-full object-cover" 
        />
        {voiceState === "idle" && (
          <div className="absolute flex flex-col items-center justify-center text-slate-350 select-none pointer-events-none">
            <Mic size={24} className="mb-1" />
            <span className="text-[10px] font-bold uppercase tracking-wider">Waveform Visualizer</span>
          </div>
        )}
      </div>

      {/* Live Transcript / Response Preview Field */}
      {liveTranscript && (
        <div className="w-full bg-slate-50 border border-slate-100 rounded-2xl p-3.5 mb-4 max-h-24 overflow-y-auto text-xs leading-relaxed animate-fade-in">
          <strong className="block text-[10px] font-black uppercase tracking-wider text-slate-400 mb-1">
            {voiceState === "recording" || voiceState === "listening" ? "Live Transcript" : "Speech Input"}
          </strong>
          <span className="text-slate-700 font-semibold italic">"{liveTranscript}"</span>
        </div>
      )}

      {/* Audio Playback control panel (For Speaks State) */}
      {voiceState === "speaking" && (
        <div className="flex items-center justify-center gap-3 bg-slate-50 border border-slate-100 p-3 rounded-2xl mb-4 animate-scale-in">
          {/* Pause / Resume */}
          <button
            onClick={handlePauseResumeSpeech}
            className="p-2.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 active:scale-95 transition-all rounded-full"
            title={isSpeechPaused ? "Resume response" : "Pause response"}
            aria-label={isSpeechPaused ? "Resume voice response" : "Pause voice response"}
          >
            {isSpeechPaused ? <Play size={16} /> : <Pause size={16} />}
          </button>
          {/* Stop speaking */}
          <button
            onClick={handleStopSpeech}
            className="p-2.5 bg-white border border-slate-200 text-rose-600 hover:bg-rose-50 hover:border-rose-100 active:scale-95 transition-all rounded-full"
            title="Stop response"
            aria-label="Stop playing response"
          >
            <Square size={16} />
          </button>
          {/* Replay */}
          <button
            onClick={handleReplaySpeech}
            className="p-2.5 bg-white border border-slate-200 text-slate-750 hover:bg-slate-50 active:scale-95 transition-all rounded-full"
            title="Replay response"
            aria-label="Replay response audio"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      )}

      {/* Core Center Microphone Button Trigger */}
      <div className="flex items-center justify-center gap-4 py-2 mt-1">
        <VoiceButton
          isRecording={voiceState === "recording" || voiceState === "listening"}
          onClick={
            voiceState === "recording" || voiceState === "listening"
              ? stopRecordingFlow 
              : startListeningFlow
          }
          disabled={voiceState === "processing" || voiceState === "thinking" || !onlineStatus}
        />
        
        {/* Close/Cancel Flow Button */}
        {voiceState !== "idle" && (
          <button
            onClick={cancelAllFlows}
            className="p-3 bg-slate-100 hover:bg-slate-250 text-slate-600 rounded-full border border-slate-200 shadow-sm active:scale-95 transition-all"
            title="Cancel voice action"
            aria-label="Cancel active voice assistant process"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Keyboard Helper Tips */}
      <div className="mt-4 flex items-center justify-center gap-1.5 text-[9px] font-bold text-slate-400 border-t border-slate-100 pt-3">
        <Keyboard size={12} className="text-slate-350" />
        <span>Space: Toggle Mic</span>
        <span className="text-slate-300">•</span>
        <span>Esc: Cancel</span>
      </div>
      </div>
    </div>
  );
}
