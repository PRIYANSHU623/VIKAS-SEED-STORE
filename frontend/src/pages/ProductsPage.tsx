import { useState, useEffect, useContext } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, SlidersHorizontal, ShoppingCart, Eye, X, Star } from "lucide-react";
import { MOCK_PRODUCTS } from "../utils/mockData";
import { type Product } from "../types/product";
import ProductCard from "../components/product/ProductCard";
import { getProducts } from "../api/productApi";
import { AuthContext } from "../context/AuthContext";
import AddedToCartModal from "../components/common/AddedToCartModal";


export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useContext(AuthContext) || { user: null };
  
  // States
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [brand, setBrand] = useState("all");
  const [maxPrice, setMaxPrice] = useState(10000);
  const [sliderMax, setSliderMax] = useState(10000);
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);
  const [productsList, setProductsList] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [addedProduct, setAddedProduct] = useState<Product | null>(null);
  const [isAddedModalOpen, setIsAddedModalOpen] = useState(false);
  const [seedKind, setSeedKind] = useState("all");
  const [seedSeason, setSeedSeason] = useState("all");
  
  // Fetch products from backend or fallback to mock
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await getProducts();
        if (data && data.length > 0) {
          // Map backend product image_url to standard image field if necessary
          const mapped = data.map((p: any) => ({
            ...p,
            id: p.id.toString(), // ensure string id for consistency with frontend types
            image: p.image || p.image_url || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600",
            rating: p.rating || 4.5,
            reviewsCount: p.reviewsCount || 12
          }));
          setProductsList(mapped);

          // Dynamically compute max price
          const prices = mapped.map((p: any) => p.price);
          const maxP = prices.length > 0 ? Math.max(...prices) : 1000;
          const ceilingPrice = Math.ceil(maxP / 100) * 100;
          setSliderMax(ceilingPrice);
          setMaxPrice(ceilingPrice);
        } else {
          setProductsList(MOCK_PRODUCTS);
          const prices = MOCK_PRODUCTS.map((p: any) => p.price);
          const maxP = prices.length > 0 ? Math.max(...prices) : 1000;
          setSliderMax(maxP);
          setMaxPrice(maxP);
        }
      } catch (error) {
        console.error("Failed to fetch products from backend:", error);
        setProductsList(MOCK_PRODUCTS);
        const prices = MOCK_PRODUCTS.map((p: any) => p.price);
        const maxP = prices.length > 0 ? Math.max(...prices) : 1000;
        setSliderMax(maxP);
        setMaxPrice(maxP);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  // Set parameters from URL on mount/update
  useEffect(() => {
    const urlCategory = searchParams.get("category");
    const urlSearch = searchParams.get("search");
    
    if (urlCategory) {
      setCategory(urlCategory);
    } else {
      setCategory("all");
    }

    if (urlSearch) {
      setSearch(urlSearch);
    }
  }, [searchParams]);

  // Extract unique brands for filter
  const brands = Array.from(new Set(productsList.map(p => p.brand).filter(Boolean)));

  // Extract unique seed kinds and sowing seasons dynamically (combining defaults and custom values from DB)
  const normalizeCategoryForList = (cat: string): string => {
    const c = (cat || "").toLowerCase().trim();
    if (c.includes("seed")) return "seeds";
    if (c.includes("fertiliz") || c.includes("manure")) return "fertilizers";
    if (c.includes("herbicid") || c.includes("weed")) return "herbicides";
    if (c.includes("pesticid") || c.includes("insecticid") || c.includes("fungicid")) return "pesticides";
    return c;
  };

  const defaultKinds = ["paddy", "wheat", "maize", "mustard", "cotton", "vegetable"];
  const seedKinds = Array.from(
    new Set([
      ...defaultKinds,
      ...productsList
        .filter(p => p.category && normalizeCategoryForList(p.category) === "seeds")
        .map(p => (p.kind || "").toLowerCase().trim())
        .filter(Boolean)
    ])
  );

  const defaultSeasons = ["kharif", "rabi", "zaid", "all-seasons"];
  const seedSeasons = Array.from(
    new Set([
      ...defaultSeasons,
      ...productsList
        .filter(p => p.category && normalizeCategoryForList(p.category) === "seeds")
        .map(p => (p.season || "").toLowerCase().trim())
        .filter(Boolean)
    ])
  );

  // Filter logic
  const filteredProducts = productsList.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(search.toLowerCase()) || 
                          product.brand.toLowerCase().includes(search.toLowerCase()) ||
                          product.description.toLowerCase().includes(search.toLowerCase());
    
    // Normalize categories to handle singular/plural and casing issues (e.g., "Seed" vs "seeds")
    const normalizeCategory = (cat: string): string => {
      const c = (cat || "").toLowerCase().trim();
      if (c.includes("seed")) return "seeds";
      if (c.includes("fertiliz") || c.includes("manure")) return "fertilizers";
      if (c.includes("herbicid") || c.includes("weed")) return "herbicides";
      if (c.includes("pesticid") || c.includes("insecticid") || c.includes("fungicid")) return "pesticides";
      return c;
    };

    const matchesCategory = category === "all" || (product.category && normalizeCategory(product.category) === normalizeCategory(category));
    const matchesBrand = brand === "all" || product.brand === brand;
    const matchesPrice = product.price <= maxPrice;

    // Seed-specific filters (only apply if active category is seeds)
    const matchesSeedKind = category !== "seeds" || seedKind === "all" || 
      (product.kind && product.kind.toLowerCase().trim() === seedKind.toLowerCase().trim());
      
    const matchesSeedSeason = category !== "seeds" || seedSeason === "all" || 
      (product.season && product.season.toLowerCase().trim() === seedSeason.toLowerCase().trim());

    return matchesSearch && matchesCategory && matchesBrand && matchesPrice && matchesSeedKind && matchesSeedSeason;
  });

  const handleTabChange = (newCategory: string) => {
    setCategory(newCategory);
    setSeedKind("all");
    setSeedSeason("all");
    if (newCategory === "all") {
      searchParams.delete("category");
    } else {
      searchParams.set("category", newCategory);
    }
    setSearchParams(searchParams);
  };

  const handleAddToCart = (product: Product, e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    const existing = cart.find((item: any) => item.product.id === product.id);
    
    if (existing) {
      existing.quantity += 1;
    } else {
      cart.push({ product, quantity: 1 });
    }
    
    localStorage.setItem("cart", JSON.stringify(cart));
    window.dispatchEvent(new Event("cart-updated"));
    setAddedProduct(product);
    setIsAddedModalOpen(true);
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="bg-green-50/50 border border-green-100 rounded-3xl p-8 text-center space-y-2">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight my-0 py-0">
          Agricultural Product Store
        </h1>
        <p className="text-black max-w-3xl mx-auto">
          Explore certified inputs, hybrid seeds, powerful crop protection formulas, and organic composts.
        </p>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-gray-100 overflow-x-auto gap-2 scrollbar-none py-1">
        {["all", "seeds", "fertilizers", "herbicides", "pesticides"].map((tab) => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab)}
            className={`px-6 py-3 font-bold text-sm rounded-xl capitalize transition-all shrink-0 ${
              category === tab
                ? "bg-green-600 text-white shadow"
                : "text-gray-500 hover:text-green-600 hover:bg-gray-50"
            }`}
          >
            {tab === "all" ? "All Products" : tab}
          </button>
        ))}
      </div>

      {/* Filter and Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Filters Sidebar */}
        <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm h-fit space-y-6 lg:sticky lg:top-24">
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <span className="font-extrabold text-gray-900 flex items-center gap-2">
              <SlidersHorizontal size={18} className="text-green-600" /> Filters
            </span>
            {(search || brand !== "all" || category !== "all" || maxPrice < 1000 || seedKind !== "all" || seedSeason !== "all") && (
              <button 
                onClick={() => {
                  setSearch("");
                  setCategory("all");
                  setBrand("all");
                  setMaxPrice(1000);
                  setSeedKind("all");
                  setSeedSeason("all");
                  setSearchParams({});
                }}
                className="text-xs text-red-500 hover:underline font-semibold"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Search Input */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">Search Products</label>
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Product name, brand..."
                className="w-full pl-9 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900"
              />
              <Search className="absolute left-3 top-3 text-gray-400" size={16} />
            </div>
          </div>

          {/* Brand Filter */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">Brand</label>
            <select
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900"
            >
              <option value="all">All Brands</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          {/* Seed Kind Filter */}
          {category === "seeds" && seedKinds.length > 0 && (
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">Seed Kind</label>
              <select
                value={seedKind}
                onChange={(e) => setSeedKind(e.target.value)}
                className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 capitalize"
              >
                <option value="all">All Kinds</option>
                {seedKinds.map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
            </div>
          )}

          {/* Seed Season Filter */}
          {category === "seeds" && seedSeasons.length > 0 && (
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">Sowing Season</label>
              <select
                value={seedSeason}
                onChange={(e) => setSeedSeason(e.target.value)}
                className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm text-gray-900 capitalize"
              >
                <option value="all">All Seasons</option>
                {seedSeasons.map((s) => (
                  <option key={s} value={s}>{s === "all-seasons" ? "All Seasons" : s}</option>
                ))}
              </select>
            </div>
          )}

          {/* Price Range Filter */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-bold uppercase tracking-wider text-gray-500">
              <span>Max Price</span>
              <span className="text-green-600 font-extrabold text-sm">₹{maxPrice}</span>
            </div>
            <input
              type="range"
              min="100"
              max={sliderMax}
              step={sliderMax > 10000 ? 500 : 50}
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="w-full accent-green-600 cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>₹100</span>
              <span>₹{sliderMax}</span>
            </div>
          </div>
        </div>

        {/* Product Grid Area */}
        <div className="lg:col-span-3 space-y-6">
          {loading ? (
            <div className="flex justify-center items-center py-24">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center text-sm text-gray-200 px-2">
                <span>Showing <strong className="text-gray-100">{filteredProducts.length}</strong> products</span>
              </div>

              {filteredProducts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredProducts.map((product) => (
                    <div key={product.id} className="relative group">
                      <ProductCard product={product} onAddToCart={handleAddToCart} />
                      
                      {/* Quick View Floating Button over Card */}
                      <button
                        onClick={() => setQuickViewProduct(product)}
                        className="absolute top-3 right-3 p-2.5 bg-white/90 hover:bg-white text-gray-700 hover:text-green-600 rounded-full shadow-md border border-gray-100 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                        title="Quick View"
                      >
                        <Eye size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white border border-gray-100 rounded-3xl p-16 text-center space-y-4">
                  <span className="text-5xl">🌾</span>
                  <h3 className="font-extrabold text-lg text-gray-900">No Products Found</h3>
                  <p className="text-gray-500 max-w-sm mx-auto">
                    We couldn't find any products matching your search criteria. Try modifying your filters or search keywords.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

      </div>

      {/* Quick View Modal */}
      {quickViewProduct && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 max-w-2xl w-full overflow-hidden relative animate-in zoom-in-95 duration-200">
            <button
              onClick={() => setQuickViewProduct(null)}
              className="absolute top-4 right-4 p-2 bg-gray-50 hover:bg-gray-100 text-gray-500 hover:text-gray-700 rounded-full transition-all border border-gray-200/50"
            >
              <X size={18} />
            </button>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
              {/* Product Image */}
              <div className="bg-gray-50 rounded-2xl overflow-hidden aspect-square relative">
                <img
                  src={quickViewProduct.image}
                  alt={quickViewProduct.name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Product Info */}
              <div className="flex flex-col space-y-4">
                <div>
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-green-600 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">
                      {quickViewProduct.category}
                    </span>
                    {(quickViewProduct.category === "seeds" || quickViewProduct.category === "seed") && quickViewProduct.kind && (
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
                        Type: {quickViewProduct.kind}
                      </span>
                    )}
                    {(quickViewProduct.category === "seeds" || quickViewProduct.category === "seed") && quickViewProduct.season && (
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100">
                        Season: {quickViewProduct.season === "all-seasons" ? "All Seasons" : quickViewProduct.season}
                      </span>
                    )}
                  </div>
                  <h2 className="text-xl font-extrabold text-gray-900 mt-2">{quickViewProduct.name}</h2>
                  <p className="text-xs text-gray-400 font-semibold mt-1">Brand: {quickViewProduct.brand}</p>
                </div>

                <div className="flex items-center gap-1">
                  <Star size={16} className="fill-amber-400 text-amber-400" />
                  <span className="text-sm font-bold text-gray-700">{quickViewProduct.rating}</span>
                  <span className="text-xs text-gray-400">({quickViewProduct.reviewsCount} reviews)</span>
                </div>

                <p className="text-sm text-gray-600 leading-relaxed font-light line-clamp-4">
                  {quickViewProduct.description}
                </p>

                <div className="flex items-center justify-between py-2 border-y border-gray-50">
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-400">Offer Price</span>
                    <span className="text-2xl font-extrabold text-gray-900">₹{quickViewProduct.price}</span>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-md ${
                    quickViewProduct.stock > 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                  }`}>
                    {quickViewProduct.stock > 0 ? `In Stock (${quickViewProduct.stock})` : 'Out of Stock'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <button
                    onClick={() => {
                      handleAddToCart(quickViewProduct);
                      setQuickViewProduct(null);
                    }}
                    disabled={quickViewProduct.stock === 0}
                    className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow active:scale-95 transition-all text-xs disabled:opacity-50"
                  >
                    <ShoppingCart size={16} /> Add to Cart
                  </button>
                  <button
                    onClick={() => {
                      setQuickViewProduct(null);
                      window.location.href = `/products/${quickViewProduct.id}`;
                    }}
                    className="w-full py-3 bg-gray-50 hover:bg-gray-100 border border-gray-100 text-gray-700 font-bold rounded-xl text-xs active:scale-95 transition-all"
                  >
                    Full Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <AddedToCartModal
        isOpen={isAddedModalOpen}
        onClose={() => setIsAddedModalOpen(false)}
        productName={addedProduct ? addedProduct.name : ""}
        userRole={user?.role}
        hasUser={!!user}
      />
    </div>
  );
}
