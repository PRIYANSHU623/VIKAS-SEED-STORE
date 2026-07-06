import { Sprout, ShieldAlert, Wheat, Layers } from "lucide-react";

interface ScheduleItem {
  day: number;
  fertilizer?: string;
  herbicide?: string;
  pesticide?: string;
  quantity: string;
}

interface ProductItem {
  category: string;
  name: string;
  price: number;
}

interface FarmPlanCardProps {
  plan: {
    crop: string;
    suitable_variety: string;
    recommended_seed: string;
    suitable_season: string;
    suitable_soil: string;
    required_water: string;
    fertilizer_schedule: ScheduleItem[];
    herbicide_schedule: ScheduleItem[];
    pesticide_schedule: ScheduleItem[];
    disease_prevention_tips: string[];
    weather_risks: string;
    estimated_cost: number;
    expected_yield: string;
    recommended_store_products: ProductItem[];
    alternative_products: ProductItem[];
    harvest_time: string;
  };
}

export default function FarmPlanCard({ plan }: FarmPlanCardProps) {
  if (!plan) return null;

  return (
    <div className="bg-gradient-to-br from-green-50/45 to-white border border-slate-200 rounded-3xl p-6 shadow-md hover:shadow-lg transition-all duration-300 max-w-2xl my-4">
      {/* Header Info */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4 mb-4">
        <div>
          <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-green-100 text-green-800 border border-green-200">
            {plan.suitable_season} Schedule
          </span>
          <h3 className="text-xl font-black text-slate-800 mt-2 mb-0.5 flex items-center gap-1.5">
            <Wheat size={20} className="text-green-600 animate-pulse" /> {plan.crop} Farm Plan
          </h3>
          <p className="text-xs text-slate-500 my-0">
            Suitable Variety: <strong className="text-slate-700">{plan.suitable_variety}</strong>
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Estimated Cost</span>
          <span className="text-xl font-black text-green-700">₹{plan.estimated_cost}</span>
        </div>
      </div>

      {/* Soil, Water & Yield Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <div className="bg-white p-3 rounded-2xl border border-slate-100/80 shadow-sm text-xs">
          <strong className="block text-slate-400 uppercase tracking-wider font-extrabold text-[9px] mb-1">Suitable Soil</strong>
          <span className="text-slate-700 font-semibold">{plan.suitable_soil}</span>
        </div>
        <div className="bg-white p-3 rounded-2xl border border-slate-100/80 shadow-sm text-xs">
          <strong className="block text-slate-400 uppercase tracking-wider font-extrabold text-[9px] mb-1">Water Requirement</strong>
          <span className="text-slate-700 font-semibold">{plan.required_water}</span>
        </div>
        <div className="bg-white p-3 rounded-2xl border border-slate-100/80 shadow-sm text-xs">
          <strong className="block text-slate-400 uppercase tracking-wider font-extrabold text-[9px] mb-1">Expected Yield</strong>
          <span className="text-slate-700 font-semibold">{plan.expected_yield}</span>
        </div>
      </div>

      {/* Sowing & Input Timelines */}
      <div className="space-y-4">
        {/* Fertilizer Plan */}
        <div>
          <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1 mb-2">
            <Layers size={14} className="text-green-600" /> Fertilizer Schedule
          </h4>
          <div className="space-y-1.5">
            {plan.fertilizer_schedule.map((item, i) => (
              <div key={i} className="flex justify-between items-center bg-white px-3.5 py-2 rounded-xl border border-slate-100 shadow-sm text-xs">
                <span className="font-bold text-slate-500">Day {item.day}</span>
                <span className="font-semibold text-slate-800">{item.fertilizer}</span>
                <span className="font-extrabold text-slate-600">{item.quantity}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Weed & Pest Control */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Herbicide */}
          <div>
            <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1 mb-2">
              <Sprout size={14} className="text-green-600" /> Weed Control
            </h4>
            {plan.herbicide_schedule.map((item, i) => (
              <div key={i} className="bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm text-xs">
                <div className="flex justify-between font-bold text-slate-500 mb-1">
                  <span>Day {item.day}</span>
                  <span className="text-green-600">{item.quantity}</span>
                </div>
                <span className="font-semibold text-slate-800">{item.herbicide}</span>
              </div>
            ))}
          </div>

          {/* Pesticide */}
          <div>
            <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1 mb-2">
              <ShieldAlert size={14} className="text-green-600" /> Pest Protection
            </h4>
            {plan.pesticide_schedule.map((item, i) => (
              <div key={i} className="bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm text-xs">
                <div className="flex justify-between font-bold text-slate-500 mb-1">
                  <span>Day {item.day}</span>
                  <span className="text-green-600">{item.quantity}</span>
                </div>
                <span className="font-semibold text-slate-800">{item.pesticide}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Disease Tips & Weather Risks */}
      <div className="mt-5 space-y-3 bg-slate-50 p-4 rounded-2xl border border-slate-100">
        <div>
          <strong className="block text-xs text-slate-700 font-bold mb-1">📋 Disease Prevention:</strong>
          <ul className="list-disc pl-4 space-y-1 text-xs text-slate-500 leading-relaxed m-0">
            {plan.disease_prevention_tips.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
        <div className="pt-2 border-t border-slate-200/50">
          <strong className="block text-xs text-amber-800 font-bold mb-0.5 flex items-center gap-1">
            ⚠️ Weather Risks:
          </strong>
          <p className="text-xs text-amber-700 m-0 leading-relaxed">{plan.weather_risks}</p>
        </div>
      </div>

      {/* Recommended Store Products */}
      <div className="mt-5 pt-4 border-t border-slate-150">
        <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 mb-2">
          Recommended Catalog Products
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {plan.recommended_store_products.map((prod, i) => (
            <div key={i} className="flex justify-between items-center bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm">
              <div>
                <span className="text-[9px] font-bold text-slate-400 uppercase block leading-none mb-0.5">{prod.category}</span>
                <span className="font-bold text-slate-700">{prod.name}</span>
              </div>
              <span className="font-black text-green-700">₹{prod.price}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
