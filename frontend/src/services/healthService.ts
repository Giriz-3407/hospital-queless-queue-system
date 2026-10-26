import { apiClient } from './api';
import { ApiResponse } from '../types';

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  service: string;
  version: string;
  uptime_seconds: number;
  database: {
    status: 'connected' | 'disconnected';
    name?: string;
  };
  server_time: string;
}

export const healthService = {
  async getHealth(): Promise<HealthStatus> {
    const res = await apiClient.get<ApiResponse<HealthStatus>>('/health');
    return res.data.data;
  },
};
