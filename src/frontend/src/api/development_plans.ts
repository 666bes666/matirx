import { apiClient } from './client'
import type {
  DevelopmentPlanRead,
  DevelopmentPlanCreate,
  DevelopmentPlanUpdate,
  DevelopmentGoalCreate,
  DevelopmentGoalUpdate,
  DevelopmentGoalRead,
  LearningResourceCreate,
  LearningResourceRead,
} from '../types/development_plan'

export const developmentPlansApi = {
  list: () => apiClient.get<DevelopmentPlanRead[]>('/development-plans').then((r) => r.data),
  get: (id: string) => apiClient.get<DevelopmentPlanRead>(`/development-plans/${id}`).then((r) => r.data),
  create: (data: DevelopmentPlanCreate) =>
    apiClient.post<DevelopmentPlanRead>('/development-plans', data).then((r) => r.data),
  update: (id: string, data: DevelopmentPlanUpdate) =>
    apiClient.patch<DevelopmentPlanRead>(`/development-plans/${id}`, data).then((r) => r.data),
  archive: (id: string) => apiClient.post(`/development-plans/${id}/archive`),
  addGoal: (planId: string, data: DevelopmentGoalCreate) =>
    apiClient.post<DevelopmentGoalRead>(`/development-plans/${planId}/goals`, data).then((r) => r.data),
  updateGoal: (planId: string, goalId: string, data: DevelopmentGoalUpdate) =>
    apiClient.patch<DevelopmentGoalRead>(`/development-plans/${planId}/goals/${goalId}`, data).then((r) => r.data),
  deleteGoal: (planId: string, goalId: string) =>
    apiClient.delete(`/development-plans/${planId}/goals/${goalId}`),
}

export type { LearningResourceCreate, LearningResourceRead }

