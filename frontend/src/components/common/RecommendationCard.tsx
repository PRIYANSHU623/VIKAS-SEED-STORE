import { 
  Sparkles, 
  Check, 
  ChevronRight,
  PackageCheck
} from "lucide-react";

interface ProductRecommendation {
  product_id: number;
  name: string;
  brand: string;
  category: string;
  price: number;
  score: number;
  reason: string;
}

interface BundleItem {
  product_id: number;
  name: string;
  category: string;
  price: number;
}

interface BundleRecommendation {
  bundle_name: string;
  crop: string;
  items: BundleItem[];
  estimated_cost: number;
  reason: string;
  alternatives: {
    seeds: Array<{ product_id: number; name: string; price: number }>;
    fertilizers: Array<{ product_id: number; name: string; price: number }>;
    pesticides: Array<{ product_id: number; name: string; price: number }>;
    herbicides: Array<{ product_id: number; name: string; price: number }>;
  };
}

interface RecommendationCardProps {
  data: {
    recommendations: ProductRecommendation[];
    bundles: BundleRecommendation[];
  };
}

export default function RecommendationCard({ data }: RecommendationCardProps) {
  if (!data) return null;

  const { recommendations, bundles } = data;

  const getScoreColorClass = (score: number) => {
    if (score >= 80) return "text-emerald-600 bg-emerald-50 border-emerald-100";
    if (score >= 60) return "text-blue-600 bg-blue-50 border-blue-100";
    return "text-slate-600 bg-slate-50 border-slate-100";
  };

  return (
    <div className="space-y-6 max-w-2xl my-4">
      {/* 1. Bundled Packages Section */}
      {bundles && bundles.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-xs font-black uppercase tracking-wider text-slate-500 flex items-center gap-1.5 mb-1">
            <PackageCheck size={16} className="text-green-600" /> AI Farm Cultivation Packages
          </h4>
          
          {bundles.map((bundle, idx) => (
            <div 
              key={idx}
              className="bg-gradient-to-br from-green-50/50 to-white border-2 border-green-500/10 hover:border-green-500/30 rounded-2xl p-5 shadow-sm transition-all duration-300"
            >
              {/* Bundle Header */}
              <div className="flex flex-wrap justify-between items-start gap-2 border-b border-green-500/10 pb-3">
                <div>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-800 text-[10px] font-extrabold uppercase tracking-wide">
                    {bundle.crop} Package
                  </span>
                  <h3 className="text-base font-extrabold text-slate-800 mt-1 mb-0">
                    {bundle.bundle_name}
                  </h3>
                </div>
                <div className="text-right">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider m-0">Estimated Cost</p>
                  <p className="text-lg font-black text-green-700 m-0">₹{bundle.estimated_cost}</p>
                </div>
              </div>

              {/* Selection Reason */}
              <p className="text-xs text-slate-600 my-3 leading-relaxed italic bg-white/50 p-2.5 rounded-xl border border-green-500/5">
                💡 <strong>Why selected:</strong> {bundle.reason}
              </p>

              {/* Package Items */}
              <div className="space-y-2 mt-3">
                <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 m-0">Included Inputs:</p>
                {bundle.items.map((item, i) => (
                  <div key={i} className="flex justify-between items-center bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                      <span className="font-bold text-slate-500 min-w-[70px]">{item.category}:</span>
                      <span className="font-semibold text-slate-800">{item.name}</span>
                    </div>
                    <span className="font-bold text-slate-600">₹{item.price}</span>
                  </div>
                ))}
              </div>

              {/* Package Alternatives */}
              {bundle.alternatives && (
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 block">
                    Alternative Choices:
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-500">
                    {bundle.alternatives.seeds && bundle.alternatives.seeds.length > 0 && (
                      <div>
                        <strong className="text-slate-600">Seeds:</strong> {bundle.alternatives.seeds[0].name} (₹{bundle.alternatives.seeds[0].price})
                      </div>
                    )}
                    {bundle.alternatives.fertilizers && bundle.alternatives.fertilizers.length > 0 && (
                      <div>
                        <strong className="text-slate-600">Fertilizer:</strong> {bundle.alternatives.fertilizers[0].name} (₹{bundle.alternatives.fertilizers[0].price})
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 2. Top Products List */}
      {recommendations && recommendations.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-black uppercase tracking-wider text-slate-500 flex items-center gap-1.5 mb-1">
            <Sparkles size={14} className="text-amber-500" /> Top Ranked Products
          </h4>
          
          <div className="space-y-2.5">
            {recommendations.map((prod) => (
              <div 
                key={prod.product_id}
                className="bg-white hover:bg-slate-50/50 border border-slate-150 rounded-xl p-3.5 flex items-center justify-between gap-4 shadow-sm hover:shadow transition-all duration-200"
              >
                {/* Left: Score Badge & Details */}
                <div className="flex-grow min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded border ${getScoreColorClass(prod.score)}`}>
                      {prod.score}% Match
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      {prod.category}
                    </span>
                  </div>
                  <h5 className="text-sm font-extrabold text-slate-800 mt-1.5 mb-0.5 truncate">
                    {prod.name}
                  </h5>
                  <p className="text-[11px] text-slate-500 m-0 truncate">
                    Brand: <span className="font-bold">{prod.brand}</span> | Price: <span className="font-bold text-slate-700">₹{prod.price}</span>
                  </p>
                  <p className="text-[10px] text-emerald-600 font-semibold m-0 mt-1 flex items-center gap-1">
                    <Check size={11} /> {prod.reason}
                  </p>
                </div>

                {/* Right: Price / Buy action */}
                <div className="shrink-0 flex flex-col items-end gap-1.5">
                  <a 
                    href={`/products/${prod.product_id}`}
                    className="p-2 bg-green-50 hover:bg-green-100 text-green-700 hover:text-green-800 rounded-xl border border-green-100 transition-colors flex items-center gap-1.5 text-xs font-bold"
                  >
                    View <ChevronRight size={13} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
