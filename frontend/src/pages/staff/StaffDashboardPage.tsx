import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { QueueTicket, Department, QueueStatus } from '../../types';
import { queueService } from '../../services/queueService';
import { departmentService } from '../../services/departmentService';
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
  Filter,
  Stethoscope,
  Loader2,
} from 'lucide-react';

export const StaffDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [tickets, setTickets] = useState<QueueTicket[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchQueues = useCallback(async () => {
    try {
      const data = await queueService.getStaffQueues(
        selectedDeptId || undefined,
        selectedStatus || undefined
      );
      setTickets(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch staff queue list.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedDeptId, selectedStatus]);

  useEffect(() => {
    departmentService
      .getDepartments()
      .then(setDepartments)
      .catch((err) => console.error('Failed to load departments', err));
  }, []);

  useEffect(() => {
    fetchQueues();
    const interval = setInterval(fetchQueues, 10000);
    return () => clearInterval(interval);
  }, [fetchQueues]);

  const handleStatusUpdate = async (queueId: string, newStatus: QueueStatus) => {
    setUpdatingId(queueId);
    try {
      await queueService.updateQueueStatus(queueId, { status: newStatus });
      await fetchQueues();
    } catch (err: any) {
      setError(err.message || `Failed to update status to ${newStatus}`);
    } finally {
      setUpdatingId(null);
    }
  };

  // Metrics calculation
  const waitingCount = tickets.filter((t) => t.status === 'waiting').length;
  const inConsultationCount = tickets.filter((t) => t.status === 'in_consultation').length;
  const completedCount = tickets.filter((t) => t.status === 'completed').length;

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hospital Staff Queue Portal</h1>
            <p className="text-sm text-slate-500">
              Welcome {user?.name} &bull; Manage patient consultations and queue flow in real time
            </p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={fetchQueues} className="gap-1.5 self-start sm:self-auto">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh List
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Card className="bg-amber-50/50 border-amber-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-amber-700 uppercase">Currently Waiting</span>
              <div className="text-3xl font-black text-amber-900 mt-1">{waitingCount}</div>
            </div>
            <Users className="w-8 h-8 text-amber-500/80" />
          </CardContent>
        </Card>

        <Card className="bg-sky-50/50 border-sky-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-sky-700 uppercase">In Consultation</span>
              <div className="text-3xl font-black text-sky-900 mt-1">{inConsultationCount}</div>
            </div>
            <Clock className="w-8 h-8 text-sky-500/80" />
          </CardContent>
        </Card>

        <Card className="bg-emerald-50/50 border-emerald-200">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-emerald-700 uppercase">Completed</span>
              <div className="text-3xl font-black text-emerald-900 mt-1">{completedCount}</div>
            </div>
            <CheckCircle className="w-8 h-8 text-emerald-500/80" />
          </CardContent>
        </Card>
      </div>

      {/* Filters and Table Section */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <h3 className="font-bold text-slate-900">Active Patient Queues</h3>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Department filter */}
            <select
              value={selectedDeptId}
              onChange={(e) => setSelectedDeptId(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>

            {/* Status filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="">All Statuses</option>
              <option value="waiting">Waiting</option>
              <option value="in_consultation">In Consultation</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="no_show">No Show</option>
            </select>
          </div>
        </CardHeader>

        <CardContent className="p-0 overflow-x-auto">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400 text-sm gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-sky-600" />
              <span>Loading department queues...</span>
            </div>
          ) : tickets.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-sm">
              No queue tickets found matching the selected filters.
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Ticket #</th>
                  <th className="px-6 py-3 font-semibold">Patient Name</th>
                  <th className="px-6 py-3 font-semibold">Department</th>
                  <th className="px-6 py-3 font-semibold">Arrival Time</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tickets.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-sky-700">
                      {t.ticket_number}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{t.patient_name}</div>
                      {t.reason && <div className="text-xs text-slate-500 italic max-w-xs truncate">{t.reason}</div>}
                    </td>
                    <td className="px-6 py-4 text-slate-600 text-xs">
                      {t.department_name} ({t.department_code})
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-xs">
                      {formatDateTime(t.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {t.status === 'waiting' && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleStatusUpdate(t.id, 'in_consultation')}
                            isLoading={updatingId === t.id}
                            className="gap-1 text-xs py-1 px-2.5"
                          >
                            <PhoneCall className="w-3.5 h-3.5" /> Call In
                          </Button>
                        )}

                        {t.status === 'in_consultation' && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleStatusUpdate(t.id, 'completed')}
                            isLoading={updatingId === t.id}
                            className="gap-1 text-xs py-1 px-2.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-800"
                          >
                            <Check className="w-3.5 h-3.5" /> Finish
                          </Button>
                        )}

                        {(t.status === 'waiting' || t.status === 'in_consultation') && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleStatusUpdate(t.id, 'no_show')}
                            isLoading={updatingId === t.id}
                            className="gap-1 text-xs py-1 px-2 text-rose-600 hover:bg-rose-50"
                            title="Mark No Show"
                          >
                            <UserX className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
