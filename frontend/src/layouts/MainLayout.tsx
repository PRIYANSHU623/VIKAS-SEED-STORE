import { useLocation } from "react-router-dom";
import Navbar from "../components/common/Navbar";
import Footer from "../components/common/Footer";

export default function MainLayout({
  children,
}: any) {
  const location = useLocation();
  const isAIAssistant = location.pathname === "/ai-assistant";

  if (isAIAssistant) {
    return (
      <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50">
        <Navbar />
        <main className="flex-grow overflow-hidden relative flex flex-col">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Navbar />

      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-6">
        {children}
      </main>

      <Footer />
    </div>
  );
}