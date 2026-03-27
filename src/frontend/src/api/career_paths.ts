import { apiClient } from './client'
import type {
  CareerPathCreate,
  CareerPathRead,
  CareerPathRequirementInput,
  CareerReadinessRead,
} from '../types/career_path'

export const careerPathsApi = {
  list: () => apiClient.get<CareerPathRead[]>('/career-paths').then((r) => r.data),
  get: (id: string) => apiClient.get<CareerPathRead>(`/career-paths/${id}`).then((r) => r.data),
  create: (data: CareerPathCreate) =>
    apiClient.post<CareerPathRead>('/career-paths', data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/career-paths/${id}`),
  setRequirements: (id: string, requirements: CareerPathRequirementInput[]) =>
    apiClient.put<CareerPathRead>(`/career-paths/${id}/requirements`, requirements).then((r) => r.data),
  getReadiness: (pathId: string, userId: string) =>
    apiClient.get<CareerReadinessRead>(`/career-paths/${pathId}/readiness/${userId}`).then((r) => r.data),
  listByDepartment: (departmentId: string) =>
    apiClient.get<CareerPathRead[]>(`/career-paths/by-department/${departmentId}`).then((r) => r.data),
}
