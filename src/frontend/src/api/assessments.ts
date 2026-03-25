import { apiClient } from './client'
import type {
  CampaignRead,
  CampaignCreate,
  AssessmentRead,
  AssessmentCreate,
  AssessmentScoreSubmit,
  CampaignProgressRead,
  AggregatedScoreRead,
} from '../types/assessment'

export const assessmentsApi = {
  listCampaigns: (status?: string) =>
    apiClient
      .get<CampaignRead[]>('/assessments/campaigns', { params: { status } })
      .then((r) => r.data),

  getCampaign: (id: string) =>
    apiClient.get<CampaignRead>(`/assessments/campaigns/${id}`).then((r) => r.data),

  createCampaign: (data: CampaignCreate) =>
    apiClient.post<CampaignRead>('/assessments/campaigns', data).then((r) => r.data),

  createAssessment: (data: AssessmentCreate) =>
    apiClient.post<AssessmentRead>('/assessments', data).then((r) => r.data),

  listAssessments: (params?: { campaign_id?: string; assessee_id?: string }) =>
    apiClient.get<AssessmentRead[]>('/assessments', { params }).then((r) => r.data),

  getAssessment: (id: string) =>
    apiClient.get<AssessmentRead>(`/assessments/${id}`).then((r) => r.data),

  submitScores: (id: string, data: AssessmentScoreSubmit) =>
    apiClient.post<AssessmentRead>(`/assessments/${id}/scores`, data).then((r) => r.data),

  activateCampaign: (id: string) =>
    apiClient.post<CampaignRead>(`/assessments/campaigns/${id}/activate`).then((r) => r.data),

  closeCampaign: (id: string) =>
    apiClient.post<CampaignRead>(`/assessments/campaigns/${id}/close`).then((r) => r.data),

  finalizeCampaign: (id: string) =>
    apiClient.post<CampaignRead>(`/assessments/campaigns/${id}/finalize`).then((r) => r.data),

  archiveCampaign: (id: string) =>
    apiClient.post<CampaignRead>(`/assessments/campaigns/${id}/archive`).then((r) => r.data),

  getCampaignProgress: (id: string) =>
    apiClient.get<CampaignProgressRead>(`/assessments/campaigns/${id}/progress`).then((r) => r.data),

  getAggregatedScores: (id: string) =>
    apiClient.get<AggregatedScoreRead[]>(`/assessments/campaigns/${id}/scores`).then((r) => r.data),

  setWeights: (id: string, weights: { department_head_weight: number; team_lead_weight: number; self_weight: number; peer_weight: number }) =>
    apiClient.put(`/assessments/campaigns/${id}/weights`, weights).then((r) => r.data),

  setPeers: (campaignId: string, peerIds: string[]) =>
    apiClient.post(`/assessments/campaigns/${campaignId}/peers`, { peer_ids: peerIds }).then((r) => r.data),

  getMyPeers: (campaignId: string) =>
    apiClient.get<string[]>(`/assessments/campaigns/${campaignId}/peers`).then((r) => r.data),

  listMyTasks: () =>
    apiClient.get<AssessmentRead[]>('/assessments/my-tasks').then((r) => r.data),
}
