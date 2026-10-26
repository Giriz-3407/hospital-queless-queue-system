export type QueueStatus = 'waiting' | 'in_consultation' | 'completed' | 'cancelled' | 'no_show';

export interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
  avg_consultation_time: number;
  is_active: boolean;
  current_waiting?: number;
  estimated_wait_minutes?: number;
  stats?: {
    waiting: number;
    in_consultation: number;
    completed_today: number;
  };
}

export interface QueueTicket {
  id: string;
  department_id: string;
  department_name: string;
  department_code: string;
  patient_id: string;
  patient_name: string;
  ticket_number: string;
  position: number;
  live_position: number;
  estimated_wait_minutes: number;
  live_estimated_wait_minutes: number;
  status: QueueStatus;
  reason?: string;
  notes?: string;
  currently_serving_ticket?: string;
  called_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface JoinQueuePayload {
  department_id: string;
  reason?: string;
}

export interface QueueUpdatePayload {
  status: QueueStatus;
  notes?: string;
}
