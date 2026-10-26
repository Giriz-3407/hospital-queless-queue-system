import { apiClient } from './api';
import { ApiResponse, Department } from '../types';

export const departmentService = {
  async getDepartments(): Promise<Department[]> {
    const res = await apiClient.get<ApiResponse<Department[]>>('/departments');
    return res.data.data;
  },
};
