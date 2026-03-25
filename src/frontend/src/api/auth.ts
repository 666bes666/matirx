import { client } from './client';
import type { LoginResponse, TokenRefreshResponse } from '../types/api';
import type { UserBrief } from '../types/models';

export const authApi = {
  login: (email: string, password: string) =>
    client.post<LoginResponse>('/auth/login', { email, password }),

  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    patronymic?: string;
  }) => client.post('/auth/register', data),

  refresh: () => client.post<TokenRefreshResponse>('/auth/refresh'),

  logout: () => client.post('/auth/logout'),

  me: () => client.get<UserBrief>('/auth/me'),
};
