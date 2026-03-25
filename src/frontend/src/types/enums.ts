export enum UserRole {
  ADMIN = 'admin',
  HEAD = 'head',
  DEPARTMENT_HEAD = 'department_head',
  TEAM_LEAD = 'team_lead',
  HR = 'hr',
  EMPLOYEE = 'employee',
}

export enum CampaignStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  COLLECTING = 'collecting',
  CALIBRATION = 'calibration',
  FINALIZED = 'finalized',
  ARCHIVED = 'archived',
}

export enum CompetencyCategoryType {
  HARD_SKILL = 'hard_skill',
  SOFT_SKILL = 'soft_skill',
  PROCESS = 'process',
  DOMAIN = 'domain',
}

export const CATEGORY_LABELS: Record<CompetencyCategoryType, string> = {
  [CompetencyCategoryType.HARD_SKILL]: 'Хард скиллы',
  [CompetencyCategoryType.SOFT_SKILL]: 'Софт скиллы',
  [CompetencyCategoryType.PROCESS]: 'Процессы',
  [CompetencyCategoryType.DOMAIN]: 'Доменные знания',
}

export const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Администратор',
  [UserRole.HEAD]: 'Руководитель управления',
  [UserRole.DEPARTMENT_HEAD]: 'Руководитель отдела',
  [UserRole.TEAM_LEAD]: 'Тимлид',
  [UserRole.HR]: 'HR',
  [UserRole.EMPLOYEE]: 'Сотрудник',
};
