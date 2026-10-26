import { apiClient } from './api';
import { ApiResponse, AuthData, LoginPayload, RegisterPayload, User } from '../types';
import { storage } from '../utils/storage';

export const authService = {
  async register(payload: RegisterPayload): Promise<AuthData> {
    const res = await apiClient.post<ApiResponse<AuthData>>('/auth/register', payload);
    const authData = res.data.data;
    storage.setToken(authData.token);
    storage.setUser(authData.user);
    return authData;
  },

  async login(payload: LoginPayload): Promise<AuthData> {
    const res = await apiClient.post<ApiResponse<AuthData>>('/auth/login', payload);
    const authData = res.data.data;
    storage.setToken(authData.token);
    storage.setUser(authData.user);
    return authData;
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get<ApiResponse<User>>('/auth/me');
    const user = res.data.data;
    storage.setUser(user);
    return user;
  },

  logout(): void {
    storage.clearAuth();
  },
};
