import { apiClient } from './api';
import { ApiResponse, AdminDashboardStats, AuditLog, Department, Doctor, QueueTicket, User } from '../types';

export interface CreateDoctorPayload {
  name: string;
  email: string;
  password: string;
  department_id: string;
  specialty?: string;
  phone?: string;
}

export interface UpdateDoctorPayload {
  department_id?: string;
  display_name?: string;
  specialty?: string;
  is_available?: boolean;
}

export interface CreateDepartmentPayload {
  name: string;
  code: string;
  description?: string;
  avg_consultation_time?: number;
  is_active?: boolean;
}

export interface UpdateDepartmentPayload {
  name?: string;
  code?: string;
  description?: string;
  avg_consultation_time?: number;
  is_active?: boolean;
}

export const adminService = {
  async getDashboardStats(): Promise<AdminDashboardStats> {
    const res = await apiClient.get<ApiResponse<AdminDashboardStats>>('/admin/dashboard');
    return res.data.data;
  },

  async getUsers(role?: string, limit: number = 50, skip: number = 0): Promise<{ users: User[]; total: number }> {
    const params: Record<string, any> = { limit, skip };
    if (role) params.role = role;
    const res = await apiClient.get<ApiResponse<{ users: User[]; total: number }>>('/admin/users', { params });
    return res.data.data;
  },

  async getDoctors(departmentId?: string): Promise<Doctor[]> {
    const params: Record<string, string> = {};
    if (departmentId) params.department_id = departmentId;
    const res = await apiClient.get<ApiResponse<Doctor[]>>('/admin/doctors', { params });
    return res.data.data;
  },

  async createDoctor(payload: CreateDoctorPayload): Promise<Doctor> {
    const res = await apiClient.post<ApiResponse<Doctor>>('/admin/doctors', payload);
    return res.data.data;
  },

  async updateDoctor(doctorId: string, payload: UpdateDoctorPayload): Promise<Doctor> {
    const res = await apiClient.patch<ApiResponse<Doctor>>(`/admin/doctors/${doctorId}`, payload);
    return res.data.data;
  },

  async createDepartment(payload: CreateDepartmentPayload): Promise<Department> {
    const res = await apiClient.post<ApiResponse<Department>>('/admin/departments', payload);
    return res.data.data;
  },

  async updateDepartment(departmentId: string, payload: UpdateDepartmentPayload): Promise<Department> {
    const res = await apiClient.patch<ApiResponse<Department>>(`/admin/departments/${departmentId}`, payload);
    return res.data.data;
  },

  async getQueues(departmentId?: string, status?: string, limit: number = 50, skip: number = 0): Promise<{ queues: QueueTicket[]; total: number }> {
    const params: Record<string, any> = { limit, skip };
    if (departmentId) params.department_id = departmentId;
    if (status) params.status = status;
    const res = await apiClient.get<ApiResponse<{ queues: QueueTicket[]; total: number }>>('/admin/queues', { params });
    return res.data.data;
  },

  async getAuditLogs(entityType?: string, action?: string, limit: number = 50, skip: number = 0): Promise<{ logs: AuditLog[]; total: number }> {
    const params: Record<string, any> = { limit, skip };
    if (entityType) params.entity_type = entityType;
    if (action) params.action = action;
    const res = await apiClient.get<ApiResponse<{ logs: AuditLog[]; total: number }>>('/admin/audit-logs', { params });
    return res.data.data;
  },
};
