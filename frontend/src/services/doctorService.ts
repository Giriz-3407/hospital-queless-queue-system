import { apiClient } from './api';
import { ApiResponse, DoctorQueueResponse, QueueTicket } from '../types';

export const doctorService = {
  async getDoctorQueue(): Promise<DoctorQueueResponse> {
    const res = await apiClient.get<ApiResponse<DoctorQueueResponse>>('/doctor/queue');
    return res.data.data;
  },

  async callNextPatient(): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>('/doctor/queue/next');
    return res.data.data;
  },

  async startConsultation(queueId: string): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>(`/doctor/queue/${queueId}/start`);
    return res.data.data;
  },

  async completeConsultation(queueId: string, notes?: string): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>(`/doctor/queue/${queueId}/complete`, { notes });
    return res.data.data;
  },

  async markNoShow(queueId: string, notes?: string): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>(`/doctor/queue/${queueId}/no-show`, { notes });
    return res.data.data;
  },
};
