import { Routes, Route } from "react-router-dom";

import Home from "../pages/Home";
import ProductsPage from "../pages/ProductsPage";
import ProductDetails from "../pages/ProductDetails";
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import AIAssistant from "../pages/AIAssistant";
import FarmerDashboard from "../pages/farmer/Dashboard";
import AdminDashboard from "../pages/admin/Dashboard";
import ProductScanner from "../pages/admin/ProductScanner";

import ProtectedRoute from "../components/common/ProtectedRoute";
import AdminRoute from "../components/common/AdminRoute";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Home />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/products/:id" element={<ProductDetails />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/ai-assistant" element={<AIAssistant />} />

      {/* Farmer Dashboard Protected Route */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <FarmerDashboard />
          </ProtectedRoute>
        }
      />

      {/* Admin Dashboard Protected Routes */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/scanner"
        element={
          <AdminRoute>
            <ProductScanner />
          </AdminRoute>
        }
      />
      
      {/* Fallback route */}
      <Route path="*" element={<Home />} />
    </Routes>
  );
}