import { Link } from "react-router-dom";
import { ShoppingCart, Eye } from "lucide-react";
import { type Product } from "../../types/product";

interface Props {
  product: Product;
  onAddToCart?: (product: Product, e: any) => void;
}

export default function ProductCard({ product, onAddToCart }: Props) {
  const isOutOfStock = product.stock === 0;
  const isLowStock = product.stock > 0 && product.stock <= 10;
  
  // Handle fallback for image properties
  const imageUrl = (product as any).image || (product as any).image_url || "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&q=80&w=600";

  return (
    <div className="flex flex-col bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 h-full group">
      
      {/* Product Image Container */}
      <div className="relative pt-[70%] bg-gray-50 overflow-hidden w-full">
        <img 
          src={imageUrl} 
          alt={product.name}
          className="absolute top-0 left-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        
        {/* Category Badge */}
        {product.category && (
          <span className="absolute top-3 left-3 bg-green-50 text-green-700 text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm border border-green-100 uppercase tracking-wider">
            {product.category}
          </span>
        )}
      </div>

      {/* Product Content Details */}
      <div className="flex flex-col flex-grow p-5">
        {/* Brand name */}
        <span className="text-xs uppercase tracking-wider font-semibold text-gray-400 mb-1">
          {product.brand || "Generic"}
        </span>

        {/* Title */}
        <h3 className="font-bold text-gray-900 text-base line-clamp-1 group-hover:text-green-600 transition-colors duration-200 mb-2">
          {product.name}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-500 line-clamp-2 flex-grow mb-4">
          {product.description || "No description provided for this agricultural item."}
        </p>

        {/* Pricing & Stock Details */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-50">
          <div className="flex flex-col">
            <span className="text-xs text-gray-400 font-medium">Price</span>
            <span className="text-lg font-extrabold text-gray-900">
              ₹{Number(product.price).toLocaleString('en-IN')}
            </span>
          </div>

          {/* Stock Status Badge */}
          <div>
            {isOutOfStock ? (
              <span className="inline-flex items-center text-xs font-bold text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">
                Out of Stock
              </span>
            ) : isLowStock ? (
              <span className="inline-flex items-center text-xs font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100 animate-pulse">
                Only {product.stock} left
              </span>
            ) : (
              <span className="inline-flex items-center text-xs font-medium text-green-700 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">
                In Stock
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 mt-5 pt-2">
          <Link 
            to={`/products/${product.id}`}
            className="py-2.5 px-3 rounded-xl font-bold text-xs bg-gray-50 hover:bg-gray-100 text-gray-700 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 border border-gray-100"
          >
            <Eye size={14} />
            Details
          </Link>

          <button 
            onClick={(e) => onAddToCart && onAddToCart(product, e)}
            disabled={isOutOfStock}
            className={`py-2.5 px-3 rounded-xl font-bold text-xs active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 ${
              isOutOfStock 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200' 
                : 'bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow'
            }`}
          >
            <ShoppingCart size={14} />
            Add To Cart
          </button>
        </div>
      </div>
    </div>
  );
}