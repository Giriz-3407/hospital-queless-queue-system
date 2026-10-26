import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { QueueTicket } from '../../types';
import { queueService } from '../../services/queueService';
import { formatWaitTime, formatDateTime, getOrdinalSuffix } from '../../utils/formatters';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Alert } from '../../components/ui/Alert';
import { ArrowLeft, Ticket, RefreshCw, XCircle, Loader2 } from 'lucide-react';

export const MyQueuePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<QueueTicket | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);

  const fetchTicket = async () => {
    if (!id) return;
    try {
      const data = await queueService.getQueueById(id);
      setTicket(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve queue ticket.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();
    const interval = setInterval(fetchTicket, 10000);
    return () => clearInterval(interval);
  }, [id]);

  const handleCancel = async () => {
    if (!ticket || !window.confirm('Are you sure you want to cancel this ticket?')) return;
    setIsCancelling(true);
    try {
      await queueService.cancelQueue(ticket.id);
      await fetchTicket();
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

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/patient/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <Button variant="outline" size="sm" onClick={fetchTicket} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Live
        </Button>
      </div>

      <Card className="border-sky-200 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <span className="text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100">
              {ticket.department_code}
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-1">{ticket.department_name}</h2>
          </div>
          <StatusBadge status={ticket.status} />
        </CardHeader>

        <CardContent className="space-y-6 text-center">
          {/* Big Ticket Display */}
          <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              Queue Ticket Number
            </span>
            <div className="text-5xl font-black text-sky-700 tracking-tight flex items-center justify-center gap-3">
              <Ticket className="w-10 h-10 text-sky-500" />
              {ticket.ticket_number}
            </div>
            <p className="text-xs text-slate-500 pt-2">Patient: {ticket.patient_name}</p>
          </div>

          {/* Position & Wait Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-xs text-slate-500 font-medium">Position</span>
              <div className="text-2xl font-extrabold text-slate-900">
                {ticket.live_position > 0 ? getOrdinalSuffix(ticket.live_position) : '-'}
              </div>
              <p className="text-[11px] text-slate-500">
                {ticket.live_position > 1 ? `${ticket.live_position - 1} ahead` : 'Next in line!'}
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-xs text-slate-500 font-medium">Est. Wait</span>
              <div className="text-2xl font-extrabold text-sky-600">
                {formatWaitTime(ticket.live_estimated_wait_minutes)}
              </div>
              <p className="text-[11px] text-slate-500">
                Serving: <strong>{ticket.currently_serving_ticket || 'None'}</strong>
              </p>
            </div>
          </div>

          {ticket.reason && (
            <div className="text-left text-xs bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-600">
              <strong>Notes:</strong> {ticket.reason}
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Created: {formatDateTime(ticket.created_at)}</span>

            {ticket.status === 'waiting' && (
              <Button
                variant="danger"
                size="sm"
                onClick={handleCancel}
                isLoading={isCancelling}
                className="gap-1.5"
              >
                <XCircle className="w-4 h-4" /> Cancel Ticket
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
