import { Calendar, AlertTriangle } from "lucide-react";
import TimelineCard from "./TimelineCard";

interface CalendarStage {
  stage: string;
  days_offset: number;
  scheduled_date: string;
  status: string; // "completed", "current", "pending"
  description: string;
}

interface CropCalendarProps {
  calendar: {
    crop: string;
    start_date: string;
    stages: CalendarStage[];
    weather_warnings: string[];
  };
}

export default function CropCalendar({ calendar }: CropCalendarProps) {
  if (!calendar) return null;

  const { crop, stages, weather_warnings } = calendar;

  // Calculate progress ratio
  const completedCount = stages.filter((s) => s.status === "completed").length;
  const currentCount = stages.filter((s) => s.status === "current").length;
  const totalCount = stages.length;
  
  // Progress percentage (current stage counts as partial/start)
  const progressPct = Math.round(((completedCount + (currentCount ? 0.5 : 0)) / totalCount) * 100);

  return (
    <div className="bg-gradient-to-br from-slate-50 to-white border border-slate-200 rounded-3xl p-5 shadow-md max-w-2xl my-4 hover:shadow-lg transition-all duration-300">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3.5 mb-4">
        <div>
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Personalized Schedule</span>
          <h3 className="text-base font-extrabold text-slate-800 m-0 mt-0.5 flex items-center gap-1.5">
            <Calendar size={18} className="text-green-600 animate-bounce" /> {crop} Cultivation Calendar
          </h3>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Completed Stages</span>
          <span className="text-xs font-black text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
            {completedCount} / {totalCount}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-5 bg-white p-3 rounded-2xl border border-slate-100 shadow-sm">
        <div className="flex justify-between items-center text-xs font-bold text-slate-500 mb-1.5">
          <span>Overall Field Progress</span>
          <span className="text-green-700 font-extrabold">{progressPct}%</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div 
            className="bg-green-600 h-full rounded-full transition-all duration-500" 
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Weather Warnings Shelf */}
      {weather_warnings && weather_warnings.length > 0 && (
        <div className="bg-rose-50/50 border border-rose-100 rounded-2xl p-3.5 mb-5 space-y-2 text-xs">
          <strong className="font-extrabold text-rose-800 flex items-center gap-1.5 uppercase tracking-wide">
            <AlertTriangle size={15} className="text-rose-600 animate-pulse" /> Sowing Weather Alerts:
          </strong>
          <ul className="list-disc pl-4 space-y-1 text-rose-700 m-0 leading-relaxed font-medium">
            {weather_warnings.map((warn, i) => (
              <li key={i}>{warn}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Vertical Timeline Events */}
      <div className="relative pl-2.5 space-y-1">
        {/* Vertical line indicator */}
        <div className="absolute left-[83px] top-4 bottom-4 w-0.5 bg-slate-200" />

        {stages.map((stageItem, idx) => (
          <TimelineCard 
            key={idx}
            stage={stageItem.stage}
            days_offset={stageItem.days_offset}
            scheduled_date={stageItem.scheduled_date}
            status={stageItem.status}
            description={stageItem.description}
          />
        ))}
      </div>
    </div>
  );
}
