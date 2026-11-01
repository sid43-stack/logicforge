import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Menu, X, PlayCircle, BookOpen, Clock, LayoutDashboard } from 'lucide-react';
import { Button } from './Button';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { to: '/', label: 'Overview' },
    { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { to: '/knowledge', label: 'Knowledge Base', icon: <BookOpen className="w-4 h-4" /> },
    { to: '/history', label: 'Audit History', icon: <Clock className="w-4 h-4" /> },
  ];

  return (
    <nav className="bg-[#29261F]/95 backdrop-blur border-b border-[#4A4338] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2.5 group">
              <div className="w-9 h-9 rounded-lg bg-gold-600 flex items-center justify-center shadow-sm group-hover:bg-gold-500 transition-colors">
                <Activity className="w-5 h-5 text-[#2B2822]" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight text-[#F2EEE4] flex items-center gap-1.5">
                  NetSage
                  <span className="text-[10px] font-mono tracking-normal px-1.5 py-0.2 rounded bg-gold-500/10 text-gold-300 border border-gold-500/20">
                    KBES
                  </span>
                </span>
                <span className="text-[10px] text-[#BDB4A5] -mt-0.5 hidden sm:block">
                  Network Troubleshooting Expert System
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                    isActive
                      ? 'bg-[#EAE3D8] text-gold-700 border border-stone-400/80 shadow-inner'
                      : 'text-[#D6CCBA] hover:text-[#F2EEE4] hover:bg-[#EAE3D8]/60'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Actions & Start CTA */}
          <div className="hidden sm:flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Inference Engine Ready</span>
            </div>

            <Link to="/diagnose">
              <Button
                variant="primary"
                size="sm"
                icon={<PlayCircle className="w-4 h-4" />}
                className="shadow-sm"
              >
                Start Diagnosis
              </Button>
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center gap-2">
            <Link to="/diagnose">
              <Button variant="primary" size="sm" className="text-xs px-2.5 py-1">
                Diagnose
              </Button>
            </Link>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-[#BDB4A5] hover:text-[#F2EEE4] hover:bg-[#EAE3D8] transition-colors"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#4A4338] bg-[#29261F] px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive
                    ? 'bg-[#EAE3D8] text-gold-700 border border-stone-400'
                    : 'text-[#D6CCBA] hover:bg-[#EAE3D8] hover:text-[#F2EEE4]'
                }`}
              >
                {link.icon}
                {link.label}
              </Link>
            );
          })}
          <div className="pt-2 border-t border-[#4A4338] mt-2">
            <div className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs font-medium text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Rule-Based Inference Engine Online</span>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};
