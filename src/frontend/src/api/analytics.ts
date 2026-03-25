import { apiClient } from './client'
import type { MatrixData, HeatmapData } from '../types/analytics'

export interface MatrixFilters {
  department_id?: string
  team_id?: string
  category_id?: string
}

export const analyticsApi = {
  getMatrix: (filters?: MatrixFilters) =>
    apiClient.get<MatrixData>('/analytics/matrix', { params: filters }).then((r) => r.data),
  getHeatmap: (params?: { category_id?: string }) =>
    apiClient.get<HeatmapData>('/analytics/heatmap', { params }).then((r) => r.data),
}
