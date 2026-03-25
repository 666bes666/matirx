import { Badge } from '@mantine/core'
import { UserRole } from '../../types/enums'

const ROLE_CONFIG: Record<UserRole, { label: string; color: string }> = {
  [UserRole.ADMIN]: { label: 'Администратор', color: 'red' },
  [UserRole.HEAD]: { label: 'Руководитель упр.', color: 'violet' },
  [UserRole.DEPARTMENT_HEAD]: { label: 'Рук. отдела', color: 'blue' },
  [UserRole.TEAM_LEAD]: { label: 'Тимлид', color: 'cyan' },
  [UserRole.HR]: { label: 'HR', color: 'teal' },
  [UserRole.EMPLOYEE]: { label: 'Сотрудник', color: 'gray' },
}

interface RoleBadgeProps {
  role: UserRole
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const config = ROLE_CONFIG[role] ?? { label: role, color: 'gray' }
  return (
    <Badge color={config.color} variant="light" size="sm">
      {config.label}
    </Badge>
  )
}
