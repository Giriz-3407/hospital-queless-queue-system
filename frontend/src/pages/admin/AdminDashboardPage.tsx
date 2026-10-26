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
import {
  ShieldAlert,
  Users,
  Stethoscope,
  Building2,
  ListOrdered,
  History,
  PlusCircle,
  RefreshCw,
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'departments' | 'doctors' | 'queues' | 'audit' | 'users'>('departments');

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
  }, [activeTab, fetchDepartments, fetchDoctors, fetchQueues, fetchAuditLogs, fetchUsers]);

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
    </div>
  );
};
