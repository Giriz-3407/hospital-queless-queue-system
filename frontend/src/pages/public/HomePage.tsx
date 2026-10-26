import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Department } from '../../types';
import { departmentService } from '../../services/departmentService';
import { formatWaitTime } from '../../utils/formatters';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Clock, Users, ArrowRight, Activity, CheckCircle, Sparkles } from 'lucide-react';

export const HomePage: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    departmentService
      .getDepartments()
      .then(setDepartments)
      .catch((err) => console.error('Error fetching departments:', err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-16 py-12">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" /> Next-Gen Hospital Queue Management
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
          Say Goodbye to Crowded Waiting Rooms. <span className="text-sky-600">Queue Virtually.</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto font-normal">
          Join hospital queues from your phone or home, track your position in real time,
          and arrive just when the doctor is ready to see you.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link to="/patient/join">
            <Button size="lg" className="gap-2 shadow-lg shadow-sky-600/25 w-full sm:w-auto">
              Join Virtual Queue Now <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link to="/staff/dashboard">
            <Button variant="outline" size="lg" className="gap-2 w-full sm:w-auto">
              <Users className="w-4 h-4" /> Hospital Staff Portal
            </Button>
          </Link>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
              <Clock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Real-Time Queue Tracking</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Live estimated wait times and dynamic position recalculation ensure you are always informed.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Fair & Transparent FIFO</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              First-in, first-out automated queue ordering with unique sequential department tickets.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Doctor & Staff Control</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Medical staff easily manage patient calls, consultations, and no-shows from a unified dashboard.
            </p>
          </div>
        </div>
      </section>

      {/* Live Department Wait Times Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Live Department Wait Times</h2>
            <p className="text-sm text-slate-500">Real-time status across hospital specialty clinics</p>
          </div>
          <Link to="/patient/join">
            <Button variant="secondary" size="sm" className="gap-1.5">
              Select Department <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 bg-white rounded-2xl border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {departments.map((dept) => (
              <Card key={dept.id} className="hover:shadow-md transition-shadow">
                <CardContent className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100">
                        {dept.code}
                      </span>
                      <h4 className="text-lg font-bold text-slate-900 mt-1">{dept.name}</h4>
                    </div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Live
                    </span>
                  </div>

                  <p className="text-xs text-slate-500 line-clamp-2">{dept.description}</p>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                    <div className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      <span><strong>{dept.current_waiting ?? 0}</strong> waiting</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{formatWaitTime(dept.estimated_wait_minutes ?? 0)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
