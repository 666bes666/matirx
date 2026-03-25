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

export const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Администратор',
  [UserRole.HEAD]: 'Руководитель управления',
  [UserRole.DEPARTMENT_HEAD]: 'Руководитель отдела',
  [UserRole.TEAM_LEAD]: 'Тимлид',
  [UserRole.HR]: 'HR',
  [UserRole.EMPLOYEE]: 'Сотрудник',
};
