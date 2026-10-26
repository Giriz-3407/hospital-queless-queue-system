export type QueueStatus =
  | 'WAITING'
  | 'CALLED'
  | 'IN_CONSULTATION'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'NO_SHOW'
  | 'waiting'
  | 'called'
  | 'in_consultation'
  | 'completed'
  | 'cancelled'
  | 'no_show';

export interface Doctor {
  id: string;
  display_name: string;
  specialty?: string;
  is_available: boolean;
  department_id?: string;
  department_name?: string;
  department_code?: string;
  user?: {
    id: string;
    name: string;
    email: string;
    role: string;
    phone?: string;
    is_active?: boolean;
  };
}

export interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
  avg_consultation_time: number;
  is_active: boolean;
  current_waiting?: number;
  estimated_wait_minutes?: number | null;
  available_doctors_count?: number;
  total_doctors_count?: number;
  stats?: {
    waiting: number;
    called?: number;
    in_consultation: number;
    completed_today: number;
    no_show_today?: number;
  };
  doctors?: Doctor[];
}

export interface QueueTicket {
  id: string;
  department_id: string;
  department_name: string;
  department_code: string;
  patient_id: string;
  patient_name: string;
  token_number: string;
  ticket_number?: string;
  queue_date?: string;
  position: number;
  live_position: number;
  patients_ahead?: number;
  estimated_wait_minutes?: number | null;
  live_estimated_wait_minutes?: number | null;
  status: QueueStatus;
  doctor_id?: string;
  doctor_name?: string;
  reason?: string;
  notes?: string;
  currently_serving_ticket?: string | null;
  currently_called_ticket?: string | null;
  joined_at?: string;
  called_at?: string;
  consultation_started_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  created_at: string;
  updated_at: string;
}

export interface JoinQueuePayload {
  department_id: string;
  reason?: string;
}

export interface QueueUpdatePayload {
  status: string;
  notes?: string;
}

export interface DoctorQueueResponse {
  doctor: Doctor;
  department: Department;
  currently_called: QueueTicket | null;
  currently_serving: QueueTicket | null;
  waiting_queue: QueueTicket[];
  stats: {
    waiting: number;
    called: number;
    in_consultation: number;
    completed_today: number;
    no_show_today: number;
  };
}

export interface AdminDashboardStats {
  total_users: number;
  total_patients: number;
  total_doctors: number;
  total_departments: number;
  active_departments: number;
  active_tickets: number;
  tickets_today: number;
  completed_today: number;
}

export interface AuditLog {
  id: string;
  actor_user_id?: string;
  actor_name?: string;
  actor_role?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
