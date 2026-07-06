import { ShoppingCart } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface AddedToCartModalProps {
  isOpen: boolean;
  onClose: () => void;
  productName: string;
  userRole?: string;
  hasUser: boolean;
}

export default function AddedToCartModal({
  isOpen,
  onClose,
  productName,
  userRole,
  hasUser,
}: AddedToCartModalProps) {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleGoToCart = () => {
    onClose();
    if (!hasUser) {
      navigate("/login?redirect=/dashboard?tab=cart");
    } else if (userRole === "admin") {
      navigate("/admin");
    } else {
      navigate("/dashboard?tab=cart");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative bg-white rounded-3xl p-6 max-w-sm w-full border border-gray-100 shadow-2xl text-center transform scale-100 transition-all duration-300 z-10 flex flex-col gap-4">
        <div className="mx-auto flex items-center justify-center h-14 w-14 rounded-2xl bg-green-50 text-green-600 shadow-inner">
          <ShoppingCart size={28} className="animate-bounce" />
        </div>
        
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-gray-900 my-0 py-0">Added to Cart</h3>
          <p className="text-sm text-gray-500">
            <strong>{productName}</strong> has been added to your cart.
          </p>
        </div>
        
        <div className="flex flex-col gap-2 pt-2">
          <button
            onClick={handleGoToCart}
            className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl text-sm transition-all shadow-sm hover:shadow"
          >
            Go to Cart
          </button>
          <button
            onClick={onClose}
            className="w-full py-3 bg-gray-50 hover:bg-gray-100 border border-gray-100 text-gray-700 font-semibold rounded-xl text-sm transition-all"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
}
