import { apiClient } from './client'
import type {
  CompetencyRead,
  CompetencyCategoryRead,
  CompetencyCreate,
  CompetencyUpdate,
  CriteriaUpsert,
} from '../types/competency'

export interface CompetencyFilters {
  category_id?: string
  department_id?: string
  is_common?: boolean
  is_archived?: boolean
  search?: string
}

export const competenciesApi = {
  listCategories: () =>
    apiClient.get<CompetencyCategoryRead[]>('/competencies/categories').then((r) => r.data),

  list: (filters?: CompetencyFilters) =>
    apiClient.get<CompetencyRead[]>('/competencies', { params: filters }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<CompetencyRead>(`/competencies/${id}`).then((r) => r.data),

  create: (data: CompetencyCreate) =>
    apiClient.post<CompetencyRead>('/competencies', data).then((r) => r.data),

  update: (id: string, data: CompetencyUpdate) =>
    apiClient.patch<CompetencyRead>(`/competencies/${id}`, data).then((r) => r.data),

  archive: (id: string) =>
    apiClient.post<CompetencyRead>(`/competencies/${id}/archive`).then((r) => r.data),

  unarchive: (id: string) =>
    apiClient.post<CompetencyRead>(`/competencies/${id}/unarchive`).then((r) => r.data),

  upsertCriteria: (id: string, criteria: CriteriaUpsert[]) =>
    apiClient.put<CompetencyRead>(`/competencies/${id}/criteria`, criteria).then((r) => r.data),
}
