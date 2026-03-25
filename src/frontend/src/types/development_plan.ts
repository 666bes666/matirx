export type PlanStatus = 'draft' | 'active' | 'completed' | 'archived'
export type PlanApproval = 'pending' | 'approved' | 'rejected'
export type GoalStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled'
export type ResourceType = 'book' | 'course' | 'article' | 'video' | 'other'

export interface DevelopmentGoalCreate {
  competency_id: string
  current_level: number
  target_level: number
  deadline?: string
  is_mandatory?: boolean
}

export interface DevelopmentGoalUpdate {
  status?: GoalStatus
  deadline?: string
  target_level?: number
}

export interface DevelopmentGoalRead {
  id: string
  plan_id: string
  competency_id: string
  competency: { id: string; name: string }
  current_level: number
  target_level: number
  status: GoalStatus
  deadline: string | null
  is_mandatory: boolean
  created_at: string
}

export interface DevelopmentPlanCreate {
  user_id: string
}

export interface DevelopmentPlanUpdate {
  status?: PlanStatus
  approval?: PlanApproval
}

export interface DevelopmentPlanRead {
  id: string
  user_id: string
  user: { id: string; first_name: string; last_name: string }
  created_by: string
  status: PlanStatus
  approval: PlanApproval
  is_archived: boolean
  goals: DevelopmentGoalRead[]
  created_at: string
  updated_at: string
}

export interface LearningResourceCreate {
  title: string
  url?: string
  resource_type?: ResourceType
  target_level?: number
  description?: string
}

export interface LearningResourceRead {
  id: string
  competency_id: string
  title: string
  url: string | null
  resource_type: ResourceType
  target_level: number | null
  description: string | null
  created_at: string
}
