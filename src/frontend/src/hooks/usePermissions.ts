import { useAuthStore } from '../stores/authStore'
import { UserRole } from '../types/enums'

export function usePermissions() {
  const { user } = useAuthStore()
  const role = user?.role as UserRole | undefined

  const is = (...roles: UserRole[]) => !!role && roles.includes(role)

  return {
    canViewAllUsers: is(UserRole.ADMIN, UserRole.HEAD, UserRole.HR),
    canCreateUser: is(UserRole.ADMIN, UserRole.HEAD),
    canEditUser: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canActivateUser: is(UserRole.ADMIN, UserRole.HEAD),

    canCreateDepartment: is(UserRole.ADMIN, UserRole.HEAD),
    canEditDepartment: is(UserRole.ADMIN, UserRole.HEAD),
    canDeleteDepartment: is(UserRole.ADMIN),

    canCreateTeam: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canEditTeam: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canDeleteTeam: is(UserRole.ADMIN),

    canCreateCompetency: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canEditCompetency: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canArchiveCompetency: is(UserRole.ADMIN, UserRole.HEAD),

    canCreateTargetProfile: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canEditTargetProfile: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canDeleteTargetProfile: is(UserRole.ADMIN, UserRole.HEAD),

    canCreateCampaign: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD),
    canCreateAssessment: is(UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD, UserRole.TEAM_LEAD),

    canViewMatrix: !!role,
    canExportReports: is(UserRole.ADMIN, UserRole.HEAD, UserRole.HR),
  }
}
