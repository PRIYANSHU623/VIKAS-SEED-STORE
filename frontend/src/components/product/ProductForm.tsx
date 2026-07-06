import { useState, useEffect } from "react";
import { type Product } from "../../types/product";
import { X, Sparkles, Loader2 } from "lucide-react";

interface ProductFormProps {
  initialData?: Product;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  title: string;
}

export default function ProductForm({ initialData, onSubmit, onCancel, title }: ProductFormProps) {
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [category, setCategory] = useState("seeds");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [description, setDescription] = useState("");
  const [kind, setKind] = useState("paddy");
  const [customKind, setCustomKind] = useState("");
  const [season, setSeason] = useState("kharif");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || "");
      setBrand(initialData.brand || "");
      setCategory(initialData.category || "seeds");
      setPrice(initialData.price?.toString() || "");
      setStock(initialData.stock?.toString() || "");
      setImageUrl(initialData.image_url || initialData.image || "");
      setDescription(initialData.description || "");

      // Load seed kind and season if category is seeds
      const catLower = (initialData.category || "").toLowerCase();
      if (catLower === "seeds" || catLower === "seed") {
        const k = initialData.kind || "";
        const predefinedKinds = ["paddy", "wheat", "maize", "mustard", "cotton", "vegetable"];
        if (predefinedKinds.includes(k.toLowerCase())) {
          setKind(k.toLowerCase());
          setCustomKind("");
        } else if (k) {
          setKind("other");
          setCustomKind(k);
        } else {
          setKind("paddy");
          setCustomKind("");
        }
        setSeason(initialData.season?.toLowerCase() || "kharif");
      }
    }
  }, [initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !category || price === "" || stock === "") {
      setError("Please fill in all required fields.");
      return;
    }

    const priceNum = parseFloat(price);
    const stockNum = parseInt(stock);

    if (isNaN(priceNum) || priceNum < 0) {
      setError("Price must be a positive number.");
      return;
    }

    if (isNaN(stockNum) || stockNum < 0) {
      setError("Stock must be a non-negative integer.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await onSubmit({
        name,
        brand: brand || null,
        category: category.toLowerCase(),
        description: description || null,
        price: priceNum,
        stock: stockNum,
        image_url: imageUrl || null,
        kind: category === "seeds" ? (kind === "other" ? customKind : kind) : null,
        season: category === "seeds" ? season : null,
      });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to save product. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 md:p-8 max-w-xl w-full border border-gray-100 shadow-2xl relative">
      <button
        onClick={onCancel}
        className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors p-1.5 hover:bg-gray-50 rounded-lg"
        type="button"
        disabled={loading}
      >
        <X size={20} />
      </button>

      <div className="mb-6 space-y-1">
        <h2 className="text-xl md:text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
          <Sparkles className="text-green-600" size={20} /> {title}
        </h2>
        <p className="text-xs md:text-sm text-gray-500">
          Enter agricultural product specifications to publish to catalogue.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl text-xs font-semibold">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 text-left">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Product Name */}
          <div className="col-span-1 md:col-span-2 space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Product Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. NPK 19-19-19 Fertilizer"
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
              disabled={loading}
            />
          </div>

          {/* Brand */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Brand / Manufacturer
            </label>
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="e.g. Mahadhan"
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
              disabled={loading}
            />
          </div>

          {/* Category */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Category *
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 transition-all"
              disabled={loading}
            >
              <option value="seeds">Seeds</option>
              <option value="fertilizers">Fertilizers</option>
              <option value="herbicides">Herbicides</option>
              <option value="pesticides">Pesticides</option>
            </select>
          </div>

          {/* Seed Specific Fields */}
          {category === "seeds" && (
            <>
              {/* Seed Kind */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Seed Kind *
                </label>
                <select
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 transition-all"
                  disabled={loading}
                >
                  <option value="paddy">Paddy (Rice)</option>
                  <option value="wheat">Wheat</option>
                  <option value="maize">Maize</option>
                  <option value="mustard">Mustard</option>
                  <option value="cotton">Cotton</option>
                  <option value="vegetable">Vegetable</option>
                  <option value="other">Other (Custom)</option>
                </select>
              </div>

              {kind === "other" && (
                <div className="space-y-1.5 col-span-1 md:col-span-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                    Specify Seed Kind *
                  </label>
                  <input
                    type="text"
                    required
                    value={customKind}
                    onChange={(e) => setCustomKind(e.target.value)}
                    placeholder="Enter custom seed type (e.g. Barley, Soybean)"
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
                    disabled={loading}
                  />
                </div>
              )}

              {/* Seed Season */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Sowing Season *
                </label>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 transition-all"
                  disabled={loading}
                >
                  <option value="kharif">Kharif (Monsoon)</option>
                  <option value="rabi">Rabi (Winter)</option>
                  <option value="zaid">Zaid (Summer)</option>
                  <option value="all-seasons">All Seasons</option>
                </select>
              </div>
            </>
          )}

          {/* Price */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Price (INR ₹) *
            </label>
            <input
              type="number"
              step="0.01"
              required
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="₹0.00"
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
              disabled={loading}
            />
          </div>

          {/* Stock */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Available Stock *
            </label>
            <input
              type="number"
              required
              min="0"
              value={stock}
              onChange={(e) => setStock(e.target.value)}
              placeholder="0 units"
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
              disabled={loading}
            />
          </div>

          {/* Image URL */}
          <div className="col-span-1 md:col-span-2 space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Product Image URL
            </label>
            <input
              type="url"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/image.jpg"
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all"
              disabled={loading}
            />
          </div>

          {/* Description */}
          <div className="col-span-1 md:col-span-2 space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
              Product Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Provide crop suitability guide, application dosage, chemical composition..."
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400 transition-all resize-none"
              disabled={loading}
            />
          </div>
        </div>

        <div className="flex gap-4 pt-4 border-t border-gray-50 mt-6">
          <button
            type="button"
            onClick={onCancel}
            className="flex-grow py-3 px-4 bg-gray-50 hover:bg-gray-100 text-gray-700 font-bold rounded-xl text-center text-sm transition-all"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex-grow py-3 px-4 bg-green-600 hover:bg-green-700 active:scale-95 text-white font-bold rounded-xl text-center text-sm transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={16} /> Saving...
              </>
            ) : (
              "Save Product"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
