import { useState, useContext, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Sprout, LogOut, User as UserIcon, Menu, X, Search, Shield, LayoutDashboard, ShoppingCart } from "lucide-react";

import { AuthContext } from "../../context/AuthContext";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, setUser } = useContext(AuthContext) || { user: null, setUser: () => {} };
  
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [cartCount, setCartCount] = useState(0);

  const updateCartCount = () => {
    try {
      const cart = JSON.parse(localStorage.getItem("cart") || "[]");
      const count = cart.reduce((acc: number, item: any) => acc + (item.quantity || 0), 0);
      setCartCount(count);
    } catch (e) {
      setCartCount(0);
    }
  };

  useEffect(() => {
    updateCartCount();
    window.addEventListener("cart-updated", updateCartCount);
    return () => {
      window.removeEventListener("cart-updated", updateCartCount);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    if (setUser) setUser(null);
    setMobileMenuOpen(false);
    navigate("/login");
  };

  // Close mobile menu on page change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery("");
      setSearchOpen(false);
    }
  };

  const navItems = [
    { name: "Home", path: "/" },
    { name: "Seeds", path: "/products?category=seeds" },
    { name: "Fertilizers", path: "/products?category=fertilizers" },
    { name: "Herbicides", path: "/products?category=herbicides" },
    { name: "Pesticides", path: "/products?category=pesticides" },
    { name: "AI Assistant", path: "/ai-assistant" },
    { name: "Contact", path: "/contact" },
  ];

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm backdrop-blur-md bg-white/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          {/* Logo / Brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="p-2 bg-green-50 rounded-xl group-hover:bg-green-100 transition-colors">
                <Sprout size={28} className="text-green-600 animate-pulse" />
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-xl tracking-tight text-gray-900 leading-none">
                  Vikas Beej Bhandar
                </span>
                <span className="text-xs text-green-600 font-semibold tracking-wider uppercase mt-0.5">
                  KrishiSathi
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`text-sm font-semibold transition-all duration-200 hover:text-green-600 relative py-1 ${
                  location.pathname + location.search === item.path ||
                  (location.pathname === "/products" && item.path.includes("category") && location.search.includes(item.path.split("=")[1]))
                    ? "text-green-600 after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-green-600"
                    : "text-gray-600"
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* Right Action Buttons */}
          <div className="hidden lg:flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              {searchOpen ? (
                <form onSubmit={handleSearchSubmit} className="flex items-center">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search seeds, fertilizer..."
                    className="w-48 px-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                    autoFocus
                  />
                  <button type="button" onClick={() => setSearchOpen(false)} className="ml-2 text-gray-400 hover:text-gray-600">
                    <X size={16} />
                  </button>
                </form>
              ) : (
                <button
                  onClick={() => setSearchOpen(true)}
                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-xl transition-all"
                  aria-label="Search"
                >
                  <Search size={20} />
                </button>
              )}
            </div>

            {/* Shopping Cart Icon */}
            <Link
              to={user ? (user.role === "admin" ? "/admin" : "/dashboard?tab=cart") : "/login?redirect=/dashboard?tab=cart"}
              className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-xl transition-all relative"
              aria-label="Shopping Cart"
            >
              <ShoppingCart size={20} />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-green-600 text-[10px] font-bold text-white ring-2 ring-white animate-in zoom-in duration-200">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* Auth / Cart Context */}
            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  to={user.role === "admin" ? "/admin" : "/dashboard"}
                  className="flex items-center gap-1.5 px-3 py-2 bg-green-50 text-green-700 hover:bg-green-100 rounded-xl text-sm font-semibold transition-all"
                >
                  {user.role === "admin" ? <Shield size={16} /> : <LayoutDashboard size={16} />}
                  <span>{user.name.split(" ")[0]}</span>
                </Link>

                <button
                  onClick={handleLogout}
                  className="p-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-xl transition-all flex items-center gap-1"
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-green-600 px-4 py-2 text-sm font-semibold transition-all"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-green-600 hover:bg-green-700 active:bg-green-800 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-sm hover:shadow transition-all"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-2 lg:hidden">
            {/* Mobile Shopping Cart */}
            <Link
              to={user ? (user.role === "admin" ? "/admin" : "/dashboard?tab=cart") : "/login?redirect=/dashboard?tab=cart"}
              className="p-2 text-gray-500 hover:text-green-600 rounded-lg relative"
              aria-label="Shopping Cart"
            >
              <ShoppingCart size={22} />
              {cartCount > 0 && (
                <span className="absolute top-0 right-0 flex h-4.5 w-4.5 items-center justify-center rounded-full bg-green-600 text-[9px] font-bold text-white ring-2 ring-white">
                  {cartCount}
                </span>
              )}
            </Link>

            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="p-2 text-gray-500 hover:text-green-600 rounded-lg"
            >
              <Search size={22} />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-gray-500 hover:text-green-600 rounded-lg focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={26} /> : <Menu size={26} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile search bar dropdown */}
      {searchOpen && (
        <div className="lg:hidden bg-gray-50 border-t border-gray-100 px-4 py-3">
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products, brands, and categories..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
            />
            <Search className="absolute left-3 top-3 text-gray-400" size={18} />
          </form>
        </div>
      )}

      {/* Mobile Menu Panel */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-t border-gray-100 transition-all animate-in fade-in slide-in-from-top duration-200">
          <div className="px-4 pt-2 pb-6 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`block px-3 py-2.5 rounded-lg text-base font-semibold hover:bg-green-50 hover:text-green-700 transition-colors ${
                  location.pathname + location.search === item.path ? "bg-green-50 text-green-700" : "text-gray-700"
                }`}
              >
                {item.name}
              </Link>
            ))}

            {/* Mobile Cart Link */}
            <Link
              to={user ? (user.role === "admin" ? "/admin" : "/dashboard?tab=cart") : "/login?redirect=/dashboard?tab=cart"}
              className={`block px-3 py-2.5 rounded-lg text-base font-semibold hover:bg-green-50 hover:text-green-700 transition-colors ${
                location.pathname === "/dashboard" && location.search === "?tab=cart" ? "bg-green-50 text-green-700" : "text-gray-700"
              }`}
            >
              <span className="flex items-center gap-2">
                <ShoppingCart size={18} />
                My Cart ({cartCount})
              </span>
            </Link>
            
            <div className="pt-4 border-t border-gray-100 space-y-2">
              {user ? (
                <>
                  <div className="px-3 py-2 text-sm text-gray-500 flex items-center gap-2">
                    <UserIcon size={16} />
                    <span>Logged in as <strong>{user.name}</strong> ({user.role})</span>
                  </div>
                  <Link
                    to={user.role === "admin" ? "/admin" : "/dashboard"}
                    className="flex w-full items-center justify-center gap-2 py-3 bg-green-50 text-green-700 hover:bg-green-100 font-bold rounded-xl text-center text-sm"
                  >
                    {user.role === "admin" ? <Shield size={18} /> : <LayoutDashboard size={18} />}
                    Go to Dashboard
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-red-50 text-red-600 hover:bg-red-100 font-bold rounded-xl text-center text-sm"
                  >
                    <LogOut size={18} />
                    Logout
                  </button>
                </>
              ) : (
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <Link
                    to="/login"
                    className="w-full py-3 border border-gray-200 text-gray-700 hover:bg-gray-50 font-bold rounded-xl text-center text-sm"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="w-full py-3 bg-green-600 text-white font-bold rounded-xl text-center text-sm hover:bg-green-700 shadow"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}