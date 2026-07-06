import { useState, useEffect, useContext } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Star, ShieldCheck, ArrowLeft, ShoppingCart, Leaf } from "lucide-react";
import { MOCK_PRODUCTS } from "../utils/mockData";
import ProductCard from "../components/product/ProductCard";
import { getProductById, getProducts } from "../api/productApi";
import { type Product } from "../types/product";
import { AuthContext } from "../context/AuthContext";
import AddedToCartModal from "../components/common/AddedToCartModal";


export default function ProductDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const { user } = useContext(AuthContext) || { user: null };
  
  // States
  const [product, setProduct] = useState<Product | null>(null);
  const [selectedImage, setSelectedImage] = useState<string>("");
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [productsList, setProductsList] = useState<Product[]>([]);
  const [isAddedModalOpen, setIsAddedModalOpen] = useState(false);

  // Fetch product from backend or fallback to mock
  useEffect(() => {
    const fetchProduct = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const data = await getProductById(id);
        if (data) {
          const mapped: Product = {
            ...data,
            id: data.id.toString(),
            image: data.image || data.image_url || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600",
            rating: data.rating || 4.5,
            reviewsCount: data.reviewsCount || 12
          };
          setProduct(mapped);
        } else {
          const mock = MOCK_PRODUCTS.find((p) => p.id === id);
          setProduct(mock || null);
        }
      } catch (error) {
        console.error("Failed to fetch product by id:", error);
        const mock = MOCK_PRODUCTS.find((p) => p.id === id);
        setProduct(mock || null);
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [id]);

  // Fetch all products for related section
  useEffect(() => {
    const fetchAllProducts = async () => {
      try {
        const data = await getProducts();
        if (data && data.length > 0) {
          const mapped = data.map((p: any) => ({
            ...p,
            id: p.id.toString(),
            image: p.image || p.image_url || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600",
            rating: p.rating || 4.5,
            reviewsCount: p.reviewsCount || 12
          }));
          setProductsList(mapped);
        } else {
          setProductsList(MOCK_PRODUCTS);
        }
      } catch (e) {
        setProductsList(MOCK_PRODUCTS);
      }
    };
    fetchAllProducts();
  }, []);

  // Sync selected image when product changes
  useEffect(() => {
    if (product) {
      setSelectedImage(product.image || "");
      setQuantity(1);
      window.scrollTo(0, 0);
    }
  }, [product]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-24 space-y-4">
        <span className="text-6xl">🔍</span>
        <h2 className="text-2xl font-extrabold text-gray-900">Product Not Found</h2>
        <p className="text-gray-500 max-w-sm mx-auto">
          The product you are trying to view does not exist or may have been removed.
        </p>
        <Link 
          to="/products"
          className="inline-block px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-md transition-all text-sm"
        >
          Return to Store
        </Link>
      </div>
    );
  }

  // Related products (same category, excluding current product)
  const normalizeCategory = (cat?: string): string => {
    const c = (cat || "").toLowerCase().trim();
    if (c.includes("seed")) return "seeds";
    if (c.includes("fertiliz") || c.includes("manure")) return "fertilizers";
    if (c.includes("herbicid") || c.includes("weed")) return "herbicides";
    if (c.includes("pesticid") || c.includes("insecticid") || c.includes("fungicid")) return "pesticides";
    return c;
  };

  const relatedProducts = productsList
    .filter((p) => normalizeCategory(p.category) === normalizeCategory(product.category) && p.id !== product.id)
    .slice(0, 4);

  const handleQuantityChange = (val: number) => {
    if (val < 1) return;
    if (val > product.stock) return;
    setQuantity(val);
  };

  const handleAddToCart = () => {
    if (!product) return;
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    const existing = cart.find((item: any) => item.product.id === product.id);
    
    if (existing) {
      existing.quantity += quantity;
    } else {
      cart.push({ product, quantity });
    }
    
    localStorage.setItem("cart", JSON.stringify(cart));
    window.dispatchEvent(new Event("cart-updated"));
    setIsAddedModalOpen(true);
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Back Link */}
      <div className="flex">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-green-600 transition-colors"
        >
          <ArrowLeft size={16} /> Back to Products
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Left Side: Product Gallery */}
        <div className="space-y-4">
          <div className="bg-gray-50 border border-gray-100 rounded-3xl overflow-hidden aspect-[4/3] relative shadow-sm">
            <img
              src={selectedImage}
              alt={product.name}
              className="w-full h-full object-cover transition-all"
            />
          </div>
          {/* Thumbnails (Simulating Gallery) */}
          <div className="flex gap-4">
            {[product.image || "", "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&q=80&w=600"].map((img, i) => (
              <button
                key={i}
                onClick={() => setSelectedImage(img || "")}
                className={`w-20 h-16 rounded-xl overflow-hidden border-2 transition-all ${
                  selectedImage === img ? "border-green-600 shadow-md" : "border-gray-100 opacity-60 hover:opacity-100"
                }`}
              >
                <img src={img} alt="Thumbnail" className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
        </div>

        {/* Right Side: Product Information */}
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-green-600 bg-green-50 px-2.5 py-1 rounded-full border border-green-100 uppercase">
                {product.category}
              </span>
              {(product.category === "seeds" || product.category === "seed") && product.kind && (
                <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
                  Type: {product.kind}
                </span>
              )}
              {(product.category === "seeds" || product.category === "seed") && product.season && (
                <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100">
                  Season: {product.season === "all-seasons" ? "All Seasons" : product.season}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight my-0 py-0">
              {product.name}
            </h1>
            <div className="flex items-center gap-4 pt-1">
              <span className="text-sm font-semibold text-gray-400">Brand: <strong className="text-gray-700">{product.brand}</strong></span>
              <span className="w-1.5 h-1.5 rounded-full bg-gray-200"></span>
              <div className="flex items-center gap-1">
                <Star size={16} className="fill-amber-400 text-amber-400" />
                <span className="text-sm font-bold text-gray-700">{product.rating}</span>
                <span className="text-xs text-gray-400">({product.reviewsCount} reviews)</span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-gray-50 border border-gray-100 rounded-2xl flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 font-medium">Special Agronomist Price</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-black text-gray-900">₹{product.price}</span>
                {product.originalPrice && (
                  <span className="text-sm text-gray-400 line-through">₹{product.originalPrice}</span>
                )}
              </div>
            </div>
            <div>
              {product.stock === 0 ? (
                <span className="px-3 py-1.5 text-xs font-bold text-red-700 bg-red-50 border border-red-100 rounded-full">
                  Out of Stock
                </span>
              ) : product.stock <= 10 ? (
                <span className="px-3 py-1.5 text-xs font-bold text-amber-700 bg-amber-50 border border-amber-100 rounded-full">
                  Low Stock: Only {product.stock} left
                </span>
              ) : (
                <span className="px-3 py-1.5 text-xs font-bold text-green-700 bg-green-50 border border-green-100 rounded-full">
                  In Stock (Ready to Ship)
                </span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-extrabold text-sm text-gray-900 uppercase tracking-wider">Product Overview</h3>
            <p className="text-sm text-gray-500 leading-relaxed font-light">
              {product.description}
            </p>
          </div>

          {/* Quantity Selector and Add to Cart */}
          {product.stock > 0 && (
            <div className="flex items-center gap-4 pt-2">
              <div className="flex items-center bg-gray-50 border border-gray-200 rounded-xl overflow-hidden">
                <button
                  onClick={() => handleQuantityChange(quantity - 1)}
                  className="px-4 py-3 text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors font-bold"
                >
                  -
                </button>
                <span className="px-4 py-3 font-extrabold text-sm text-gray-900 w-12 text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => handleQuantityChange(quantity + 1)}
                  className="px-4 py-3 text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors font-bold"
                >
                  +
                </button>
              </div>

              <button
                onClick={handleAddToCart}
                className="flex-grow py-3 px-6 bg-green-600 hover:bg-green-700 active:scale-[0.98] text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow hover:shadow-lg transition-all"
              >
                <ShoppingCart size={18} /> Add to Shopping Cart
              </button>
            </div>
          )}

          {/* High Quality Flags */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <ShieldCheck className="text-green-600" size={16} />
              <span>100% Original Brand Guarantee</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Leaf className="text-green-600" size={16} />
              <span>Eco-friendly organic options</span>
            </div>
          </div>
        </div>
      </div>

      {/* Specifications */}
      {product.specifications && Object.keys(product.specifications).length > 0 && (
        <div className="bg-white border border-gray-100 rounded-3xl p-8 space-y-6 shadow-sm">
          <h3 className="font-extrabold text-lg text-gray-900 border-b border-gray-50 pb-4">
            Technical Specifications
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
            {Object.entries(product.specifications).map(([key, val]) => (
              <div key={key} className="flex justify-between py-2 border-b border-gray-50 text-sm">
                <span className="text-gray-400 font-medium">{key}</span>
                <span className="text-gray-800 font-semibold text-right">{val}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Products Shelf */}
      {relatedProducts.length > 0 && (
        <div className="space-y-6">
          <h3 className="font-extrabold text-xl text-gray-900">
            Related Agricultural Products
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {relatedProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      )}

      <AddedToCartModal
        isOpen={isAddedModalOpen}
        onClose={() => setIsAddedModalOpen(false)}
        productName={product ? product.name : ""}
        userRole={user?.role}
        hasUser={!!user}
      />
    </div>
  );
}
