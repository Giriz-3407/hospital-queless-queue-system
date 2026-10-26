import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { DoctorQueueResponse } from '../../types';
import { doctorService } from '../../services/doctorService';
import { formatDateTime } from '../../utils/formatters';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Alert } from '../../components/ui/Alert';
import {
  Users,
  CheckCircle,
  Clock,
  PhoneCall,
  Check,
  UserX,
  RefreshCw,
  Stethoscope,
  Loader2,
  Play,
} from 'lucide-react';

export const DoctorDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [queueData, setQueueData] = useState<DoctorQueueResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);
  const [consultationNotes, setConsultationNotes] = useState<string>('');
  const isVisibleRef = useRef<boolean>(true);

  const fetchDoctorQueue = useCallback(async (isBackground: boolean = false) => {
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;

    try {
      if (!isBackground && !queueData) setIsLoading(true);
      const data = await doctorService.getDoctorQueue();
      setQueueData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch doctor queue.');
    } finally {
      setIsLoading(false);
    }
  }, [queueData]);

  useEffect(() => {
    fetchDoctorQueue(false);

    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isVisibleRef.current = isVisible;
      if (isVisible) fetchDoctorQueue(true);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    const interval = setInterval(() => {
      if (isVisibleRef.current) fetchDoctorQueue(true);
    }, 10000);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      clearInterval(interval);
    };
  }, [fetchDoctorQueue]);

  // Actions
  const handleCallNext = async () => {
    setIsActionLoading(true);
    setError(null);
    try {
      await doctorService.callNextPatient();
      await fetchDoctorQueue(false);
    } catch (err: any) {
      setError(err.message || 'Failed to call next patient.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleStartConsultation = async (queueId: string) => {
    setIsActionLoading(true);
    setError(null);
    try {
      await doctorService.startConsultation(queueId);
      await fetchDoctorQueue(false);
    } catch (err: any) {
      setError(err.message || 'Failed to start consultation.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleCompleteConsultation = async (queueId: string) => {
    setIsActionLoading(true);
    setError(null);
    try {
      await doctorService.completeConsultation(queueId, consultationNotes.trim() || undefined);
      setConsultationNotes('');
      await fetchDoctorQueue(false);
    } catch (err: any) {
      setError(err.message || 'Failed to complete consultation.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleMarkNoShow = async (queueId: string) => {
    if (!window.confirm('Mark this patient as No-Show?')) return;
    setIsActionLoading(true);
    setError(null);
    try {
      await doctorService.markNoShow(queueId, 'Marked as No-Show by attending doctor');
      await fetchDoctorQueue(false);
    } catch (err: any) {
      setError(err.message || 'Failed to mark as No-Show.');
    } finally {
      setIsActionLoading(false);
    }
  };

  if (isLoading && !queueData) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 text-sky-600 animate-spin" />
        <p className="text-sm text-slate-500">Loading your clinic queue...</p>
      </div>
    );
  }

  const calledPatient = queueData?.currently_called;
  const inConsultationPatient = queueData?.currently_serving;
  const waitingList = queueData?.waiting_queue || [];
  const stats = queueData?.stats || { waiting: 0, called: 0, in_consultation: 0, completed_today: 0 };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Doctor Consultation Console</h1>
            <p className="text-sm text-slate-500">
              {queueData?.doctor?.display_name || user?.name} &bull;{' '}
              <span className="font-semibold text-slate-700">
                {queueData?.department?.name || 'Assigned Department'} ({queueData?.department?.code})
              </span>
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchDoctorQueue(false)}
          className="gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Live
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-amber-50/50 border-amber-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-800">Waiting Patients</span>
            <Users className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-3xl font-extrabold text-amber-900 mt-2">{stats.waiting}</div>
          <p className="text-[11px] text-amber-700 mt-1">Eligible in queue</p>
        </Card>

        <Card className="p-4 bg-sky-50/50 border-sky-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-800">Currently Called</span>
            <PhoneCall className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-3xl font-extrabold text-sky-900 mt-2">
            {calledPatient ? (calledPatient.token_number || calledPatient.ticket_number) : 'None'}
          </div>
          <p className="text-[11px] text-sky-700 mt-1">
            {calledPatient ? calledPatient.patient_name : 'No active call'}
          </p>
        </Card>

        <Card className="p-4 bg-indigo-50/50 border-indigo-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-800">In Consultation</span>
            <Clock className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-3xl font-extrabold text-indigo-900 mt-2">
            {inConsultationPatient ? (inConsultationPatient.token_number || inConsultationPatient.ticket_number) : 'None'}
          </div>
          <p className="text-[11px] text-indigo-700 mt-1">
            {inConsultationPatient ? inConsultationPatient.patient_name : 'Room available'}
          </p>
        </Card>

        <Card className="p-4 bg-emerald-50/50 border-emerald-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-800">Completed Today</span>
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-900 mt-2">{stats.completed_today}</div>
          <p className="text-[11px] text-emerald-700 mt-1">Consultations finished</p>
        </Card>
      </div>

      {/* Main Workflow Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Active Patient Interaction */}
        <div className="lg:col-span-1 space-y-6">
          {/* Active Call / Active Consultation Card */}
          {inConsultationPatient ? (
            <Card className="border-indigo-300 shadow-md bg-gradient-to-br from-white to-indigo-50/40">
              <CardHeader className="flex flex-row items-center justify-between border-indigo-100">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-800 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-ping" />
                  Active Consultation
                </span>
                <StatusBadge status="IN_CONSULTATION" />
              </CardHeader>

              <CardContent className="space-y-4 pt-4">
                <div className="p-4 bg-white rounded-xl border border-indigo-100 text-center space-y-1">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    Patient Token
                  </span>
                  <div className="text-4xl font-black text-indigo-800">
                    {inConsultationPatient.token_number || inConsultationPatient.ticket_number}
                  </div>
                  <div className="text-base font-bold text-slate-800">
                    {inConsultationPatient.patient_name}
                  </div>
                  {inConsultationPatient.reason && (
                    <p className="text-xs text-slate-500 italic mt-1">
                      "{inConsultationPatient.reason}"
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="notes" className="block text-xs font-medium text-slate-700 mb-1">
                    Consultation Summary & Notes (Optional)
                  </label>
                  <textarea
                    id="notes"
                    rows={3}
                    value={consultationNotes}
                    onChange={(e) => setConsultationNotes(e.target.value)}
                    placeholder="Enter diagnosis, prescription notes, or follow-up advice..."
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <Button
                  variant="primary"
                  size="md"
                  onClick={() => handleCompleteConsultation(inConsultationPatient.id)}
                  isLoading={isActionLoading}
                  className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <Check className="w-4 h-4" /> Complete Consultation
                </Button>
              </CardContent>
            </Card>
          ) : calledPatient ? (
            <Card className="border-sky-300 shadow-md bg-gradient-to-br from-white to-sky-50/40">
              <CardHeader className="flex flex-row items-center justify-between border-sky-100">
                <span className="text-xs font-bold uppercase tracking-wider text-sky-800 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-600 animate-ping" />
                  Patient Called
                </span>
                <StatusBadge status="CALLED" />
              </CardHeader>

              <CardContent className="space-y-4 pt-4">
                <div className="p-4 bg-white rounded-xl border border-sky-100 text-center space-y-1">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    Awaiting Entry
                  </span>
                  <div className="text-4xl font-black text-sky-700">
                    {calledPatient.token_number || calledPatient.ticket_number}
                  </div>
                  <div className="text-base font-bold text-slate-800">
                    {calledPatient.patient_name}
                  </div>
                  <p className="text-xs text-slate-500">
                    Called at: {formatDateTime(calledPatient.called_at)}
                  </p>
                  {calledPatient.reason && (
                    <p className="text-xs text-slate-500 italic mt-1">"{calledPatient.reason}"</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Button
                    variant="primary"
                    size="md"
                    onClick={() => handleStartConsultation(calledPatient.id)}
                    isLoading={isActionLoading}
                    className="w-full gap-2 bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Play className="w-4 h-4" /> Start Consultation
                  </Button>

                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleMarkNoShow(calledPatient.id)}
                    isLoading={isActionLoading}
                    className="w-full gap-1.5"
                  >
                    <UserX className="w-4 h-4" /> Mark No-Show
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed border-2 text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
                <PhoneCall className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Room Ready for Next Patient</h3>
                <p className="text-xs text-slate-500 mt-1">
                  {waitingList.length > 0
                    ? `${waitingList.length} patient(s) waiting in queue.`
                    : 'No patients waiting in queue.'}
                </p>
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={handleCallNext}
                isLoading={isActionLoading}
                disabled={waitingList.length === 0}
                className="w-full gap-2 shadow-sm"
              >
                <PhoneCall className="w-5 h-5" /> Call Next Patient
              </Button>
            </Card>
          )}
        </div>

        {/* Right Column: Waiting Queue List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-sky-600" />
              Waiting Patients ({waitingList.length})
            </h2>
            <span className="text-xs text-slate-500">Ordered by arrival time (FIFO)</span>
          </div>

          {waitingList.length === 0 ? (
            <Card className="p-8 text-center text-slate-400">
              <p className="text-sm">No patients currently waiting in your clinic queue.</p>
            </Card>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="divide-y divide-slate-100">
                {waitingList.map((ticket, index) => (
                  <div
                    key={ticket.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 font-bold text-xs text-slate-700 flex items-center justify-center shrink-0">
                        #{index + 1}
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-sm text-sky-700">
                            {ticket.token_number || ticket.ticket_number}
                          </span>
                          <span className="font-semibold text-sm text-slate-900">
                            {ticket.patient_name}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">
                          Joined: {formatDateTime(ticket.joined_at || ticket.created_at)}
                          {ticket.reason && (
                            <span className="italic ml-2 text-slate-600">"{ticket.reason}"</span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <StatusBadge status={ticket.status} />
                      {!calledPatient && !inConsultationPatient && index === 0 && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={handleCallNext}
                          isLoading={isActionLoading}
                          className="gap-1 text-xs"
                        >
                          <PhoneCall className="w-3.5 h-3.5" /> Call Now
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
