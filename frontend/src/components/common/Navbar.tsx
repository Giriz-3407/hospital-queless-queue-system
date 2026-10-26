import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Activity, LogOut, Menu, X, Clock, ShieldAlert, Stethoscope, PlusCircle } from 'lucide-react';
import { Button } from '../ui/Button';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2.5">
            <div className="w-10 h-10 rounded-xl bg-sky-600 flex items-center justify-center text-white shadow-md shadow-sky-600/20">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
                Queueless{' '}
                <span className="text-sky-600 font-semibold text-xs px-2 py-0.5 bg-sky-50 rounded-full border border-sky-100">
                  Smart Hospital
                </span>
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium text-slate-600">
            <Link to="/" className="hover:text-sky-600 transition-colors">
              Home
            </Link>

            {isAuthenticated && user?.role === 'patient' && (
              <>
                <Link to="/patient/dashboard" className="hover:text-sky-600 transition-colors flex items-center gap-1">
                  <Clock className="w-4 h-4" /> My Queues
                </Link>
                <Link to="/patient/join" className="hover:text-sky-600 transition-colors flex items-center gap-1">
                  <PlusCircle className="w-4 h-4" /> Join Queue
                </Link>
              </>
            )}

            {isAuthenticated && user?.role === 'doctor' && (
              <Link to="/doctor/dashboard" className="hover:text-sky-600 transition-colors flex items-center gap-1.5 font-semibold text-sky-700">
                <Stethoscope className="w-4 h-4" /> Doctor Console
              </Link>
            )}

            {isAuthenticated && user?.role === 'admin' && (
              <>
                <Link to="/admin/dashboard" className="hover:text-purple-600 transition-colors flex items-center gap-1.5 font-semibold text-purple-700">
                  <ShieldAlert className="w-4 h-4" /> Admin Portal
                </Link>
                <Link to="/doctor/dashboard" className="hover:text-sky-600 transition-colors flex items-center gap-1">
                  <Stethoscope className="w-4 h-4" /> Doctor Console
                </Link>
              </>
            )}
          </nav>

          {/* Desktop Auth Section */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-sm font-semibold text-slate-800">{user.name}</div>
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${
                      user.role === 'admin'
                        ? 'bg-purple-100 text-purple-800 border border-purple-200'
                        : user.role === 'doctor'
                        ? 'bg-sky-100 text-sky-800 border border-sky-200'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
                <Button variant="outline" size="sm" onClick={handleLogout} className="gap-1.5">
                  <LogOut className="w-4 h-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link to="/register">
                  <Button variant="primary" size="sm">
                    Register as Patient
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile hamburger button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block py-2 text-sm font-medium text-slate-700 hover:text-sky-600"
          >
            Home
          </Link>

          {isAuthenticated && user?.role === 'patient' && (
            <>
              <Link
                to="/patient/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block py-2 text-sm font-medium text-slate-700 hover:text-sky-600"
              >
                My Queues
              </Link>
              <Link
                to="/patient/join"
                onClick={() => setMobileMenuOpen(false)}
                className="block py-2 text-sm font-medium text-slate-700 hover:text-sky-600"
              >
                Join Virtual Queue
              </Link>
            </>
          )}

          {isAuthenticated && user?.role === 'doctor' && (
            <Link
              to="/doctor/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-semibold text-sky-700"
            >
              Doctor Console
            </Link>
          )}

          {isAuthenticated && user?.role === 'admin' && (
            <>
              <Link
                to="/admin/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block py-2 text-sm font-semibold text-purple-700"
              >
                Admin Portal
              </Link>
              <Link
                to="/doctor/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block py-2 text-sm font-medium text-sky-700"
              >
                Doctor Console
              </Link>
            </>
          )}

          <div className="pt-3 border-t border-slate-100">
            {isAuthenticated && user ? (
              <div className="space-y-3">
                <div className="text-sm font-medium text-slate-800">
                  Signed in as <strong className="capitalize">{user.name}</strong> ({user.role})
                </div>
                <Button variant="outline" size="sm" onClick={handleLogout} className="w-full justify-center gap-1.5">
                  <LogOut className="w-4 h-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="ghost" size="sm" className="w-full justify-center">
                    Sign In
                  </Button>
                </Link>
                <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" size="sm" className="w-full justify-center">
                    Register as Patient
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
