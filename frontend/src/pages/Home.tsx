import { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";
import { Sprout, Users, CheckCircle, Award, Shield, Truck, Sparkles, ArrowRight, ChevronLeft, ChevronRight } from "lucide-react";
import { MOCK_PRODUCTS } from "../utils/mockData";
import { type Product } from "../types/product";
import ProductCard from "../components/product/ProductCard";
import { getProducts } from "../api/productApi";
import { getHomepageReviews, type Review } from "../api/reviewApi";
import { AuthContext } from "../context/AuthContext";
import AddedToCartModal from "../components/common/AddedToCartModal";


export default function Home() {
  const { user } = useContext(AuthContext) || { user: null };
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [testimonials, setTestimonials] = useState<Review[]>([]);
  const [productsList, setProductsList] = useState<Product[]>([]);
  const [addedProduct, setAddedProduct] = useState<Product | null>(null);
  const [isAddedModalOpen, setIsAddedModalOpen] = useState(false);

  useEffect(() => {
    const fetchProducts = async () => {
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
      } catch (error) {
        console.error("Failed to load products for Home:", error);
        setProductsList(MOCK_PRODUCTS);
      }
    };
    fetchProducts();
  }, []);

  useEffect(() => {
    const fetchTestimonials = async () => {
      try {
        const data = await getHomepageReviews();
        setTestimonials(data);
      } catch (error) {
        console.error("Failed to load testimonials:", error);
      }
    };
    fetchTestimonials();
  }, []);

  const stats = [
    { label: "Products Available", value: "150+", icon: Sprout },
    { label: "Farmers Served", value: "10,000+", icon: Users },
    { label: "Orders Completed", value: "25,000+", icon: CheckCircle },
    { label: "Years of Trust", value: "20+", icon: Award },
  ];

  const categories = [
    {
      name: "Seeds",
      description: "High-yield hybrid and organic crop seeds for a rich harvest.",
      icon: "🌱",
      image: "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&q=80&w=400",
      path: "/products?category=seeds"
    },
    {
      name: "Fertilizers",
      description: "NPK, urea, and organic manures to boost soil productivity.",
      icon: "🧪",
      image: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&q=80&w=400",
      path: "/products?category=fertilizers"
    },
    {
      name: "Herbicides",
      description: "Control weeds effectively and protect crop yields.",
      icon: "🌾",
      image: "https://images.unsplash.com/photo-1592417817098-8f3d6eb19675?auto=format&fit=crop&q=80&w=400",
      path: "/products?category=herbicides"
    },
    {
      name: "Pesticides",
      description: "Protect crops from diseases and harmful pest infestations.",
      icon: "🐛",
      image: "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=400",
      path: "/products?category=pesticides"
    }
  ];

  const features = [
    {
      title: "High Quality Products",
      description: "All products undergo rigorous quality checks for premium germination and effectiveness.",
      icon: CheckCircle
    },
    {
      title: "Trusted Brands",
      description: "Authorized dealer of top brands like Syngenta, Mahadhan, BioGrow, and Vikas Seeds.",
      icon: Shield
    },
    {
      title: "Fast Delivery",
      description: "Prompt local logistics ensuring products reach your farm when needed most.",
      icon: Truck
    },
    {
      title: "AI Farming Assistance",
      description: "Identify crop diseases and get product recommendations instantly with our bot.",
      icon: Sparkles
    }
  ];

  // Show first 4 products as featured
  const featuredProducts = productsList.slice(0, 4);

  const nextTestimonial = () => {
    if (testimonials.length === 0) return;
    setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    if (testimonials.length === 0) return;
    setActiveTestimonial((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  const handleAddToCart = (product: Product, e: React.MouseEvent) => {
    e.preventDefault();
    // Fetch current cart
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
    <div className="space-y-20 pb-16">
      
      {/* 1. Hero Section */}
      <section className="relative rounded-3xl overflow-hidden shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-r from-green-950/90 to-green-900/60 z-10"></div>
        <img 
          src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&q=80&w=1600" 
          alt="Green crop field"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="relative z-20 max-w-4xl mx-auto px-6 py-24 sm:py-32 text-center text-white space-y-8">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-green-500/20 border border-green-500/30 text-green-300 text-sm font-semibold tracking-wide uppercase">
            <Sparkles size={14} /> Modern Farming Partner
          </span>
          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
            Empowering Farmers with Quality Agricultural Products
          </h1>
          <p className="text-lg sm:text-xl text-green-100 max-w-2xl mx-auto font-light leading-relaxed">
            Premium Seeds, Fertilizers, Herbicides and Pesticides delivered with absolute trust and expertise.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link 
              to="/products"
              className="w-full sm:w-auto px-8 py-4 bg-green-600 hover:bg-green-500 active:scale-[0.98] text-white font-extrabold rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2 text-base"
            >
              Browse Products <ArrowRight size={18} />
            </Link>
            <Link 
              to="/ai-assistant"
              className="w-full sm:w-auto px-8 py-4 bg-white/10 hover:bg-white/15 border border-white/20 active:scale-[0.98] text-white font-bold rounded-2xl transition-all flex items-center justify-center gap-2 text-base backdrop-blur-sm"
            >
              <Sparkles size={18} className="text-green-300" /> Ask AI Assistant
            </Link>
          </div>
        </div>
      </section>

      {/* 2. Statistics Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div key={i} className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col items-center text-center">
                <div className="p-3 bg-green-50 rounded-xl text-green-600 mb-4">
                  <Icon size={24} />
                </div>
                <span className="text-3xl font-extrabold text-gray-900">{stat.value}</span>
                <span className="text-sm font-semibold text-gray-500 mt-1">{stat.label}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Category Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
            Browse by Product Category
          </h2>
          <p className="text-gray-500">
            Find premium grade supplies curated specifically for different stages of the cultivation cycle.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {categories.map((cat, i) => (
            <div key={i} className="flex flex-col bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group">
              <div className="relative pt-[55%] bg-gray-100 overflow-hidden w-full">
                <img 
                  src={cat.image} 
                  alt={cat.name}
                  className="absolute top-0 left-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <span className="absolute bottom-3 left-3 text-3xl p-1.5 bg-white/95 rounded-xl shadow-md backdrop-blur-sm">
                  {cat.icon}
                </span>
              </div>
              <div className="p-6 flex flex-col flex-grow space-y-4">
                <h3 className="font-extrabold text-lg text-gray-900">{cat.name}</h3>
                <p className="text-sm text-gray-500 flex-grow leading-relaxed">{cat.description}</p>
                <Link 
                  to={cat.path}
                  className="w-full py-3 bg-green-50 hover:bg-green-100 text-green-700 font-bold rounded-xl text-center text-sm transition-all flex items-center justify-center gap-1 group-hover:bg-green-600 group-hover:text-white"
                >
                  View Products <ArrowRight size={16} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Featured Products Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-3">
            <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
              Featured High-Quality Products
            </h2>
            <p className="text-gray-500">
              Handpicked top-selling products highly recommended by expert agronomists.
            </p>
          </div>
          <Link 
            to="/products" 
            className="text-green-600 hover:text-green-700 font-bold text-sm flex items-center gap-1 shrink-0 self-start sm:self-auto underline decoration-2 underline-offset-4"
          >
            See All Products <ArrowRight size={16} />
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {featuredProducts.map((product) => (
            <ProductCard 
              key={product.id} 
              product={product} 
              onAddToCart={handleAddToCart}
            />
          ))}
        </div>
      </section>

      {/* 5. Why Choose Us Section */}
      <section className="bg-green-50/50 py-16 rounded-3xl max-w-7xl mx-auto px-6 border border-green-100/50 space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Why Indian Farmers Trust Us
          </h2>
          <p className="text-gray-500">
            For over two decades, we have partnered with farmers to deliver verified seeds, fertilizers, and technology.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feat, i) => {
            const Icon = feat.icon;
            return (
              <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col space-y-3">
                <div className="p-3 bg-green-500 text-white rounded-xl self-start">
                  <Icon size={20} />
                </div>
                <h3 className="font-extrabold text-base text-gray-900">{feat.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{feat.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 6. Testimonials Section (Carousel) */}
      <section className="max-w-4xl mx-auto px-6 space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Success Stories from Our Farmers
          </h2>
          <p className="text-gray-500">
            Hear directly from the growers who have enhanced their crop yield using our products.
          </p>
        </div>
        
        {testimonials.length > 0 && testimonials[activeTestimonial] ? (
          <div className="relative bg-white border border-gray-100 rounded-3xl shadow-xl p-8 sm:p-12">
            {/* Decorative quote icon */}
            <span className="absolute top-6 left-8 text-7xl text-green-100 select-none font-serif">“</span>

            <div className="space-y-6 relative z-10">
              <p className="text-lg sm:text-xl text-gray-700 italic leading-relaxed text-center">
                "{testimonials[activeTestimonial].comment}"
              </p>
              <div className="flex items-center justify-center gap-4 pt-4">
                <img 
                  src={testimonials[activeTestimonial].user_image || "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150"} 
                  alt={testimonials[activeTestimonial].user_name}
                  className="w-16 h-16 rounded-full object-cover border-2 border-green-500 shadow-md"
                />
                <div className="text-left">
                  <h4 className="font-bold text-gray-900">{testimonials[activeTestimonial].user_name}</h4>
                  <p className="text-xs text-green-600 font-semibold">{testimonials[activeTestimonial].user_role || "Farmer"}</p>
                  <p className="text-xs text-gray-400">{testimonials[activeTestimonial].user_location || "India"}</p>
                </div>
              </div>
            </div>

            {/* Carousel Buttons */}
            <div className="flex items-center justify-center gap-4 mt-8 pt-4">
              <button 
                onClick={prevTestimonial}
                className="p-2.5 bg-gray-50 hover:bg-green-50 text-gray-600 hover:text-green-700 rounded-xl border border-gray-100 hover:border-green-100 active:scale-95 transition-all"
                aria-label="Previous review"
              >
                <ChevronLeft size={18} />
              </button>
              <div className="flex gap-1.5">
                {testimonials.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveTestimonial(i)}
                    className={`w-2.5 h-2.5 rounded-full transition-all ${
                      activeTestimonial === i ? "bg-green-600 w-6" : "bg-gray-200"
                    }`}
                    aria-label={`Go to slide ${i + 1}`}
                  />
                ))}
              </div>
              <button 
                onClick={nextTestimonial}
                className="p-2.5 bg-gray-50 hover:bg-green-50 text-gray-600 hover:text-green-700 rounded-xl border border-gray-100 hover:border-green-100 active:scale-95 transition-all"
                aria-label="Next review"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          </div>
        )}
      </section>

      {/* 7. Call To Action Section */}
      <section className="bg-gradient-to-br from-green-700 to-green-900 rounded-3xl max-w-7xl mx-auto px-8 py-16 text-center text-white space-y-6 shadow-xl relative overflow-hidden">
        {/* Background blobs */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-green-600/20 rounded-full blur-3xl -mr-20 -mt-20"></div>
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-green-500/10 rounded-full blur-3xl -ml-20 -mb-20"></div>

        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight relative z-10">
          Ready to Increase Your Harvest Yield?
        </h2>
        <p className="text-green-100 max-w-2xl mx-auto relative z-10 leading-relaxed font-light">
          Get in touch with our agronomists, search our seed catalogue, or leverage our AI Crop Doctor for quick diagnostic answers on the go.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 relative z-10">
          <Link 
            to="/products"
            className="w-full sm:w-auto px-8 py-3.5 bg-white text-green-800 font-extrabold rounded-xl shadow-md hover:bg-green-50 transition-all text-sm uppercase tracking-wider"
          >
            Start Shopping
          </Link>
          <Link 
            to="/ai-assistant"
            className="w-full sm:w-auto px-8 py-3.5 border border-white/30 hover:border-white text-white font-bold rounded-xl transition-all text-sm flex items-center justify-center gap-2 bg-white/5 backdrop-blur-sm"
          >
            <Sparkles size={16} /> Consult AI Doctor
          </Link>
        </div>
      </section>

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
