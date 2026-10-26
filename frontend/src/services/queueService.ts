import { apiClient } from './api';
import { ApiResponse, QueueTicket, JoinQueuePayload, QueueUpdatePayload } from '../types';

export const queueService = {
  async joinQueue(payload: JoinQueuePayload): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>('/queues/join', payload);
    return res.data.data;
  },

  async getMyQueues(): Promise<QueueTicket[]> {
    const res = await apiClient.get<ApiResponse<QueueTicket[]>>('/queues/my');
    return res.data.data;
  },

  async getQueueById(queueId: string): Promise<QueueTicket> {
    const res = await apiClient.get<ApiResponse<QueueTicket>>(`/queues/${queueId}`);
    return res.data.data;
  },

  async cancelQueue(queueId: string): Promise<QueueTicket> {
    const res = await apiClient.post<ApiResponse<QueueTicket>>(`/queues/${queueId}/cancel`);
    return res.data.data;
  },

  async getStaffQueues(departmentId?: string, status?: string): Promise<QueueTicket[]> {
    const params: Record<string, string> = {};
    if (departmentId) params.department_id = departmentId;
    if (status) params.status = status;

    const res = await apiClient.get<ApiResponse<QueueTicket[]>>('/queues', { params });
    return res.data.data;
  },

  async updateQueueStatus(queueId: string, payload: QueueUpdatePayload): Promise<QueueTicket> {
    const res = await apiClient.patch<ApiResponse<QueueTicket>>(`/queues/${queueId}/status`, payload);
    return res.data.data;
  },
};
