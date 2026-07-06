import { CheckCircle2, Circle, Clock } from "lucide-react";

interface TimelineCardProps {
  stage: string;
  days_offset: number;
  scheduled_date: string;
  status: string; // "completed", "current", "pending"
  description: string;
}

export default function TimelineCard({
  stage,
  days_offset,
  scheduled_date,
  status,
  description
}: TimelineCardProps) {
  const getStatusStyle = () => {
    if (status === "completed") {
      return {
        badge: "bg-emerald-50 text-emerald-700 border-emerald-100",
        icon: <CheckCircle2 size={16} className="text-emerald-500" />,
        line: "bg-emerald-300"
      };
    }
    if (status === "current") {
      return {
        badge: "bg-green-600 text-white border-transparent ring-4 ring-green-100",
        icon: <Clock size={16} className="text-white animate-spin-slow" />,
        line: "bg-green-500"
      };
    }
    return {
      badge: "bg-slate-50 text-slate-400 border-slate-200",
      icon: <Circle size={16} className="text-slate-300" />,
      line: "bg-slate-200"
    };
  };

  const styles = getStatusStyle();

  return (
    <div className="flex gap-4 relative animate-in fade-in slide-in-from-left duration-200">
      {/* Date marker */}
      <div className="w-16 shrink-0 text-right pr-2">
        <span className="text-[10px] font-black text-slate-400 uppercase block tracking-tight leading-none mb-0.5">
          Day {days_offset}
        </span>
        <span className="text-[10px] font-bold text-slate-500 block leading-none">
          {new Date(scheduled_date).toLocaleDateString([], { month: "short", day: "numeric" })}
        </span>
      </div>

      {/* Center line connector */}
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full border flex items-center justify-center shrink-0 ${styles.badge}`}>
          {styles.icon}
        </div>
      </div>

      {/* Description block */}
      <div className={`flex-grow bg-white p-3 rounded-2xl border border-slate-100/90 shadow-sm mb-4 ${status === "current" && "ring-1 ring-green-500/20 shadow"}`}>
        <h5 className="font-extrabold text-slate-800 text-sm m-0 flex items-center gap-1.5 justify-between">
          <span>{stage}</span>
          {status === "current" && (
            <span className="text-[9px] font-black uppercase tracking-wider bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
              Today
            </span>
          )}
        </h5>
        <p className="text-xs text-slate-500 m-0 mt-1 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
