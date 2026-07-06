import { 
  CloudRain, 
  Thermometer, 
  Wind, 
  Droplets, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle
} from "lucide-react";

interface SuitabilityDetail {
  score: number;
  suitable: boolean;
  reason: string;
}

interface WeatherCardProps {
  data: {
    location: string;
    temperature: number;
    humidity: number;
    wind_speed: number;
    rain_probability: number;
    forecast: string;
    recommendation: string;
    suitability: {
      spraying: SuitabilityDetail;
      irrigation: SuitabilityDetail;
      sowing: SuitabilityDetail;
      harvest: SuitabilityDetail;
      fertilizer: SuitabilityDetail;
    };
    risks: {
      heavy_rainfall: string;
      frost: string;
      heat_stress: string;
    };
  };
}

export default function WeatherCard({ data }: WeatherCardProps) {
  if (!data) return null;

  const {
    location,
    temperature,
    humidity,
    wind_speed,
    rain_probability,
    forecast,
    recommendation,
    suitability,
    risks
  } = data;



  const getScoreBg = (score: number) => {
    if (score >= 70) return "bg-emerald-50 text-emerald-700 border-emerald-100";
    if (score >= 40) return "bg-amber-50 text-amber-700 border-amber-100";
    return "bg-rose-50 text-rose-700 border-rose-100";
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-300 max-w-2xl my-3">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Current Forecast</span>
          <h3 className="text-lg font-black text-slate-800 my-0 flex items-center gap-1.5">
            {location}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100 flex items-center gap-1">
            <CloudRain size={12} className="animate-bounce" /> {forecast}
          </span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-4">
        {/* Temp */}
        <div className="bg-white p-3 rounded-xl border border-slate-100 flex items-center gap-3">
          <div className="p-2 bg-orange-50 text-orange-600 rounded-lg">
            <Thermometer size={18} />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider m-0">Temperature</p>
            <p className="text-base font-extrabold text-slate-800 m-0">{temperature}°C</p>
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-white p-3 rounded-xl border border-slate-100 flex items-center gap-3">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <Droplets size={18} />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider m-0">Humidity</p>
            <p className="text-base font-extrabold text-slate-800 m-0">{humidity}%</p>
          </div>
        </div>

        {/* Wind */}
        <div className="bg-white p-3 rounded-xl border border-slate-100 flex items-center gap-3">
          <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
            <Wind size={18} />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider m-0">Wind Speed</p>
            <p className="text-base font-extrabold text-slate-800 m-0">{wind_speed} km/h</p>
          </div>
        </div>

        {/* Rain Probability */}
        <div className="bg-white p-3 rounded-xl border border-slate-100 flex items-center gap-3">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
            <CloudRain size={18} />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider m-0">Rain Prob.</p>
            <p className="text-base font-extrabold text-slate-800 m-0">{rain_probability}%</p>
          </div>
        </div>
      </div>

      {/* Risks Banner */}
      <div className="bg-amber-50/50 border border-amber-100/75 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2 mb-4 text-xs">
        <span className="font-bold text-amber-800 flex items-center gap-1.5">
          <AlertTriangle size={14} className="text-amber-600" /> Critical Weather Risks:
        </span>
        <div className="flex gap-2">
          <span className={`px-2 py-0.5 rounded font-semibold border ${risks.heavy_rainfall === "High" ? "bg-red-50 text-red-700 border-red-100" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
            Heavy Rain: {risks.heavy_rainfall}
          </span>
          <span className={`px-2 py-0.5 rounded font-semibold border ${risks.frost === "High" ? "bg-blue-50 text-blue-700 border-blue-100" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
            Frost: {risks.frost}
          </span>
          <span className={`px-2 py-0.5 rounded font-semibold border ${risks.heat_stress === "High" ? "bg-orange-50 text-orange-700 border-orange-100" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
            Heat Stress: {risks.heat_stress}
          </span>
        </div>
      </div>

      {/* Agronomic Suitability Section */}
      <div className="space-y-3">
        <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 mb-1">Agronomic Suitability</h4>
        
        {Object.entries(suitability).map(([operation, details]) => (
          <div key={operation} className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex-grow">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-extrabold text-sm text-slate-700 uppercase tracking-tight">
                  {operation}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${getScoreBg(details.score)}`}>
                  {details.score}%
                </span>
              </div>
              <p className="text-xs text-slate-500 m-0">{details.reason}</p>
            </div>
            <div className="shrink-0 flex items-center gap-2">
              {details.suitable ? (
                <span className="text-emerald-600 text-xs font-bold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                  <CheckCircle2 size={13} /> Recommended
                </span>
              ) : (
                <span className="text-rose-600 text-xs font-bold flex items-center gap-1 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-100">
                  <XCircle size={13} /> Not Recommended
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* General Farming Advice */}
      <div className="mt-4 pt-3 border-t border-slate-100">
        <div className="p-3 bg-green-50/50 border border-green-100/60 rounded-xl text-xs text-green-800 leading-relaxed">
          <strong className="block text-green-900 font-bold mb-0.5">🌾 KrishiSathi Farm Advice:</strong>
          {recommendation}
        </div>
      </div>
    </div>
  );
}
