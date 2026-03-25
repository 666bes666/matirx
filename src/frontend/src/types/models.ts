import { UserRole } from './enums';

export interface UserBrief {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  patronymic: string | null;
  position: string | null;
  role: UserRole;
  department_id: string | null;
  team_id: string | null;
  telegram_username: string | null;
  hire_date: string | null;
  is_active: boolean;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}
