import React from 'react';
import { Activity, ShieldCheck, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2 text-slate-700">
            <Activity className="w-5 h-5 text-sky-600" />
            <span className="font-semibold text-sm">Queueless Smart Hospital System</span>
          </div>

          <div className="flex items-center space-x-6 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Virtual Queueing Protected
            </span>
            <span className="flex items-center gap-1">
              <Heart className="w-4 h-4 text-rose-500" /> Patient-First Healthcare
            </span>
          </div>

          <div className="text-xs text-slate-400">
            &copy; {new Date().getFullYear()} Queueless Hospital. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};
