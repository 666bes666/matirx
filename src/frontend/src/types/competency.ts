import { CompetencyCategoryType } from './enums'

export interface CompetencyCategoryRead {
  id: string
  name: CompetencyCategoryType
  description: string | null
}

export interface CriteriaRead {
  level: number
  criteria_description: string
}

export interface CriteriaUpsert {
  level: number
  criteria_description: string
}

export interface CompetencyRead {
  id: string
  category_id: string
  category: CompetencyCategoryRead
  name: string
  description: string | null
  is_common: boolean
  is_archived: boolean
  departments: { id: string; name: string }[]
  level_criteria: CriteriaRead[]
  created_at: string
  updated_at: string
}

export interface CompetencyCreate {
  category_id: string
  name: string
  description?: string
  is_common?: boolean
  department_ids?: string[]
}

export interface CompetencyUpdate {
  name?: string
  description?: string
  is_common?: boolean
  category_id?: string
  department_ids?: string[]
}
