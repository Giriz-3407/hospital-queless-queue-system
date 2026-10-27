import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { departmentService } from '../../services/departmentService';
import { queueService } from '../../services/queueService';
import { Department, QueueTicket } from '../../types';
import { Card, CardHeader, CardContent, CardFooter } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { StatusBadge } from '../../components/common/StatusBadge';
import {
  Activity,
  Clock,
  Users,
  Stethoscope,
  LogIn,
  UserPlus,
  ArrowRight,
  Smartphone,
  AlertTriangle,
  CheckCircle2,
  Building2,
  ExternalLink,
} from 'lucide-react';

export const DepartmentLandingPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [department, setDepartment] = useState<Department | null>(null);
  const [activeTicket, setActiveTicket] = useState<QueueTicket | null>(null);
  const [reason, setReason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Centralized mobile app install destination (empty placeholder by default)
  const appInstallUrl = import.meta.env.VITE_APP_INSTALL_URL || '';

  // Auto-redirect to native Android app via intent if opened on an Android mobile device
  useEffect(() => {
    const isAndroid = typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent);
    if (isAndroid && slug) {
      const intentUrl = `intent://department/${slug}#Intent;scheme=queueless;package=com.queueless.hospital;end`;
      const timer = setTimeout(() => {
        window.location.href = intentUrl;
      }, 400);
      return () => clearTimeout(timer);
    }
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    setIsLoading(true);
    setError(null);

    departmentService
      .getDepartmentByIdOrSlug(slug)
      .then((data) => {
        setDepartment(data);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || `Department "${slug}" was not found or is currently unavailable.`);
        setIsLoading(false);
      });
  }, [slug]);

  // Check if current authenticated patient already has an active ticket
  useEffect(() => {
    if (isAuthenticated && user?.role === 'patient') {
      queueService
        .getMyQueues()
        .then((tickets) => {
          const active = tickets.find((t) => {
            const s = (t.status || '').toUpperCase();
            return s === 'WAITING' || s === 'CALLED' || s === 'IN_CONSULTATION';
          });
          setActiveTicket(active || null);
        })
        .catch((err) => console.error('Error fetching patient queues:', err));
    }
  }, [isAuthenticated, user]);

  const handleJoinQueue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!department) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const ticket = await queueService.joinQueue({
        department_id: department.id,
        reason: reason.trim() || undefined,
      });
      // Navigate to live tracking screen
      navigate(`/patient/queue/${ticket.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to join the virtual queue. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const departmentSlug = department?.slug || slug || '';
  const redirectParam = `/department/${departmentSlug}`;

  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
        <Activity className="w-10 h-10 text-sky-600 animate-spin mb-4" />
        <h2 className="text-xl font-bold text-slate-800">Resolving Department...</h2>
        <p className="text-sm text-slate-500 mt-1">Connecting to Queueless Hospital Queue System</p>
      </div>
    );
  }

  if (error && !department) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <Card className="border-red-200">
          <CardHeader>
            <div className="w-12 h-12 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mb-2">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Department Unavailable</h1>
            <p className="text-sm text-slate-500 mt-1">
              The department slug or link you opened could not be resolved on the server.
            </p>
          </CardHeader>
          <CardContent>
            <Alert variant="error">{error}</Alert>
            <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-600">
              <p className="font-semibold text-slate-800 mb-1">Looking for a specific clinic?</p>
              <p>
                Hospital departments might be renamed or undergoing maintenance. Please visit our main department directory to view all live clinics and wait times.
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between items-center">
            <Link to="/">
              <Button variant="outline">Browse All Departments</Button>
            </Link>
            <Link to="/login">
              <Button variant="primary">Sign In</Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  const isInactive = department && !department.is_active;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Mobile App Smart Banner for immediate 1-tap jump */}
      <div className="bg-gradient-to-r from-sky-600 to-indigo-700 text-white p-4 rounded-2xl shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
            <Smartphone className="w-5 h-5 text-white" />
          </div>
          <div>
            <h4 className="text-sm font-bold">Have the Queueless Android App?</h4>
            <p className="text-xs text-sky-100">Tap to open this department directly in the native mobile application.</p>
          </div>
        </div>
        <a
          href={`intent://department/${departmentSlug}#Intent;scheme=queueless;package=com.queueless.hospital;end`}
          className="flex-shrink-0 w-full sm:w-auto"
        >
          <Button size="sm" className="w-full sm:w-auto bg-white text-sky-700 hover:bg-sky-50 font-bold shadow-sm whitespace-nowrap">
            Open in Queueless App
          </Button>
        </a>
      </div>

      {/* Queueless Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center shadow-inner">
            <Building2 className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-600 bg-sky-50 px-2 py-0.5 rounded-md">
                {department?.code} Clinic
              </span>
              {!isInactive && <StatusBadge status="WAITING" />}
              {isInactive && <span className="text-xs font-semibold px-2 py-0.5 rounded bg-red-100 text-red-700">Currently Closed</span>}
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">{department?.name}</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Queueless Smart Hospital Queue &bull; Fallback Web Portal
            </p>
          </div>
        </div>

        <Link to="/" className="text-sm text-sky-600 hover:text-sky-700 font-semibold flex items-center gap-1 self-start sm:self-auto">
          View all clinics <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Inactive Department Notice */}
      {isInactive && (
        <Alert variant="warning">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-900">This department is currently closed or inactive.</p>
              <p className="text-xs text-amber-700 mt-0.5">
                Queue registration is paused. Please speak with hospital reception or check the main directory for open departments.
              </p>
            </div>
          </div>
        </Alert>
      )}

      {/* Department Overview Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 bg-white border-slate-200">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-medium">Estimated Wait</span>
            <Clock className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {department?.estimated_wait_minutes !== null && department?.estimated_wait_minutes !== undefined
              ? `~${department.estimated_wait_minutes} min`
              : 'Unavailable'}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Based on doctor availability</p>
        </Card>

        <Card className="p-4 bg-white border-slate-200">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-medium">Patients Waiting</span>
            <Users className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{department?.current_waiting ?? 0}</div>
          <p className="text-[11px] text-slate-400 mt-1">In virtual line ahead</p>
        </Card>

        <Card className="p-4 bg-white border-slate-200">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-medium">Consultation Avg</span>
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{department?.avg_consultation_time} min</div>
          <p className="text-[11px] text-slate-400 mt-1">Target consultation time</p>
        </Card>

        <Card className="p-4 bg-white border-slate-200">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-medium">Doctors on Duty</span>
            <Stethoscope className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {department?.available_doctors_count ?? 0}
            <span className="text-xs font-normal text-slate-400"> / {department?.total_doctors_count ?? 0}</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Attending providers</p>
        </Card>
      </div>

      {/* Description & Doctors */}
      {department?.description && (
        <Card className="p-5 bg-white border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">Clinic Scope & Details</h2>
          <p className="text-sm text-slate-600 leading-relaxed">{department.description}</p>
        </Card>
      )}

      {/* Queue Joining Flow Section */}
      {!isInactive && (
        <>
          {/* Case 1: Patient Already Holds an Active Queue Ticket */}
          {isAuthenticated && activeTicket && (
            <Card className="p-6 border-amber-300 bg-amber-50/50">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div className="space-y-2 flex-1">
                  <h2 className="text-lg font-bold text-slate-900">One Active Queue Rule Enforced</h2>
                  <p className="text-sm text-slate-600">
                    You currently hold active ticket{' '}
                    <span className="font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">
                      {activeTicket.token_number}
                    </span>{' '}
                    in <strong>{activeTicket.department_name}</strong>.
                  </p>
                  <p className="text-xs text-slate-500">
                    Hospital policy permits each patient at most one active queue ticket across the entire hospital at any time. Once your current consultation is completed or cancelled, you may take a place in another clinic.
                  </p>
                  <div className="pt-2">
                    <Link to={`/patient/queue/${activeTicket.id}`}>
                      <Button variant="primary" className="gap-2">
                        View Active Ticket ({activeTicket.token_number}) <ArrowRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Case 2: Authenticated Patient with No Active Ticket (Can Join Queue) */}
          {isAuthenticated && !activeTicket && (
            <Card className="border-sky-200 bg-white shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Confirm & Join {department?.name} Queue</h2>
                    <p className="text-xs text-slate-500">
                      Logged in as <strong>{user?.name}</strong> ({user?.email})
                    </p>
                  </div>
                </div>
              </CardHeader>

              <form onSubmit={handleJoinQueue}>
                <CardContent className="space-y-4">
                  <p className="text-sm text-slate-600">
                    By confirming, you will be allocated an atomic sequential token for today's clinic and entered into the live consultation queue.
                  </p>

                  <Input
                    label="Reason for Visit / Chief Complaint (Optional)"
                    placeholder="e.g., Routine follow-up, acute symptoms, doctor referral..."
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </CardContent>

                <CardFooter className="flex justify-between items-center bg-slate-50/60 border-t border-slate-100 p-4">
                  <Link to="/">
                    <Button variant="outline" type="button">
                      Cancel
                    </Button>
                  </Link>

                  <Button variant="primary" type="submit" disabled={isSubmitting} className="gap-2">
                    {isSubmitting ? 'Allocating Token...' : 'Confirm & Join Queue'}
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </CardFooter>
              </form>
            </Card>
          )}

          {/* Case 3: Unauthenticated User (Needs Login/Registration) */}
          {!isAuthenticated && (
            <Card className="border-slate-200 bg-white p-6 shadow-sm">
              <div className="max-w-xl mx-auto text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
                  <LogIn className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900">
                  Ready to join the {department?.name} queue?
                </h2>
                <p className="text-sm text-slate-600">
                  Sign in with your patient account or register in 30 seconds. Your department selection will be preserved, and you will be returned directly here to confirm your queue entry.
                </p>

                <div className="flex flex-col sm:flex-row justify-center gap-3 pt-2">
                  <Link to={`/login?redirect=${encodeURIComponent(redirectParam)}`} className="flex-1">
                    <Button variant="primary" className="w-full gap-2">
                      <LogIn className="w-4 h-4" /> Sign In to Join
                    </Button>
                  </Link>
                  <Link to={`/register?redirect=${encodeURIComponent(redirectParam)}`} className="flex-1">
                    <Button variant="outline" className="w-full gap-2">
                      <UserPlus className="w-4 h-4" /> Create Patient Account
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Mobile App Promotion & Notification Clarity Card */}
      <Card className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl border-0 shadow-lg">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center flex-shrink-0 text-sky-400">
              <Smartphone className="w-6 h-6" />
            </div>
            <div className="space-y-1.5 max-w-xl">
              <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-300 uppercase tracking-wider">
                <span>Queueless Android App</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-200 border border-sky-400/30">
                  App-First Queue Experience
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">Prefer automatic on-device queue alerts?</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Prefer queue updates and live notifications on your phone? Open directly in the Queueless Android App.
              </p>
            </div>
          </div>

          <div className="self-stretch sm:self-auto flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <a
              href={`intent://department/${departmentSlug}#Intent;scheme=queueless;package=com.queueless.hospital;end`}
              className="inline-flex"
            >
              <Button className="w-full sm:w-auto bg-sky-500 hover:bg-sky-600 text-white gap-2 font-semibold shadow-md shadow-sky-500/30">
                <Smartphone className="w-4 h-4" /> Open in App
              </Button>
            </a>
            {appInstallUrl ? (
              <a href={appInstallUrl} target="_blank" rel="noopener noreferrer" className="inline-flex">
                <Button variant="outline" className="w-full sm:w-auto text-slate-200 border-white/20 hover:bg-white/10 gap-2 font-semibold">
                  Install APK <ExternalLink className="w-4 h-4" />
                </Button>
              </a>
            ) : null}
          </div>
        </div>
      </Card>
    </div>
  );
};
