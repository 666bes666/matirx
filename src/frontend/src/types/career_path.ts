export interface CareerPathRequirementInput {
  competency_id: string
  required_level: number
  is_mandatory?: boolean
}

export interface CareerPathRequirementRead {
  id: string
  career_path_id: string
  competency_id: string
  competency: { id: string; name: string }
  required_level: number
  is_mandatory: boolean
}

export interface CareerPathCreate {
  from_department_id: string
  to_department_id: string
}

export interface CareerPathRead {
  id: string
  from_department_id: string
  to_department_id: string
  from_department: { id: string; name: string }
  to_department: { id: string; name: string }
  is_active: boolean
  requirements: CareerPathRequirementRead[]
  created_at: string
}

export interface ReadinessItem {
  competency_id: string
  competency_name: string
  required_level: number
  is_mandatory: boolean
  current_score: number | null
  gap: number | null
  is_met: boolean
}

export interface CareerReadinessRead {
  career_path_id: string
  user_id: string
  is_ready: boolean
  readiness_pct: number
  mandatory_met: boolean
  items: ReadinessItem[]
}
