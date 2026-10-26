import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useQueue } from '../../hooks/useQueue';
import { queueService } from '../../services/queueService';
import { formatWaitTime, formatDateTime, getOrdinalSuffix } from '../../utils/formatters';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Alert } from '../../components/ui/Alert';
import {
  Clock,
  PlusCircle,
  XCircle,
  RefreshCw,
  Ticket,
} from 'lucide-react';

export const PatientDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { queues, activeTicket, error, refresh } = useQueue(10000);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleCancelTicket = async (ticketId: string) => {
    if (!window.confirm('Are you sure you want to cancel your queue ticket?')) return;
    setActionError(null);
    setCancellingId(ticketId);
    try {
      await queueService.cancelQueue(ticketId);
      await refresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to cancel queue ticket.');
    } finally {
      setCancellingId(null);
    }
  };

  const pastTickets = queues.filter(
    (q) => q.status === 'completed' || q.status === 'cancelled' || q.status === 'no_show'
  );

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome, {user?.name || 'Patient'}</h1>
          <p className="text-sm text-slate-500">Live virtual queue tracking & hospital appointments</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => refresh()} className="gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </Button>
          {!activeTicket && (
            <Link to="/patient/join">
              <Button size="sm" className="gap-1.5 shadow-sm">
                <PlusCircle className="w-4 h-4" /> Join a Queue
              </Button>
            </Link>
          )}
        </div>
      </div>

      {actionError && <Alert variant="error">{actionError}</Alert>}
      {error && <Alert variant="error">{error}</Alert>}

      {/* Active Ticket Card (Hero) */}
      {activeTicket ? (
        <Card className="border-sky-200 bg-gradient-to-br from-white to-sky-50/50 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between border-sky-100">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-xs font-bold uppercase tracking-wider text-sky-800">
                Active Live Queue Ticket
              </span>
            </div>
            <StatusBadge status={activeTicket.status} />
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              {/* Ticket identifier */}
              <div className="space-y-1">
                <span className="text-xs text-slate-500 font-medium">Ticket Number</span>
                <div className="text-4xl font-black text-sky-700 tracking-tight flex items-center gap-2">
                  <Ticket className="w-8 h-8 text-sky-500" />
                  {activeTicket.ticket_number}
                </div>
                <p className="text-sm font-semibold text-slate-800">{activeTicket.department_name}</p>
                {activeTicket.reason && (
                  <p className="text-xs text-slate-500 italic">"{activeTicket.reason}"</p>
                )}
              </div>

              {/* Real-time Position */}
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center space-y-1">
                <span className="text-xs text-slate-500 font-medium">Your Position</span>
                <div className="text-3xl font-extrabold text-slate-900">
                  {activeTicket.live_position > 0 ? getOrdinalSuffix(activeTicket.live_position) : 'Serving Now'}
                </div>
                <p className="text-xs text-slate-500">
                  {activeTicket.live_position > 1
                    ? `${activeTicket.live_position - 1} patient(s) ahead of you`
                    : activeTicket.live_position === 1
                    ? 'You are next in line!'
                    : 'Please enter the consultation room'}
                </p>
              </div>

              {/* Real-time Estimated wait time */}
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center space-y-1">
                <span className="text-xs text-slate-500 font-medium flex items-center justify-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-sky-600" /> Estimated Wait Time
                </span>
                <div className="text-3xl font-extrabold text-sky-600">
                  {formatWaitTime(activeTicket.live_estimated_wait_minutes)}
                </div>
                <p className="text-xs text-slate-500">
                  Currently Serving:{' '}
                  <strong className="text-slate-800">
                    {activeTicket.currently_serving_ticket || 'None'}
                  </strong>
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-sky-100 text-xs text-slate-500">
              <span>Joined at: {formatDateTime(activeTicket.created_at)}</span>

              {activeTicket.status === 'waiting' && (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleCancelTicket(activeTicket.id)}
                  isLoading={cancellingId === activeTicket.id}
                  className="gap-1"
                >
                  <XCircle className="w-4 h-4" /> Cancel My Ticket
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="text-center p-8 border-dashed border-2">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
              <Ticket className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">You are not in any virtual queue</h3>
            <p className="text-sm text-slate-500">
              Need to see a doctor? Join the virtual queue now and relax anywhere until your turn is near.
            </p>
            <Link to="/patient/join" className="inline-block">
              <Button size="md" className="gap-2">
                <PlusCircle className="w-4 h-4" /> Join Virtual Queue
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* Past Queue History */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Your Queue History</h2>
        {pastTickets.length === 0 ? (
          <p className="text-sm text-slate-500">No previous queue history found.</p>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-100">
              {pastTickets.map((ticket) => (
                <div key={ticket.id} className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900">{ticket.ticket_number}</span>
                      <span className="text-xs text-slate-500">&bull; {ticket.department_name}</span>
                    </div>
                    <p className="text-xs text-slate-400">Date: {formatDateTime(ticket.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={ticket.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
