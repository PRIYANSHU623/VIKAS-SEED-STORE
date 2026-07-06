import { Link } from "react-router-dom";
import { Sprout, Phone, Mail, MapPin, ShieldCheck } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-300 border-t border-gray-800">
      {/* Top Banner Accent */}
      <div className="bg-green-600 h-1.5 w-full"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          
          {/* Column 1: About */}
          <div className="space-y-6">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="p-2 bg-green-950 rounded-xl group-hover:bg-green-900 transition-colors">
                <Sprout size={24} className="text-green-400" />
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-lg text-white leading-none">
                  Vikas Beej Bhandar
                </span>
                <span className="text-xs text-green-400 font-semibold tracking-wider uppercase mt-0.5">
                  KrishiSathi
                </span>
              </div>
            </Link>
            <p className="text-sm text-gray-400 leading-relaxed">
              Empowering farmers across the country with high-yielding seeds, premium fertilizers, and highly effective herbicides and pesticides. Built on trust and quality service.
            </p>
            <div className="flex items-center gap-3">
              <a href="#" className="p-2 bg-gray-800 hover:bg-green-600 hover:text-white rounded-lg transition-all" aria-label="Facebook">
                <svg className="w-[18px] h-[18px] fill-current" viewBox="0 0 24 24"><path d="M9 8H7v3h2v9h3v-9h2.72l.42-3H12V6.5a1 1 0 0 1 1-1h1.5V2H12a5 5 0 0 0-5 5V8z"/></svg>
              </a>
              <a href="#" className="p-2 bg-gray-800 hover:bg-green-600 hover:text-white rounded-lg transition-all" aria-label="Twitter">
                <svg className="w-[18px] h-[18px] fill-current" viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
              </a>
              <a href="#" className="p-2 bg-gray-800 hover:bg-green-600 hover:text-white rounded-lg transition-all" aria-label="Instagram">
                <svg className="w-[18px] h-[18px] fill-none stroke-current stroke-2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
              </a>
            </div>
          </div>


          {/* Column 2: Quick Links */}
          <div>
            <h3 className="text-white font-bold text-base mb-6 tracking-wide uppercase">Quick Links</h3>
            <ul className="space-y-3.5 text-sm">
              <li>
                <Link to="/" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">Home</Link>
              </li>
              <li>
                <Link to="/products" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">All Products</Link>
              </li>
              <li>
                <Link to="/ai-assistant" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">AI Assistant Chat</Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">User Login</Link>
              </li>
              <li>
                <Link to="/register" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">Register New Account</Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Categories */}
          <div>
            <h3 className="text-white font-bold text-base mb-6 tracking-wide uppercase">Product Categories</h3>
            <ul className="space-y-3.5 text-sm">
              <li>
                <Link to="/products?category=seeds" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">Quality Crop Seeds</Link>
              </li>
              <li>
                <Link to="/products?category=fertilizers" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">NPK & Organic Fertilizers</Link>
              </li>
              <li>
                <Link to="/products?category=herbicides" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">Weedicides & Herbicides</Link>
              </li>
              <li>
                <Link to="/products?category=pesticides" className="hover:text-green-400 hover:translate-x-1 inline-block transition-all">Systemic & Organic Pesticides</Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Contact Info */}
          <div className="space-y-6">
            <h3 className="text-white font-bold text-base mb-6 tracking-wide uppercase">Contact Us</h3>
            <ul className="space-y-4 text-sm text-gray-400">
              <li className="flex items-start gap-3">
                <MapPin size={18} className="text-green-500 shrink-0 mt-0.5" />
                <span>Vikas Beej Bhandar, Main Market Road, Grain Market Area, India</span>
              </li>
              <li className="flex items-center gap-3">
                <Phone size={18} className="text-green-500 shrink-0" />
                <span>+91 98765 43210</span>
              </li>
              <li className="flex items-center gap-3">
                <Mail size={18} className="text-green-500 shrink-0" />
                <span>support@vikasbeejbhandar.com</span>
              </li>
            </ul>
            <div className="pt-2">
              <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-950 p-3 rounded-xl border border-gray-800/50">
                <ShieldCheck size={16} className="text-green-500" />
                <span>ISO 9001:2015 Certified Dealer</span>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 mt-16 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500">
          <p>© {currentYear} Vikas Beej Bhandar - KrishiSathi. All rights reserved.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-gray-300">Privacy Policy</a>
            <a href="#" className="hover:text-gray-300">Terms of Service</a>
            <a href="#" className="hover:text-gray-300">Sitemap</a>
          </div>
        </div>
      </div>
    </footer>
  );
}