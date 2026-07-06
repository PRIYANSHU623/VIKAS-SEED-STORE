import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { LayoutDashboard, ShoppingBag, ShoppingCart, MessageSquare, LogOut, CheckCircle2, Clock, Trash2, ArrowRight } from "lucide-react";
import { MOCK_ORDERS, MOCK_PRODUCTS } from "../../utils/mockData";
import { getProducts } from "../../api/productApi";
import { getOrders, createOrder, updateOrder } from "../../api/orderApi";


export default function FarmerDashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [cartItems, setCartItems] = useState<any[]>([]);
  const [user, setUser] = useState<any>(null);
  const [ordersList, setOrdersList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Sync tab with query parameters
  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  // Load user and cart from localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (!savedUser) {
      navigate("/login");
      return;
    }
    setUser(JSON.parse(savedUser));
    
    // Load cart
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    setCartItems(cart);
  }, [navigate]);

  // Load products and orders from backend
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch products
      let dbProducts = [];
      try {
        dbProducts = await getProducts();
        if (!dbProducts || dbProducts.length === 0) {
          dbProducts = MOCK_PRODUCTS;
        }
      } catch (err) {
        console.error("Error loading products, using mock:", err);
        dbProducts = MOCK_PRODUCTS;
      }

      // 2. Fetch orders
      let dbOrders = [];
      try {
        dbOrders = await getOrders();
      } catch (err) {
        console.error("Error loading orders, falling back to local storage:", err);
        const local = localStorage.getItem("orders");
        dbOrders = local ? JSON.parse(local) : MOCK_ORDERS;
      }

      // Map orders to include product names/images from product catalog
      const mapped = dbOrders.map((o: any) => {
        // If order already has items array (like mock orders), use it
        if (o.items && Array.isArray(o.items)) {
          return o;
        }
        
        // Find product in catalog
        const product = o.product || dbProducts.find((p: any) => p.id.toString() === o.product_id.toString());
        return {
          id: `ORD-${o.id}`,
          realId: o.id,
          date: new Date(o.created_at).toLocaleDateString(),
          total: o.total_price,
          status: o.status.charAt(0).toUpperCase() + o.status.slice(1),
          items: [
            {
              productId: o.product_id.toString(),
              productName: product ? product.name : `Product #${o.product_id}`,
              quantity: o.quantity,
              price: product ? product.price : (o.total_price / o.quantity),
              image: product ? (product.image || product.image_url) : "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600"
            }
          ]
        };
      });

      setOrdersList(mapped);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const handleUpdateCartQty = (productId: string, newQty: number) => {
    if (newQty < 1) return;
    const updated = cartItems.map((item) => {
      if (item.product.id === productId) {
        return { ...item, quantity: newQty };
      }
      return item;
    });
    setCartItems(updated);
    localStorage.setItem("cart", JSON.stringify(updated));
    window.dispatchEvent(new Event("cart-updated"));
  };

  const handleRemoveFromCart = (productId: string) => {
    const updated = cartItems.filter((item) => item.product.id !== productId);
    setCartItems(updated);
    localStorage.setItem("cart", JSON.stringify(updated));
    window.dispatchEvent(new Event("cart-updated"));
  };

  const handleCheckout = async () => {
    if (cartItems.length === 0) return;
    
    setLoading(true);
    try {
      // Place each cart item as an order to backend sequentially or in parallel
      await Promise.all(
        cartItems.map((item) => 
          createOrder({
            product_id: Number(item.product.id),
            quantity: item.quantity
          })
        )
      );

      // Clear cart
      setCartItems([]);
      localStorage.removeItem("cart");
      window.dispatchEvent(new Event("cart-updated"));
      
      alert(`Order placed successfully!`);
      await fetchDashboardData();
      setActiveTab("orders");
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Checkout failed. Please check product stock or try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId: number) => {
    if (!window.confirm("Are you sure you want to cancel this order?")) return;
    setLoading(true);
    try {
      await updateOrder(orderId, { status: "cancelled" });
      alert("Order cancelled successfully!");
      await fetchDashboardData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to cancel order.");
    } finally {
      setLoading(false);
    }
  };

  const cartTotal = cartItems.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

  const orders = ordersList;
  const pendingOrders = ordersList.filter((o: any) => o.status === "Pending" || o.status === "Processing");
  const completedOrders = ordersList.filter((o: any) => o.status === "Completed");

  const sidebarLinks = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "products", label: "Products Catalog", icon: ShoppingBag, path: "/products" },
    { id: "orders", label: "My Orders", icon: ShoppingBag },
    { id: "cart", label: "My Cart", icon: ShoppingCart, count: cartItems.reduce((acc, c) => acc + c.quantity, 0) },
    { id: "ai", label: "Ask AI Assistant", icon: MessageSquare, path: "/ai-assistant" },
  ];

  return (
    <div className="min-h-[calc(100vh-140px)] flex flex-col md:flex-row bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-xl">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-gray-50 border-r border-gray-100 p-6 flex flex-col justify-between shrink-0">
        <div className="space-y-8">
          <div className="flex items-center gap-3 border-b border-gray-200/50 pb-4">
            <div className="h-10 w-10 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-bold text-lg">
              {user?.name?.[0] || "F"}
            </div>
            <div>
              <h4 className="font-extrabold text-sm text-gray-900 leading-none">{user?.name || "Farmer"}</h4>
              <span className="text-[10px] font-bold text-green-600 uppercase tracking-widest mt-1 inline-block">Farmer Account</span>
            </div>
          </div>

          <nav className="space-y-1">
            {sidebarLinks.map((link) => {
              const Icon = link.icon;
              return link.path ? (
                <Link
                  key={link.id}
                  to={link.path}
                  className="flex items-center justify-between px-4 py-3 text-sm font-bold text-gray-600 hover:text-green-600 hover:bg-green-50/50 rounded-xl transition-all"
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} />
                    <span>{link.label}</span>
                  </div>
                </Link>
              ) : (
                <button
                  key={link.id}
                  onClick={() => setActiveTab(link.id)}
                  className={`w-full flex items-center justify-between px-4 py-3 text-sm font-bold rounded-xl transition-all ${
                    activeTab === link.id
                      ? "bg-green-600 text-white shadow"
                      : "text-gray-600 hover:text-green-600 hover:bg-green-50/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} />
                    <span>{link.label}</span>
                  </div>
                  {link.count && link.count > 0 ? (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      activeTab === link.id ? "bg-white text-green-700" : "bg-green-100 text-green-700"
                    }`}>
                      {link.count}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="pt-6 border-t border-gray-200/50 mt-8">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-red-600 hover:bg-red-50 rounded-xl transition-all"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow p-8 overflow-y-auto">
        {loading && (
          <div className="flex justify-center items-center py-4 bg-green-50 border border-green-200 text-green-700 rounded-xl mb-4 text-xs font-semibold animate-pulse">
            Syncing data with KrishiSathi server...
          </div>
        )}
        
        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-8">
            <div className="space-y-1">
              <h2 className="text-2xl font-extrabold text-gray-900 my-0 py-0">Hello, {user?.name || "Farmer"}!</h2>
              <p className="text-sm text-gray-500">Welcome to your farm command console. Track orders and manage products.</p>
            </div>

            {/* Dashboard Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex items-center gap-4">
                <div className="p-3 bg-green-50 rounded-xl text-green-600">
                  <ShoppingBag size={24} />
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-gray-900">{orders.length}</span>
                  <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mt-0.5">Total Orders</p>
                </div>
              </div>
              <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex items-center gap-4">
                <div className="p-3 bg-amber-50 rounded-xl text-amber-600">
                  <Clock size={24} />
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-gray-900">{pendingOrders.length}</span>
                  <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mt-0.5">Pending Orders</p>
                </div>
              </div>
              <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm flex items-center gap-4">
                <div className="p-3 bg-green-50 rounded-xl text-green-700">
                  <CheckCircle2 size={24} />
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-gray-900">{completedOrders.length}</span>
                  <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mt-0.5">Completed Orders</p>
                </div>
              </div>
            </div>

            {/* Recent Orders Table */}
            <div className="space-y-4">
              <h3 className="text-lg font-extrabold text-gray-900">Recent Purchase Orders</h3>
              <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-gray-400 text-xs font-bold uppercase tracking-wider">
                      <tr>
                        <th className="px-6 py-4">Order ID</th>
                        <th className="px-6 py-4">Date</th>
                        <th className="px-6 py-4">Total Price</th>
                        <th className="px-6 py-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-gray-700 font-medium">
                      {orders.length > 0 ? (
                        orders.slice(0, 5).map((order: any) => (
                          <tr key={order.id} className="hover:bg-gray-50/50">
                            <td className="px-6 py-4 text-green-600 font-bold">{order.id}</td>
                            <td className="px-6 py-4">{order.date}</td>
                            <td className="px-6 py-4">₹{order.total}</td>
                            <td className="px-6 py-4">
                              <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-bold ${
                                order.status === "Completed"
                                  ? "bg-green-50 text-green-700 border border-green-100"
                                  : order.status === "Cancelled"
                                  ? "bg-red-50 text-red-700 border border-red-100"
                                  : "bg-amber-50 text-amber-700 border border-amber-100"
                              }`}>
                                {order.status}
                              </span>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="px-6 py-8 text-center text-gray-400 text-sm">
                            No orders placed yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === "orders" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-extrabold text-gray-900 my-0 py-0">My Purchase Orders</h2>
            
            {orders.length > 0 ? (
              <div className="space-y-4">
                {orders.map((order: any) => (
                  <div key={order.id} className="border border-gray-100 rounded-2xl p-6 bg-white shadow-sm space-y-4 animate-in fade-in duration-200">
                    <div className="flex justify-between items-center border-b border-gray-50 pb-4">
                      <div className="flex items-center gap-4">
                        <span className="font-extrabold text-green-600">{order.id}</span>
                        <span className="text-xs text-gray-400 font-semibold">{order.date}</span>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        order.status === "Completed"
                          ? "bg-green-50 text-green-700 border border-green-100"
                          : order.status === "Cancelled"
                          ? "bg-red-50 text-red-700 border border-red-100"
                          : "bg-amber-50 text-amber-700 border border-amber-100"
                      }`}>
                        {order.status}
                      </span>
                    </div>
                    
                    {/* Items List */}
                    <div className="space-y-3">
                      {order.items.map((item: any, i: number) => (
                        <div key={i} className="flex justify-between items-center text-sm">
                          <div className="flex items-center gap-3">
                            <img src={item.image} alt={item.productName} className="w-12 h-10 rounded-lg object-cover" />
                            <div>
                              <p className="font-bold text-gray-800 line-clamp-1">{item.productName}</p>
                              <span className="text-xs text-gray-400">Qty: {item.quantity} × ₹{item.price}</span>
                            </div>
                          </div>
                          <span className="font-bold text-gray-900">₹{item.price * item.quantity}</span>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-between items-center border-t border-gray-50 pt-4 font-extrabold text-base">
                      <span className="text-gray-500 text-sm">Order Grand Total:</span>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-900">₹{order.total}</span>
                        {order.status.toLowerCase() === "pending" && (
                          <button
                            onClick={() => handleCancelOrder(order.realId)}
                            className="px-3.5 py-2 bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs rounded-xl transition-all shadow-sm"
                          >
                            Cancel Order
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white border border-gray-100 rounded-3xl p-16 text-center space-y-4">
                <span className="text-5xl">📦</span>
                <h3 className="font-extrabold text-lg text-gray-900">No Orders Placed</h3>
                <p className="text-gray-500 max-w-sm mx-auto">
                  You haven't placed any orders yet. Visit the catalog to buy seeds, fertilizers, or pesticides.
                </p>
                <Link 
                  to="/products"
                  className="inline-block px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-md transition-all text-sm"
                >
                  Shop Products
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Cart Tab */}
        {activeTab === "cart" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-extrabold text-gray-900 my-0 py-0">Shopping Cart</h2>
            
            {cartItems.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Cart Items List */}
                <div className="lg:col-span-2 space-y-4">
                  {cartItems.map((item) => (
                    <div key={item.product.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between border border-gray-100 p-4 rounded-2xl bg-white shadow-sm gap-4">
                      <div className="flex items-center gap-4">
                        <img src={item.product.image} alt={item.product.name} className="w-16 h-14 rounded-xl object-cover shrink-0" />
                        <div>
                          <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{item.product.name}</h4>
                          <span className="text-xs text-gray-400 font-semibold">{item.product.brand}</span>
                          <p className="text-green-700 font-extrabold text-sm mt-1">₹{item.product.price}</p>
                        </div>
                      </div>

                      {/* Quantity Action */}
                      <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-start">
                        <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                          <button 
                            onClick={() => handleUpdateCartQty(item.product.id, item.quantity - 1)}
                            className="px-3 py-1.5 text-gray-500 hover:bg-gray-100 font-bold"
                          >
                            -
                          </button>
                          <span className="px-3 text-xs font-bold text-gray-900 w-8 text-center">{item.quantity}</span>
                          <button 
                            onClick={() => handleUpdateCartQty(item.product.id, item.quantity + 1)}
                            className="px-3 py-1.5 text-gray-500 hover:bg-gray-100 font-bold"
                          >
                            +
                          </button>
                        </div>

                        <button 
                          onClick={() => handleRemoveFromCart(item.product.id)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-all"
                          title="Remove item"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Checkout Summary Card */}
                <div className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm h-fit space-y-6">
                  <h3 className="font-extrabold text-gray-900 border-b border-gray-50 pb-4">Order Summary</h3>
                  
                  <div className="space-y-3.5 text-sm">
                    <div className="flex justify-between text-gray-500">
                      <span>Subtotal</span>
                      <span className="font-bold text-gray-800">₹{cartTotal}</span>
                    </div>
                    <div className="flex justify-between text-gray-500">
                      <span>Shipping</span>
                      <span className="text-green-600 font-bold">FREE</span>
                    </div>
                    <div className="flex justify-between text-gray-500">
                      <span>Tax (GST)</span>
                      <span className="font-bold text-gray-800">₹0</span>
                    </div>
                    <div className="border-t border-gray-50 pt-3 flex justify-between font-extrabold text-base text-gray-900">
                      <span>Total Amount:</span>
                      <span>₹{cartTotal}</span>
                    </div>
                  </div>

                  <button 
                    onClick={handleCheckout}
                    className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-extrabold rounded-xl transition-all shadow hover:shadow-lg flex items-center justify-center gap-2"
                  >
                    Place Order (Cash on Delivery) <ArrowRight size={16} />
                  </button>
                </div>

              </div>
            ) : (
              <div className="bg-white border border-gray-100 rounded-3xl p-16 text-center space-y-4">
                <span className="text-5xl">🛒</span>
                <h3 className="font-extrabold text-lg text-gray-900">Your Cart is Empty</h3>
                <p className="text-gray-500 max-w-sm mx-auto">
                  Browse our store catalog and pick seeds, fertilizers or pesticides to boost your harvest.
                </p>
                <Link 
                  to="/products"
                  className="inline-block px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-md transition-all text-sm"
                >
                  Shop Products
                </Link>
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}
