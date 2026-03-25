import { apiClient } from './client'
import type { UserRead, UserCreate, UserUpdate, AssessmentHistoryEntry } from '../types/models'

export interface UserFilters {
  search?: string
  department_id?: string
  team_id?: string
  role?: string
  is_active?: boolean
}

export const usersApi = {
  list: (filters?: UserFilters) =>
    apiClient.get<UserRead[]>('/users', { params: filters }).then((r) => r.data),

  get: (id: string) => apiClient.get<UserRead>(`/users/${id}`).then((r) => r.data),

  me: () => apiClient.get<UserRead>('/users/me').then((r) => r.data),

  create: (data: UserCreate) => apiClient.post<UserRead>('/users', data).then((r) => r.data),

  update: (id: string, data: UserUpdate) =>
    apiClient.patch<UserRead>(`/users/${id}`, data).then((r) => r.data),

  activate: (id: string) =>
    apiClient.post<UserRead>(`/users/${id}/activate`).then((r) => r.data),

  deactivate: (id: string) =>
    apiClient.post<UserRead>(`/users/${id}/deactivate`).then((r) => r.data),

  getAssessmentHistory: (userId: string) =>
    apiClient.get<AssessmentHistoryEntry[]>(`/users/${userId}/assessment-history`).then((r) => r.data),
}
