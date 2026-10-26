import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { AdminDashboardStats, Department, Doctor, QueueTicket, AuditLog, User } from '../../types';
import { adminService, CreateDoctorPayload, CreateDepartmentPayload } from '../../services/adminService';
import { departmentService } from '../../services/departmentService';
import { formatDateTime } from '../../utils/formatters';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { QRCodeCanvas } from 'qrcode.react';
import {
  ShieldAlert,
  Users,
  Stethoscope,
  Building2,
  ListOrdered,
  History,
  PlusCircle,
  RefreshCw,
  QrCode,
  Download,
  Printer,
  Copy,
  Check,
  ExternalLink,
  UserPlus,
  Ticket,
  Info,
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'departments' | 'doctors' | 'queues' | 'audit' | 'users' | 'qr-codes' | 'walk-in'>('departments');

  // Stats
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Departments State
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isDeptModalOpen, setIsDeptModalOpen] = useState<boolean>(false);
  const [deptForm, setDeptForm] = useState<CreateDepartmentPayload>({
    name: '',
    code: '',
    description: '',
    avg_consultation_time: 15,
  });

  // Doctors State
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [isDoctorModalOpen, setIsDoctorModalOpen] = useState<boolean>(false);
  const [doctorForm, setDoctorForm] = useState<CreateDoctorPayload>({
    name: '',
    email: '',
    password: '',
    department_id: '',
    specialty: '',
    phone: '',
  });

  // Queues State
  const [queues, setQueues] = useState<QueueTicket[]>([]);
  const [queueFilterDept, setQueueFilterDept] = useState<string>('');
  const [queueFilterStatus, setQueueFilterStatus] = useState<string>('');

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  // Users State
  const [usersList, setUsersList] = useState<User[]>([]);

  // QR Codes State
  const [qrBaseUrl, setQrBaseUrl] = useState<string>('https://httpbin.org/anything');
  const [isQrLoading, setIsQrLoading] = useState<boolean>(false);
  const [copiedSlug, setCopiedSlug] = useState<string | null>(null);
  const [selectedPlacardDept, setSelectedPlacardDept] = useState<Department | null>(null);

  // Walk-In Patient State
  const [walkInForm, setWalkInForm] = useState<{
    department_id: string;
    patient_name: string;
    phone: string;
    age: string;
    reason: string;
  }>({
    department_id: '',
    patient_name: '',
    phone: '',
    age: '',
    reason: '',
  });
  const [walkInTicket, setWalkInTicket] = useState<QueueTicket | null>(null);
  const [isWalkInSubmitting, setIsWalkInSubmitting] = useState<boolean>(false);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Load Dashboard Overview Stats
  const fetchStats = useCallback(async () => {
    try {
      const data = await adminService.getDashboardStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load admin stats', err);
    }
  }, []);

  // Fetch Departments
  const fetchDepartments = useCallback(async () => {
    try {
      const data = await departmentService.getDepartments();
      setDepartments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load departments');
    }
  }, []);

  // Fetch Doctors
  const fetchDoctors = useCallback(async () => {
    try {
      const data = await adminService.getDoctors();
      setDoctors(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load doctors');
    }
  }, []);

  // Fetch Queues
  const fetchQueues = useCallback(async () => {
    try {
      const res = await adminService.getQueues(queueFilterDept || undefined, queueFilterStatus || undefined);
      setQueues(res.queues);
    } catch (err: any) {
      setError(err.message || 'Failed to load queues');
    }
  }, [queueFilterDept, queueFilterStatus]);

  // Fetch Audit Logs
  const fetchAuditLogs = useCallback(async () => {
    try {
      const res = await adminService.getAuditLogs();
      setAuditLogs(res.logs);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs');
    }
  }, []);

  // Fetch Users
  const fetchUsers = useCallback(async () => {
    try {
      const res = await adminService.getUsers();
      setUsersList(res.users);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    }
  }, []);

  // Fetch QR Code Config & Department List
  const fetchQrConfig = useCallback(async (customBaseUrl?: string) => {
    setIsQrLoading(true);
    try {
      const data = await adminService.getQrConfig(customBaseUrl);
      if (!customBaseUrl) {
        setQrBaseUrl(data.qr_public_base_url);
      }
    } catch (err: any) {
      console.error('Failed to load QR configurations', err);
    } finally {
      setIsQrLoading(false);
    }
  }, []);

  const downloadQrCode = (slug: string, _deptName?: string) => {
    const canvas = document.getElementById(`qr-canvas-${slug}`) as HTMLCanvasElement;
    if (!canvas) return;
    const pngUrl = canvas.toDataURL('image/png');
    const downloadLink = document.createElement('a');
    downloadLink.href = pngUrl;
    downloadLink.download = `queueless-${slug}-qr.png`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  };

  const copyQrUrl = (url: string, slug: string) => {
    navigator.clipboard.writeText(url);
    setCopiedSlug(slug);
    setTimeout(() => setCopiedSlug(null), 2000);
  };

  const handleRegisterWalkIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!walkInForm.department_id || !walkInForm.patient_name.trim()) {
      setError('Please select a clinical department and enter patient name.');
      return;
    }

    setIsWalkInSubmitting(true);
    setError(null);

    try {
      const ticket = await adminService.registerWalkIn({
        department_id: walkInForm.department_id,
        patient_name: walkInForm.patient_name.trim(),
        phone: walkInForm.phone.trim() || undefined,
        age: walkInForm.age ? parseInt(walkInForm.age) : undefined,
        reason: walkInForm.reason.trim() || undefined,
      });

      setWalkInTicket(ticket);
      setSuccessMsg(`Walk-in ticket ${ticket.token_number} issued for ${ticket.patient_name}!`);
      // Reset walk-in input fields
      setWalkInForm((prev) => ({
        ...prev,
        patient_name: '',
        phone: '',
        age: '',
        reason: '',
      }));
      await fetchStats();
      await fetchQueues();
    } catch (err: any) {
      setError(err.message || 'Failed to register walk-in patient.');
    } finally {
      setIsWalkInSubmitting(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDepartments();
  }, [fetchStats, fetchDepartments]);

  useEffect(() => {
    if (activeTab === 'departments') fetchDepartments();
    else if (activeTab === 'doctors') {
      fetchDoctors();
      fetchDepartments();
    } else if (activeTab === 'queues') fetchQueues();
    else if (activeTab === 'audit') fetchAuditLogs();
    else if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'qr-codes') {
      fetchQrConfig(qrBaseUrl);
      fetchDepartments();
    } else if (activeTab === 'walk-in') {
      fetchDepartments();
    }
  }, [activeTab, fetchDepartments, fetchDoctors, fetchQueues, fetchAuditLogs, fetchUsers, fetchQrConfig, qrBaseUrl]);

  // Handlers for Departments
  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await adminService.createDepartment(deptForm);
      setSuccessMsg('Department created successfully!');
      setIsDeptModalOpen(false);
      setDeptForm({ name: '', code: '', description: '', avg_consultation_time: 15 });
      await fetchDepartments();
      await fetchStats();
    } catch (err: any) {
      setError(err.message || 'Failed to create department.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleDepartmentActive = async (dept: Department) => {
    try {
      await adminService.updateDepartment(dept.id, { is_active: !dept.is_active });
      await fetchDepartments();
      await fetchStats();
    } catch (err: any) {
      setError(err.message || 'Failed to update department status.');
    }
  };

  // Handlers for Doctors
  const handleCreateDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await adminService.createDoctor(doctorForm);
      setSuccessMsg('Doctor account created and assigned successfully!');
      setIsDoctorModalOpen(false);
      setDoctorForm({ name: '', email: '', password: '', department_id: '', specialty: '', phone: '' });
      await fetchDoctors();
      await fetchStats();
    } catch (err: any) {
      setError(err.message || 'Failed to create doctor account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleDoctorAvailability = async (doc: Doctor) => {
    try {
      await adminService.updateDoctor(doc.id, { is_available: !doc.is_available });
      await fetchDoctors();
      await fetchStats();
    } catch (err: any) {
      setError(err.message || 'Failed to update doctor availability.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hospital Administration</h1>
            <p className="text-sm text-slate-500">
              Logged in as {user?.name} &bull; Clinical departments, medical staff & audit management
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            fetchStats();
            if (activeTab === 'departments') fetchDepartments();
            if (activeTab === 'doctors') fetchDoctors();
            if (activeTab === 'queues') fetchQueues();
            if (activeTab === 'audit') fetchAuditLogs();
            if (activeTab === 'users') fetchUsers();
          }}
          className="gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Data
        </Button>
      </div>

      {error && <Alert variant="error">{error}</Alert>}
      {successMsg && (
        <Alert variant="success">
          <div className="flex items-center justify-between">
            <span>{successMsg}</span>
            <button onClick={() => setSuccessMsg(null)} className="text-xs font-semibold underline">
              Dismiss
            </button>
          </div>
        </Alert>
      )}

      {/* System Statistics Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4 bg-white border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Departments</span>
              <Building2 className="w-4 h-4 text-sky-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {stats.active_departments} <span className="text-xs font-normal text-slate-400">/ {stats.total_departments}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Active hospital clinics</p>
          </Card>

          <Card className="p-4 bg-white border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Doctors</span>
              <Stethoscope className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">{stats.total_doctors}</div>
            <p className="text-[11px] text-slate-400 mt-1">Active providers</p>
          </Card>

          <Card className="p-4 bg-white border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Active Queues</span>
              <ListOrdered className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-black text-amber-700 mt-2">{stats.active_tickets}</div>
            <p className="text-[11px] text-slate-400 mt-1">Patients waiting/serving</p>
          </Card>

          <Card className="p-4 bg-white border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium">Registered Patients</span>
              <Users className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">{stats.total_patients}</div>
            <p className="text-[11px] text-slate-400 mt-1">Total user accounts</p>
          </Card>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('departments')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'departments'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Building2 className="w-4 h-4" /> Departments ({departments.length})
        </button>

        <button
          onClick={() => setActiveTab('doctors')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'doctors'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Stethoscope className="w-4 h-4" /> Doctors ({doctors.length})
        </button>

        <button
          onClick={() => setActiveTab('queues')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'queues'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <ListOrdered className="w-4 h-4" /> Queues Monitor
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <History className="w-4 h-4" /> Audit Logs
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'users'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Users className="w-4 h-4" /> User Accounts
        </button>

        <button
          onClick={() => setActiveTab('qr-codes')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'qr-codes'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <QrCode className="w-4 h-4" /> Department QR Codes
        </button>

        <button
          onClick={() => setActiveTab('walk-in')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === 'walk-in'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <UserPlus className="w-4 h-4" /> Register Walk-in Patient
        </button>
      </div>

      {/* Tab 1: Departments Management */}
      {activeTab === 'departments' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Hospital Departments</h2>
            <Button
              size="sm"
              onClick={() => setIsDeptModalOpen(true)}
              className="gap-1.5 shadow-sm"
            >
              <PlusCircle className="w-4 h-4" /> Add Department
            </Button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Department Name</th>
                  <th className="py-3 px-4">Avg Duration</th>
                  <th className="py-3 px-4">Active Doctors</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.map((dept) => (
                  <tr key={dept.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-bold text-sky-700">{dept.code}</td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      <div>{dept.name}</div>
                      {dept.description && (
                        <div className="text-xs text-slate-400 truncate max-w-xs">{dept.description}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{dept.avg_consultation_time} mins</td>
                    <td className="py-3 px-4 text-slate-600">
                      {dept.available_doctors_count ?? 0} on duty
                    </td>
                    <td className="py-3 px-4">
                      {dept.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-600">
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleDepartmentActive(dept)}
                        className="text-xs"
                      >
                        {dept.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Doctors Management */}
      {activeTab === 'doctors' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Hospital Medical Providers</h2>
            <Button
              size="sm"
              onClick={() => setIsDoctorModalOpen(true)}
              className="gap-1.5 shadow-sm"
            >
              <PlusCircle className="w-4 h-4" /> Provision Doctor
            </Button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Doctor Name</th>
                  <th className="py-3 px-4">Login Email</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Specialty</th>
                  <th className="py-3 px-4">Availability</th>
                  <th className="py-3 px-4 text-right">Toggle On-Duty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {doctors.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-semibold text-slate-900">{doc.display_name}</td>
                    <td className="py-3 px-4 text-slate-600">{doc.user?.email || '-'}</td>
                    <td className="py-3 px-4 text-sky-700 font-medium">{doc.department_name || '-'}</td>
                    <td className="py-3 px-4 text-slate-600">{doc.specialty || '-'}</td>
                    <td className="py-3 px-4">
                      {doc.is_available ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                          Available / On-Duty
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-600">
                          Off Duty
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleDoctorAvailability(doc)}
                        className="text-xs"
                      >
                        {doc.is_available ? 'Set Off-Duty' : 'Set On-Duty'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Queues Monitor */}
      {activeTab === 'queues' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-slate-900">Hospital Queues Monitor</h2>

            <div className="flex items-center gap-3">
              <Select
                value={queueFilterDept}
                onChange={(e) => setQueueFilterDept(e.target.value)}
                options={[
                  { value: '', label: 'All Departments' },
                  ...departments.map((d) => ({ value: d.id, label: d.name })),
                ]}
              />

              <Select
                value={queueFilterStatus}
                onChange={(e) => setQueueFilterStatus(e.target.value)}
                options={[
                  { value: '', label: 'All Statuses' },
                  { value: 'WAITING', label: 'Waiting' },
                  { value: 'CALLED', label: 'Called' },
                  { value: 'IN_CONSULTATION', label: 'In Consultation' },
                  { value: 'COMPLETED', label: 'Completed' },
                  { value: 'CANCELLED', label: 'Cancelled' },
                  { value: 'NO_SHOW', label: 'No Show' },
                ]}
              />
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Ticket</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Joined At</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Attending Doctor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {queues.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No queue entries found matching the filter criteria.
                    </td>
                  </tr>
                ) : (
                  queues.map((q) => (
                    <tr key={q.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-black text-sky-700">
                        {q.token_number || q.ticket_number}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-900">{q.patient_name}</td>
                      <td className="py-3 px-4 text-slate-600">{q.department_name}</td>
                      <td className="py-3 px-4 text-slate-500 text-xs">
                        {formatDateTime(q.joined_at || q.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={q.status} />
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-600">
                        {q.doctor_name || '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <History className="w-5 h-5 text-purple-600" /> System Audit Trail
            </h2>
            <span className="text-xs text-slate-500">Security & Operational Activity Log</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-xs">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400 font-sans">
                      No audit logs recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 text-slate-500">{formatDateTime(log.timestamp)}</td>
                      <td className="py-3 px-4 font-bold text-purple-700">{log.action}</td>
                      <td className="py-3 px-4 font-sans text-slate-800">
                        {log.actor_name || 'System'} ({log.actor_role || 'system'})
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {log.entity_type} #{log.entity_id.slice(-6)}
                      </td>
                      <td className="py-3 px-4 text-slate-500 truncate max-w-xs font-sans">
                        {log.metadata ? JSON.stringify(log.metadata) : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: Users */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Registered Users</h2>
            <span className="text-xs text-slate-500">Total accounts: {usersList.length}</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Joined Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usersList.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-semibold text-slate-900">{u.name}</td>
                    <td className="py-3 px-4 text-slate-600">{u.email}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase bg-slate-100 text-slate-700">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">{formatDateTime(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 6: Department QR Codes */}
      {activeTab === 'qr-codes' && (
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-100 mb-2">
                <QrCode className="w-3.5 h-3.5" /> Physical Hospital Placards & App Links
              </div>
              <h2 className="text-xl font-bold text-slate-900">Department QR Codes</h2>
              <p className="text-sm text-slate-500 mt-1 max-w-2xl">
                Generate high-resolution scannable QR codes for every clinical department. When scanned, patients with the Android app open the department directly; other devices open the web fallback.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchQrConfig(qrBaseUrl)}
                isLoading={isQrLoading}
                className="gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh Codes
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => window.print()}
                className="gap-1.5 shadow-sm"
              >
                <Printer className="w-3.5 h-3.5" /> Print Placards
              </Button>
            </div>
          </div>

          {/* Centralized URL Configuration Box */}
          <Card className="p-5 bg-slate-50/70 border-slate-200">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Centralized Public QR Destination Base URL
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">
                    Single Source of Truth
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  QR codes encode <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">&lt;base_url&gt;/department/&lt;department-slug&gt;</code>. Change here to test or deploy to production.
                </p>
              </div>

              {/* Quick Presets */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-slate-500 mr-1 font-medium">Presets:</span>
                <button
                  type="button"
                  onClick={() => {
                    const u = 'https://httpbin.org/anything';
                    setQrBaseUrl(u);
                    fetchQrConfig(u);
                  }}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                    qrBaseUrl === 'https://httpbin.org/anything'
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm font-semibold'
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  Temporary Reachable Test (httpbin)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const u = 'http://localhost:5173';
                    setQrBaseUrl(u);
                    fetchQrConfig(u);
                  }}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                    qrBaseUrl === 'http://localhost:5173'
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm font-semibold'
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  Local Web Fallback (localhost:5173)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const u = 'https://queueless.hospital.org';
                    setQrBaseUrl(u);
                    fetchQrConfig(u);
                  }}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                    qrBaseUrl === 'https://queueless.hospital.org'
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm font-semibold'
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  Production Placeholder
                </button>
              </div>
            </div>

            <div className="mt-4 flex flex-col sm:flex-row items-center gap-2">
              <input
                type="url"
                value={qrBaseUrl}
                onChange={(e) => setQrBaseUrl(e.target.value)}
                placeholder="https://YOUR_DOMAIN.example"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono text-xs"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchQrConfig(qrBaseUrl)}
                className="whitespace-nowrap w-full sm:w-auto"
              >
                Regenerate QR Codes
              </Button>
            </div>

            {/* Explanatory Banner for Testing Mode */}
            {qrBaseUrl.includes('httpbin.org') && (
              <div className="mt-3 p-3 rounded-xl bg-sky-50 border border-sky-200 text-xs text-sky-900 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Temporary Testing Mode Active:</span> QR codes encode{' '}
                  <code>https://httpbin.org/anything/department/&lt;slug&gt;</code>. Scanning with a camera or QR reader will open this verified reachable destination and display the path/slug. Third-party testing sites do not collect patient data or invoke verified App Links until the hospital's registered domain is configured.
                </div>
              </div>
            )}
          </Card>

          {/* Department QR Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {departments.map((dept) => {
              const slug = dept.slug || dept.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
              const cleanBase = (qrBaseUrl || 'https://httpbin.org/anything').replace(/\/$/, '');
              const deptQrUrl = `${cleanBase}/department/${slug}`;

              return (
                <Card
                  key={dept.id}
                  className={`p-5 bg-white border flex flex-col justify-between transition-all ${
                    !dept.is_active ? 'opacity-85 border-amber-200 bg-amber-50/20' : 'border-slate-200 hover:shadow-md'
                  }`}
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-sky-600 bg-sky-50 px-2 py-0.5 rounded">
                            {dept.code}
                          </span>
                          {!dept.is_active && (
                            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                              Inactive
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 mt-1">{dept.name}</h3>
                      </div>
                      <span className="text-xs text-slate-400 font-mono">avg {dept.avg_consultation_time}m</span>
                    </div>

                    {/* QR Code Canvas */}
                    <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex flex-col items-center justify-center my-3">
                      <div className="bg-white p-3 rounded-xl shadow-sm border border-slate-200">
                        <QRCodeCanvas
                          id={`qr-canvas-${slug}`}
                          value={deptQrUrl}
                          size={175}
                          level="H"
                          includeMargin={true}
                        />
                      </div>
                      <span className="text-[11px] text-slate-500 font-medium mt-2">
                        Scan to Join {dept.name}
                      </span>
                    </div>

                    {/* Encoded URL Display */}
                    <div className="space-y-1 mt-2">
                      <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                        Encoded Destination URL
                      </label>
                      <div className="flex items-center gap-1.5 p-2 bg-slate-100/80 rounded-lg border border-slate-200 text-xs font-mono text-slate-700">
                        <span className="truncate flex-1">{deptQrUrl}</span>
                        <button
                          type="button"
                          onClick={() => copyQrUrl(deptQrUrl, slug)}
                          className="p-1 text-slate-500 hover:text-slate-800 transition-colors"
                          title="Copy Encoded URL"
                        >
                          {copiedSlug === slug ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <a
                          href={deptQrUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-slate-500 hover:text-sky-600 transition-colors"
                          title="Test Link in Browser"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 mt-3 border-t border-slate-100">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadQrCode(slug, dept.name)}
                      className="flex-1 gap-1.5 text-xs"
                    >
                      <Download className="w-3.5 h-3.5" /> Download PNG
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedPlacardDept(dept)}
                      className="gap-1.5 text-xs text-sky-600 hover:text-sky-700"
                    >
                      <Printer className="w-3.5 h-3.5" /> Placard Preview
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 7: Register Walk-In Patient */}
      {activeTab === 'walk-in' && (
        <div className="space-y-6 max-w-3xl mx-auto">
          {/* Header */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center flex-shrink-0">
              <UserPlus className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Reception-Assisted Walk-In Registration</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Register walk-in patients directly into clinical queues without requiring smartphone ownership or account credentials.
              </p>
            </div>
          </div>

          {/* Registration Form Card */}
          <Card className="p-6 bg-white border-slate-200 shadow-sm">
            <form onSubmit={handleRegisterWalkIn} className="space-y-5">
              <Select
                label="Target Clinical Department"
                required
                value={walkInForm.department_id}
                onChange={(e) => setWalkInForm({ ...walkInForm, department_id: e.target.value })}
                options={[
                  { value: '', label: 'Select Clinical Department...' },
                  ...departments
                    .filter((d) => d.is_active)
                    .map((d) => ({
                      value: d.id,
                      label: `${d.name} (${d.code}) — ~${d.avg_consultation_time} min avg`,
                    })),
                ]}
              />

              <Input
                label="Patient Full Legal Name"
                required
                value={walkInForm.patient_name}
                onChange={(e) => setWalkInForm({ ...walkInForm, patient_name: e.target.value })}
                placeholder="e.g. Eleanor Vance"
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Contact Phone Number (Optional)"
                  type="tel"
                  value={walkInForm.phone}
                  onChange={(e) => setWalkInForm({ ...walkInForm, phone: e.target.value })}
                  placeholder="e.g. +1-555-0199"
                  helperText="Enforces single active queue entry if provided"
                />

                <Input
                  label="Patient Age in Years (Optional)"
                  type="number"
                  min={0}
                  max={130}
                  value={walkInForm.age}
                  onChange={(e) => setWalkInForm({ ...walkInForm, age: e.target.value })}
                  placeholder="e.g. 45"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Reason for Visit / Chief Complaint (Optional)
                </label>
                <textarea
                  rows={2}
                  value={walkInForm.reason}
                  onChange={(e) => setWalkInForm({ ...walkInForm, reason: e.target.value })}
                  placeholder="Routine follow-up, acute chest pain, fever, dressing change..."
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              {/* Data Rules Callout */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
                <span className="font-semibold text-slate-800 block">Hospital Walk-In Policy:</span>
                <p>
                  &bull; No fake emails or passwords are created. The patient is issued an atomic sequential token using the existing queue engine.
                </p>
                <p>
                  &bull; If a phone number is entered, duplicate active ticket checks prevent multiple waiting slots across departments.
                </p>
                <p>
                  &bull; The ticket appears instantly on the attending physician's consultation console.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() =>
                    setWalkInForm({
                      department_id: '',
                      patient_name: '',
                      phone: '',
                      age: '',
                      reason: '',
                    })
                  }
                >
                  Clear Form
                </Button>
                <Button type="submit" isLoading={isWalkInSubmitting} className="gap-2 shadow-sm">
                  <Ticket className="w-4 h-4" /> Issue Walk-In Ticket
                </Button>
              </div>
            </form>
          </Card>

          {/* Recently Issued Walk-in Token Banner */}
          {walkInTicket && (
            <Card className="p-6 bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-200/80 px-2 py-0.5 rounded">
                      Walk-In Token Confirmed
                    </span>
                    <span className="text-xs text-emerald-700">{formatDateTime(walkInTicket.created_at)}</span>
                  </div>
                  <div className="text-3xl font-black text-emerald-950 font-mono tracking-tight mt-1">
                    {walkInTicket.token_number}
                  </div>
                  <p className="text-sm font-semibold text-emerald-900">
                    {walkInTicket.patient_name} &bull; {walkInTicket.department_name}
                  </p>
                  <p className="text-xs text-emerald-700">
                    Queue Position: <strong>#{walkInTicket.position}</strong> &bull; Est. Wait:{' '}
                    <strong>
                      {walkInTicket.estimated_wait_minutes !== null && walkInTicket.estimated_wait_minutes !== undefined
                        ? `~${walkInTicket.estimated_wait_minutes} min`
                        : 'Estimate pending'}
                    </strong>
                  </p>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.print()}
                    className="gap-1.5 bg-white text-emerald-800 border-emerald-300 hover:bg-emerald-50"
                  >
                    <Printer className="w-3.5 h-3.5" /> Print Patient Slip
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => setWalkInTicket(null)}
                    className="bg-emerald-700 hover:bg-emerald-800 text-white"
                  >
                    Done
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Modal: Add Department */}
      <Modal
        isOpen={isDeptModalOpen}
        onClose={() => setIsDeptModalOpen(false)}
        title="Add Hospital Department"
      >
        <form onSubmit={handleCreateDepartment} className="space-y-4">
          <Input
            label="Department Name"
            required
            value={deptForm.name}
            onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
            placeholder="e.g. Ophthalmology"
          />
          <Input
            label="Department Code"
            required
            value={deptForm.code}
            onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value.toUpperCase() })}
            placeholder="e.g. OPHTH"
            maxLength={10}
          />
          <Input
            label="Average Consultation Time (Minutes)"
            type="number"
            min={1}
            max={120}
            required
            value={deptForm.avg_consultation_time}
            onChange={(e) =>
              setDeptForm({ ...deptForm, avg_consultation_time: parseInt(e.target.value) || 15 })
            }
          />
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Description (Optional)</label>
            <textarea
              rows={2}
              value={deptForm.description}
              onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
              placeholder="Brief description of clinical services provided..."
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" type="button" onClick={() => setIsDeptModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              Create Department
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Provision Doctor */}
      <Modal
        isOpen={isDoctorModalOpen}
        onClose={() => setIsDoctorModalOpen(false)}
        title="Provision Doctor Account"
      >
        <form onSubmit={handleCreateDoctor} className="space-y-4">
          <Input
            label="Doctor Full Name"
            required
            value={doctorForm.name}
            onChange={(e) => setDoctorForm({ ...doctorForm, name: e.target.value })}
            placeholder="e.g. Marcus Vance"
          />
          <Input
            label="Email Address"
            type="email"
            required
            value={doctorForm.email}
            onChange={(e) => setDoctorForm({ ...doctorForm, email: e.target.value })}
            placeholder="doctor@hospital.org"
          />
          <Input
            label="Initial Password (min 8 characters)"
            type="password"
            required
            minLength={8}
            value={doctorForm.password}
            onChange={(e) => setDoctorForm({ ...doctorForm, password: e.target.value })}
            placeholder="••••••••"
          />
          <Select
            label="Assigned Department"
            required
            value={doctorForm.department_id}
            onChange={(e) => setDoctorForm({ ...doctorForm, department_id: e.target.value })}
            options={[
              { value: '', label: 'Select Department...' },
              ...departments.map((d) => ({ value: d.id, label: `${d.name} (${d.code})` })),
            ]}
          />
          <Input
            label="Clinical Specialty (Optional)"
            value={doctorForm.specialty || ''}
            onChange={(e) => setDoctorForm({ ...doctorForm, specialty: e.target.value })}
            placeholder="e.g. Interventional Cardiology"
          />
          <Input
            label="Contact Phone (Optional)"
            value={doctorForm.phone || ''}
            onChange={(e) => setDoctorForm({ ...doctorForm, phone: e.target.value })}
            placeholder="+1-555-0100"
          />

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="ghost" type="button" onClick={() => setIsDoctorModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              Provision Doctor
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Department QR Placard Preview & Print */}
      {selectedPlacardDept && (
        <Modal
          isOpen={!!selectedPlacardDept}
          onClose={() => setSelectedPlacardDept(null)}
          title={`Hospital Placard: ${selectedPlacardDept.name}`}
        >
          {(() => {
            const slug =
              selectedPlacardDept.slug ||
              selectedPlacardDept.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            const cleanBase = (qrBaseUrl || 'https://httpbin.org/anything').replace(/\/$/, '');
            const deptQrUrl = `${cleanBase}/department/${slug}`;

            return (
              <div className="space-y-6">
                {/* Printable Placard Container */}
                <div
                  id="printable-placard"
                  className="bg-white p-8 rounded-3xl border-2 border-slate-900 text-center shadow-md space-y-4 max-w-sm mx-auto"
                >
                  <div className="border-b-2 border-slate-900 pb-3">
                    <div className="text-[10px] font-black uppercase tracking-widest text-sky-700">
                      QUEUELess SMART HOSPITAL
                    </div>
                    <h3 className="text-2xl font-black text-slate-900 uppercase tracking-tight mt-0.5">
                      {selectedPlacardDept.name}
                    </h3>
                    <div className="inline-block mt-1 bg-slate-900 text-white font-mono text-xs font-bold px-3 py-0.5 rounded-full">
                      {selectedPlacardDept.code} CLINIC
                    </div>
                  </div>

                  <div className="py-2 flex justify-center">
                    <div className="p-3 bg-white border-2 border-slate-200 rounded-2xl shadow-inner">
                      <QRCodeCanvas
                        id={`placard-qr-${slug}`}
                        value={deptQrUrl}
                        size={220}
                        level="H"
                        includeMargin={true}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-left text-xs text-slate-700 space-y-1.5">
                    <div className="font-bold text-slate-900 text-center uppercase tracking-wider text-[11px]">
                      How to Join This Queue
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-bold text-sky-700">1.</span>
                      <span>Scan QR code with your mobile camera.</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-bold text-sky-700">2.</span>
                      <span>Open the Queueless link to enter the virtual line.</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-bold text-sky-700">3.</span>
                      <span>Track live position & return when called.</span>
                    </div>
                  </div>

                  <div className="pt-2 text-[10px] text-slate-400 font-mono truncate">
                    {deptQrUrl}
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => downloadQrCode(slug, selectedPlacardDept.name)}
                    className="gap-1.5 text-xs"
                  >
                    <Download className="w-4 h-4" /> Save PNG
                  </Button>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" onClick={() => setSelectedPlacardDept(null)}>
                      Close
                    </Button>
                    <Button variant="primary" onClick={() => window.print()} className="gap-1.5 shadow-sm">
                      <Printer className="w-4 h-4" /> Print Placard
                    </Button>
                  </div>
                </div>
              </div>
            );
          })()}
        </Modal>
      )}
    </div>
  );
};
