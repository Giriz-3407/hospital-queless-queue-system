import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { QueueTicket } from '../../types';
import { queueService } from '../../services/queueService';
import { formatWaitTime, getOrdinalSuffix } from '../../utils/formatters';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Alert } from '../../components/ui/Alert';
import { ArrowLeft, RefreshCw, XCircle, Loader2, UserCheck, Clock, Users } from 'lucide-react';

export const MyQueuePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<QueueTicket | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const isVisibleRef = useRef<boolean>(true);

  const fetchTicket = useCallback(async (isBackground: boolean = false) => {
    if (!id) return;
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;

    try {
      if (!isBackground) setIsLoading(ticket ? false : true);
      const data = await queueService.getQueueById(id);
      setTicket(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve queue ticket.');
    } finally {
      setIsLoading(false);
    }
  }, [id, ticket]);

  useEffect(() => {
    fetchTicket(false);

    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isVisibleRef.current = isVisible;
      if (isVisible) fetchTicket(true);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    const interval = setInterval(() => {
      if (isVisibleRef.current) fetchTicket(true);
    }, 10000);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      clearInterval(interval);
    };
  }, [fetchTicket]);

  const handleCancel = async () => {
    if (!ticket || !window.confirm('Are you sure you want to cancel this ticket?')) return;
    setIsCancelling(true);
    try {
      await queueService.cancelQueue(ticket.id);
      await fetchTicket(false);
    } catch (err: any) {
      setError(err.message || 'Failed to cancel ticket.');
    } finally {
      setIsCancelling(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 text-sky-600 animate-spin" />
        <p className="text-sm text-slate-500">Loading queue position...</p>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-xl mx-auto space-y-4">
        <Alert variant="error">{error || 'Ticket not found.'}</Alert>
        <Link to="/patient/dashboard">
          <Button variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" /> Return to Dashboard
          </Button>
        </Link>
      </div>
    );
  }

  const statusUpper = (ticket.status || '').toUpperCase();
  const patientsAhead = ticket.patients_ahead ?? (ticket.live_position ? Math.max(0, ticket.live_position - 1) : 0);

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/patient/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <Button variant="outline" size="sm" onClick={() => fetchTicket(false)} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Live
        </Button>
      </div>

      <Card className="border-sky-300 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <span className="text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100">
              {ticket.department_code}
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-1">{ticket.department_name}</h2>
          </div>
          <StatusBadge status={ticket.status} size="md" />
        </CardHeader>

        <CardContent className="space-y-6 text-center">
          {/* Big Ticket Display */}
          <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              Queue Ticket Number
            </span>
            <div className="text-5xl font-black text-sky-700 tracking-tight">
              {ticket.token_number || ticket.ticket_number}
            </div>
            {ticket.doctor_name && (
              <p className="text-xs font-medium text-sky-600 flex items-center justify-center gap-1 pt-1">
                <UserCheck className="w-3.5 h-3.5" /> Assigned Doctor: {ticket.doctor_name}
              </p>
            )}
            {ticket.reason && (
              <p className="text-xs text-slate-500 italic mt-2">"{ticket.reason}"</p>
            )}
          </div>

          {/* Real-time stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-xs text-slate-500 font-medium flex items-center justify-center gap-1">
                <Users className="w-3.5 h-3.5 text-sky-600" /> Queue Position
              </span>
              <div className="text-2xl font-black text-slate-900">
                {statusUpper === 'CALLED' ? (
                  <span className="text-sky-600 animate-pulse text-xl">Called!</span>
                ) : statusUpper === 'IN_CONSULTATION' ? (
                  <span className="text-indigo-600 text-xl">In Room</span>
                ) : ticket.live_position > 0 ? (
                  getOrdinalSuffix(ticket.live_position)
                ) : (
                  '-'
                )}
              </div>
              <p className="text-[11px] text-slate-400">
                {statusUpper === 'WAITING' ? `${patientsAhead} patient(s) ahead` : 'Status updated'}
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-xs text-slate-500 font-medium flex items-center justify-center gap-1">
                <Clock className="w-3.5 h-3.5 text-sky-600" /> Estimated Wait
              </span>
              <div className="text-2xl font-black text-sky-600">
                {formatWaitTime(ticket.live_estimated_wait_minutes)}
              </div>
              <p className="text-[11px] text-slate-400">Dynamic live update</p>
            </div>
          </div>

          {/* Action buttons */}
          {statusUpper === 'WAITING' && (
            <div className="pt-2">
              <Button
                variant="danger"
                size="md"
                onClick={handleCancel}
                isLoading={isCancelling}
                className="w-full gap-2"
              >
                <XCircle className="w-4 h-4" /> Cancel Queue Entry
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
