import { UserRole } from './enums';

export interface DepartmentBrief {
  id: string;
  name: string;
}

export interface TeamBrief {
  id: string;
  name: string;
}

export interface UserBrief {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
}

export interface UserRead {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  patronymic: string | null;
  position: string | null;
  role: UserRole;
  department_id: string | null;
  team_id: string | null;
  department: DepartmentBrief | null;
  team: TeamBrief | null;
  telegram_username: string | null;
  hire_date: string | null;
  is_active: boolean;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  patronymic?: string;
  position?: string;
  role?: UserRole;
  department_id?: string;
  team_id?: string;
  telegram_username?: string;
  hire_date?: string;
}

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
  patronymic?: string;
  position?: string;
  role?: UserRole;
  department_id?: string;
  team_id?: string;
  telegram_username?: string;
  hire_date?: string;
  is_active?: boolean;
}

export interface AssessmentHistoryEntry {
  campaign_id: string;
  campaign_name: string;
  campaign_end_date: string;
  competency_id: string;
  final_score: number;
  self_score: number | null;
  tl_score: number | null;
  dh_score: number | null;
  peer_score: number | null;
}
