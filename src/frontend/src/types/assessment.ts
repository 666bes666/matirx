export interface CampaignCreate {
  name: string
  description?: string
  scope: string
  department_id?: string
  team_id?: string
  start_date: string
  end_date: string
}

export interface CampaignRead {
  id: string
  name: string
  description: string | null
  scope: string
  status: string
  department_id: string | null
  team_id: string | null
  start_date: string
  end_date: string
  created_at: string
  updated_at: string
}

export interface AssessmentCreate {
  campaign_id: string
  assessee_id: string
  assessor_type: string
}

export interface ScoreInput {
  competency_id: string
  score: number
  comment?: string
}

export interface AssessmentScoreSubmit {
  scores: ScoreInput[]
  is_draft?: boolean
}

export interface AssessmentScoreRead {
  competency_id: string
  score: number
  comment: string | null
  is_draft: boolean
}

export interface UserBrief {
  id: string
  first_name: string
  last_name: string
}

export interface AssessmentRead {
  id: string
  campaign_id: string
  assessee: UserBrief
  assessor: UserBrief
  assessor_type: string
  status: string
  scores: AssessmentScoreRead[]
  created_at: string
}

export interface CampaignProgressRead {
  campaign_id: string
  total_assessments: number
  completed_assessments: number
  pending_assessments: number
  completion_pct: number
}

export interface AggregatedScoreRead {
  user_id: string
  competency_id: string
  final_score: number
  self_score: number | null
  peer_score: number | null
  tl_score: number | null
  dh_score: number | null
}

export interface PeerSelectionSet {
  peer_ids: string[]
}
