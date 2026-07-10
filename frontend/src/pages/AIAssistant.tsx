import { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Sparkles, 
  User, 
  Sprout, 
  Bot, 
  Mic, 
  Plus, 
  MessageSquare, 
  Menu, 
  X,
  Trash2,
  HelpCircle
} from "lucide-react";
import { askAIChat } from "../api/aiApi";
import WeatherCard from "../components/common/WeatherCard";
import RecommendationCard from "../components/common/RecommendationCard";
import FarmPlanCard from "../components/common/FarmPlanCard";
import CropCalendar from "../components/common/CropCalendar";
import VoiceRecorder from "../components/common/VoiceRecorder";

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
  timestamp: Date;
  toolResults?: {
    weather?: {
      success: boolean;
      data: any;
    };
    recommendation?: {
      success: boolean;
      data: {
        recommendations: any[];
        bundles: any[];
      };
    };
    farm_plan?: {
      success: boolean;
      data: {
        action: string;
        plan?: any;
        plans?: any[];
      };
    };
    calendar?: {
      success: boolean;
      data: any;
    };
  };
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

export default function AIAssistant() {
  // Load conversations list from localStorage or initialize defaults
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const saved = localStorage.getItem("krishisathi_chats");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.map((c: any) => ({
          ...c,
          messages: c.messages.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
        }));
      } catch (e) {
        console.warn("Failed to load local chat history:", e);
      }
    }
    return [
      {
        id: "chat-default",
        title: "Paddy & Wheat Advisory",
        messages: [
          {
            id: "init-1",
            sender: "bot",
            text: "Namaste! I am KrishiSathi's AI Assistant. You can ask me about crop diseases, high-yield seed varieties, NPK fertilizer dosages, local weather planning, or general crop care tips. How can I help you today?",
            timestamp: new Date()
          }
        ]
      }
    ];
  });

  const [activeChatId, setActiveChatId] = useState<string>(() => {
    return conversations[0]?.id || "chat-default";
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [voiceActive, setVoiceActive] = useState(false);
  const [language, setLanguage] = useState<"en" | "hi">("en");

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem("krishisathi_chats", JSON.stringify(conversations));
  }, [conversations]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, activeChatId, loading]);

  const activeChat = conversations.find(c => c.id === activeChatId) || conversations[0];

  const suggestions = [
    { text: "Recommend wheat seed package", icon: <Sprout className="text-green-600" /> },
    { text: "Will it rain tomorrow in Ludhiana?", icon: <Sparkles className="text-amber-500" /> },
    { text: "Organic ways to control termites?", icon: <HelpCircle className="text-blue-500" /> },
    { text: "I want to grow paddy.", icon: <Sprout className="text-emerald-500" /> }
  ];

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date()
    };

    // Update messages in current conversation
    setConversations(prev => prev.map(c => {
      if (c.id === activeChatId) {
        // Auto update title if it's currently default/generic
        const updatedTitle = c.title === "New Chat" || c.messages.length === 1
          ? (textToSend.length > 25 ? textToSend.substring(0, 22) + "..." : textToSend)
          : c.title;

        return {
          ...c,
          title: updatedTitle,
          messages: [...c.messages, userMsg]
        };
      }
      return c;
    }));

    setInput("");
    setLoading(true);

    try {
      const responsePayload = await askAIChat(textToSend, activeChatId);
      
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: responsePayload.answer || responsePayload.response,
        timestamp: new Date(),
        toolResults: responsePayload.tool_results
      };

      setConversations(prev => prev.map(c => {
        if (c.id === activeChatId) {
          return {
            ...c,
            messages: [...c.messages, botMsg]
          };
        }
        return c;
      }));
    } catch (error) {
      console.warn("Backend AI chat failed, falling back to local fallback response:", error);
      
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: "I experienced a connection issue, but here is a quick guide. Please ensure optimal irrigation and check the weather warning panels inside the crop calendar page if you are planning to sow seeds.",
        timestamp: new Date()
      };

      setConversations(prev => prev.map(c => {
        if (c.id === activeChatId) {
          return {
            ...c,
            messages: [...c.messages, botMsg]
          };
        }
        return c;
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    const newId = `chat-${Date.now()}`;
    const newChat: Conversation = {
      id: newId,
      title: "New Chat",
      messages: [
        {
          id: `init-${Date.now()}`,
          sender: "bot",
          text: "Namaste! This is a new advisory session. Ask me any farming questions or type 'I want to grow paddy' to generate a plan.",
          timestamp: new Date()
        }
      ]
    };
    setConversations(prev => [newChat, ...prev]);
    setActiveChatId(newId);
    setVoiceActive(false);
  };

  const handleDeleteChat = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (conversations.length === 1) {
      alert("You must keep at least one active conversation session.");
      return;
    }
    const filtered = conversations.filter(c => c.id !== id);
    setConversations(filtered);
    if (activeChatId === id) {
      setActiveChatId(filtered[0].id);
    }
  };

  const handleClearHistory = () => {
    if (window.confirm("Are you sure you want to permanently clear all chats?")) {
      const resetChat: Conversation = {
        id: "chat-default",
        title: "Paddy & Wheat Advisory",
        messages: [
          {
            id: "init-1",
            sender: "bot",
            text: "Namaste! I am KrishiSathi's AI Assistant. Ask me anything to start a new chat.",
            timestamp: new Date()
          }
        ]
      };
      setConversations([resetChat]);
      setActiveChatId("chat-default");
      setVoiceActive(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-slate-50 relative font-sans overflow-hidden">
      
      {/* Mobile Sidebar Overlay Backdrop */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-slate-950/45 backdrop-blur-xs z-20 md:hidden"
        />
      )}

      {/* Collapsible Left Sidebar (ChatGPT Dark Slate Style) */}
      <div 
        className={`${
          sidebarOpen ? "w-64 translate-x-0" : "w-0 -translate-x-full md:w-0"
        } transition-all duration-300 bg-slate-900 text-slate-200 flex flex-col shrink-0 h-full overflow-hidden z-30 absolute md:relative border-r border-slate-950`}
      >
        {/* Sidebar Header */}
        <div className="p-3.5 flex items-center justify-between border-b border-slate-800/80">
          <button 
            onClick={handleNewChat}
            className="flex items-center gap-2.5 w-full bg-slate-800 hover:bg-slate-700/80 text-white rounded-xl py-2 px-3 text-xs font-bold transition-all border border-slate-700 active:scale-95"
          >
            <Plus size={16} /> New Chat
          </button>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="p-2 text-slate-400 hover:text-white rounded-lg md:hidden ml-2"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Conversation List */}
        <div className="flex-grow overflow-y-auto p-2.5 space-y-1.5 scrollbar-thin">
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-500 px-2 block mb-1">Recent Chats</span>
          {conversations.map((c) => {
            const isActive = c.id === activeChatId;
            return (
              <div
                key={c.id}
                onClick={() => {
                  setActiveChatId(c.id);
                  // Hide sidebar drawer on mobile after clicking
                  if (window.innerWidth < 768) setSidebarOpen(false);
                }}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-all text-xs font-semibold ${
                  isActive 
                    ? "bg-slate-800 text-white shadow-sm" 
                    : "text-slate-400 hover:bg-slate-850 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate max-w-[80%]">
                  <MessageSquare size={14} className={isActive ? "text-green-500" : "text-slate-500"} />
                  <span className="truncate">{c.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteChat(c.id, e)}
                  className="p-1 text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-all rounded"
                  title="Delete Conversation"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 bg-slate-950/60 border-t border-slate-850 flex flex-col gap-2">
          {/* Language Toggle */}
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-1.5 rounded-xl">
            <span className="text-[10px] font-black uppercase text-slate-500 pl-1.5">Voice Input</span>
            <div className="flex bg-slate-950 p-0.5 rounded-lg border border-slate-800">
              <button
                onClick={() => setLanguage("en")}
                className={`text-[10px] px-2 py-0.5 rounded font-black tracking-wide ${language === "en" ? "bg-green-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi")}
                className={`text-[10px] px-2 py-0.5 rounded font-black tracking-wide ${language === "hi" ? "bg-green-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                हिंदी
              </button>
            </div>
          </div>
          <button 
            onClick={handleClearHistory}
            className="flex items-center justify-center gap-1.5 w-full text-slate-500 hover:text-rose-400 text-[10px] font-extrabold uppercase py-2 transition-colors"
          >
            <Trash2 size={12} /> Clear Chat Logs
          </button>
        </div>
      </div>

      {/* Main Workspace Frame */}
      <div className="flex-grow flex flex-col h-full bg-white overflow-hidden relative">
        
        {/* Simple ChatGPT Header Bar */}
        <div className="h-14 border-b border-slate-100 px-4 flex items-center justify-between bg-white shrink-0 shadow-sm z-10">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button 
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-slate-50 text-slate-600 rounded-xl transition-all border border-slate-200 shadow-sm"
                aria-label="Open Sidebar"
              >
                <Menu size={18} />
              </button>
            )}
            <div>
              <h2 className="text-sm text-gray-800 font-extrabold my-0 flex items-center gap-1.5">
                <Sprout size={16} className="text-green-600" /> KrishiSathi AI
              </h2>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block leading-none mt-0.5">
                {activeChat?.title || "Farming advisory"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black uppercase bg-green-50 border border-green-150 px-2 py-0.5 rounded text-green-700">
              AGY-Model 2.5
            </span>
          </div>
        </div>

        {/* Message Thread Container */}
        <div className="flex-grow overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin bg-slate-50/20">
          <div className="max-w-3xl mx-auto space-y-6">
            
            {/* Suggestion Dashboard for Empty Chats (ChatGPT Dashboard Style) */}
            {activeChat?.messages.length <= 1 && !loading && (
              <div className="flex flex-col items-center justify-center py-10 md:py-16 text-center space-y-6">
                <div className="inline-flex p-4 bg-green-50 border border-green-100 rounded-full text-green-600 animate-bounce">
                  <Sprout size={36} />
                </div>
                <div>
                  <h1 className="text-2xl font-black text-slate-800 tracking-tight my-0">How can I help with your crops today?</h1>
                  <p className="text-xs text-slate-400 font-semibold mt-1.5 leading-relaxed">Ask about high-yield seeds, DAP schedules, weather impacts, or grow timelines.</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                  {suggestions.map((sug, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(sug.text)}
                      className="flex items-center gap-3 bg-white hover:bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5 text-left text-xs font-semibold text-slate-700 active:scale-95 transition-all shadow-sm"
                    >
                      <div className="p-2 bg-slate-50 border border-slate-100 rounded-lg shadow-sm shrink-0">
                        {sug.icon}
                      </div>
                      <span className="flex-grow truncate">{sug.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeChat?.messages.map((msg) => {
              const isBot = msg.sender === "bot";
              return (
                <div 
                  key={msg.id}
                  className={`flex gap-4 ${isBot ? "items-start" : "items-start flex-row-reverse"}`}
                >
                  {/* Clean Avatar */}
                  <div className={`h-8 w-8 rounded-full border flex items-center justify-center shrink-0 shadow-sm ${
                    isBot 
                      ? "bg-green-50 border-green-150 text-green-600" 
                      : "bg-slate-100 border-slate-200 text-slate-500"
                  }`}>
                    {isBot ? <Bot size={15} /> : <User size={15} />}
                  </div>

                  {/* Message Bubble (Modern Flat ChatGPT Style) */}
                  <div className="flex-grow max-w-[85%] space-y-2">
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isBot 
                        ? "bg-white border border-slate-100 shadow-sm text-slate-800" 
                        : "bg-slate-800 text-white shadow font-semibold"
                    }`}>
                      {msg.text}
                    </div>

                    {/* Integrated Tool Result Visual Cards */}
                    {isBot && msg.toolResults && (
                      <div className="space-y-3 mt-2 w-full max-w-full">
                        {msg.toolResults.weather?.success && msg.toolResults.weather?.data && (
                          <WeatherCard data={msg.toolResults.weather.data} />
                        )}
                        {msg.toolResults.recommendation?.success && msg.toolResults.recommendation?.data && (
                          <RecommendationCard data={msg.toolResults.recommendation.data} />
                        )}
                        {msg.toolResults.farm_plan?.success && msg.toolResults.farm_plan?.data && (
                          msg.toolResults.farm_plan.data.action === "list" ? (
                            <div className="bg-white border border-slate-250 rounded-2xl p-4 text-xs max-w-md shadow-sm">
                              <strong className="block text-slate-700 font-extrabold mb-2 uppercase tracking-wide">📂 Saved Farm Plans:</strong>
                              {msg.toolResults.farm_plan.data.plans?.map((p: any) => (
                                <div key={p.id} className="border-b border-slate-100 py-2 last:border-b-0 flex justify-between items-center">
                                  <div>
                                    <span className="font-extrabold text-slate-800">{p.crop}</span> 
                                    <span className="text-[10px] text-slate-400 font-bold ml-1.5 uppercase">({p.season})</span>
                                  </div>
                                  <span className="font-black text-green-700">₹{p.estimated_cost}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            msg.toolResults.farm_plan.data.plan && <FarmPlanCard plan={msg.toolResults.farm_plan.data.plan} />
                          )
                        )}
                        {msg.toolResults.calendar?.success && msg.toolResults.calendar?.data && (
                          <CropCalendar calendar={msg.toolResults.calendar.data} />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Spinner Loader when compiling */}
            {loading && (
              <div className="flex gap-4 items-start animate-pulse">
                <div className="h-8 w-8 rounded-full bg-green-50 border border-green-150 flex items-center justify-center shrink-0 text-green-600">
                  <Bot size={15} />
                </div>
                <div className="bg-white border border-slate-100 text-slate-500 text-sm p-4 rounded-2xl shadow-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-green-600 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-green-600 rounded-full animate-bounce delay-100"></span>
                  <span className="w-1.5 h-1.5 bg-green-600 rounded-full animate-bounce delay-200"></span>
                  <span>AI Crop Doctor compiling recommendations...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Voice Assistant Modal Overlay */}
        <VoiceRecorder
          isOpen={voiceActive}
          onClose={() => setVoiceActive(false)}
          language={language}
          conversationId={activeChatId}
          onTranscriptReceived={(transcript, botAnswer, toolResults) => {
            const userMsg: Message = {
              id: `user-${Date.now()}`,
              sender: "user",
              text: transcript,
              timestamp: new Date()
            };
            const botMsg: Message = {
              id: `bot-${Date.now()}`,
              sender: "bot",
              text: botAnswer,
              timestamp: new Date(),
              toolResults: toolResults
            };
            setConversations(prev => prev.map(c => {
              if (c.id === activeChatId) {
                return {
                  ...c,
                  messages: [...c.messages, userMsg, botMsg]
                };
              }
              return c;
            }));
          }}
        />

        {/* Integrated Bottom Input Bar */}
        <div className="p-4 bg-white border-t border-slate-100 shrink-0 z-10">
          <div className="max-w-3xl mx-auto flex items-center gap-3.5 relative">
            
            {/* Toggle Mic Button (Green/Pink color block) */}
            <button
              onClick={() => setVoiceActive(!voiceActive)}
              className={`p-3.5 rounded-full border transition-all active:scale-95 flex items-center justify-center shrink-0 shadow-md ${
                voiceActive 
                  ? "bg-rose-500 border-rose-600 text-white hover:bg-rose-650" 
                  : "bg-green-600 border-green-700 text-white hover:bg-green-700"
              }`}
              title={voiceActive ? "Deactivate Voice Assistant" : "Activate Voice Assistant"}
              aria-label="Toggle Voice Assistant Mode"
            >
              <Mic size={18} />
            </button>

            {/* Combined Text Input Form */}
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                handleSend(input);
              }}
              className="flex-grow flex items-center relative"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message KrishiSathi AI..."
                className="w-full pl-4 pr-12 py-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-slate-800 font-medium placeholder-slate-400 shadow-inner"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="absolute right-2 p-2 bg-slate-800 hover:bg-slate-900 active:scale-95 text-white rounded-xl disabled:opacity-30 disabled:hover:bg-slate-800 shadow transition-all"
                aria-label="Send Message"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
}
