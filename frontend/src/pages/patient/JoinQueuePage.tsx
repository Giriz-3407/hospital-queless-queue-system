import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Department } from '../../types';
import { departmentService } from '../../services/departmentService';
import { queueService } from '../../services/queueService';
import { formatWaitTime } from '../../utils/formatters';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Alert } from '../../components/ui/Alert';
import { ArrowLeft, Clock, Users, Ticket, Stethoscope } from 'lucide-react';

export const JoinQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [isLoadingDepartments, setIsLoadingDepartments] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    departmentService
      .getDepartments()
      .then((data) => {
        setDepartments(data);
        if (data.length > 0) {
          setSelectedDeptId(data[0].id);
        }
      })
      .catch((err) => setError(err.message || 'Failed to load hospital departments'))
      .finally(() => setIsLoadingDepartments(false));
  }, []);

  const selectedDept = departments.find((d) => d.id === selectedDeptId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeptId) {
      setError('Please select a department to proceed.');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await queueService.joinQueue({
        department_id: selectedDeptId,
        reason: reason.trim() || undefined,
      });
      navigate('/patient/dashboard');
    } catch (err: any) {
      setError(err.message || 'Could not join virtual queue.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/patient/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Join a Virtual Queue</h1>
        <p className="text-sm text-slate-500">
          Select a hospital department to receive your digital ticket and track your turn in real time.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6 pt-6">
            {/* Department selection */}
            <div>
              <Select
                label="Select Department / Specialty Clinic"
                value={selectedDeptId}
                onChange={(e) => setSelectedDeptId(e.target.value)}
                options={departments.map((d) => ({
                  value: d.id,
                  label: `${d.name} (${d.code})`,
                }))}
                disabled={isLoadingDepartments || departments.length === 0}
              />
            </div>

            {/* Department live status preview */}
            {selectedDept && (
              <div className="p-4 rounded-xl bg-sky-50/70 border border-sky-100 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">
                    Live Department Status
                  </span>
                  <span className="text-xs text-sky-600 font-medium">
                    Avg Consultation: {selectedDept.avg_consultation_time} mins
                  </span>
                </div>

                {selectedDept.description && (
                  <p className="text-xs text-slate-600">{selectedDept.description}</p>
                )}

                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-sky-100 text-xs">
                  <div className="flex items-center gap-2 text-slate-700">
                    <Users className="w-4 h-4 text-sky-600" />
                    <span>Patients waiting: <strong>{selectedDept.current_waiting ?? 0}</strong></span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-700">
                    <Clock className="w-4 h-4 text-sky-600" />
                    <span>Est. Wait: <strong>{formatWaitTime(selectedDept.estimated_wait_minutes)}</strong></span>
                  </div>
                </div>

                {/* Assigned Doctors */}
                {selectedDept.doctors && selectedDept.doctors.length > 0 && (
                  <div className="pt-2 border-t border-sky-100 text-xs">
                    <span className="text-slate-500 font-medium flex items-center gap-1 mb-1">
                      <Stethoscope className="w-3.5 h-3.5 text-sky-600" /> Medical Providers on Duty:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedDept.doctors.map((doc) => (
                        <span
                          key={doc.id}
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium ${
                            doc.is_available
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${doc.is_available ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                          {doc.display_name} {doc.specialty ? `(${doc.specialty})` : ''}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Reason / Symptoms input */}
            <div>
              <label htmlFor="reason" className="block text-sm font-medium text-slate-700 mb-1.5">
                Reason for Visit / Symptoms (Optional)
              </label>
              <textarea
                id="reason"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Briefly describe your symptoms or reason for visit (e.g. Mild headache and fever since yesterday)..."
                className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 placeholder-slate-400"
                maxLength={500}
              />
              <span className="text-xs text-slate-400">Max 500 characters</span>
            </div>

            <Button
              type="submit"
              size="lg"
              isLoading={isSubmitting}
              disabled={isLoadingDepartments || !selectedDeptId}
              className="w-full gap-2 shadow-sm"
            >
              <Ticket className="w-5 h-5" /> Generate Digital Queue Ticket
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
};
