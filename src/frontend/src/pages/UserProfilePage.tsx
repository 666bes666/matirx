import {
  Badge,
  Button,
  Divider,
  Group,
  LoadingOverlay,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { usersApi } from '../api/users'
import { RoleBadge } from '../components/ui/RoleBadge'
import { useAuthStore } from '../stores/authStore'
import { UserRole } from '../types/enums'

export function UserProfilePage() {
  const { id } = useParams<{ id: string }>()
  const { user: currentUser } = useAuthStore()

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', id],
    queryFn: () => usersApi.get(id!),
    enabled: !!id,
  })

  const canEdit =
    currentUser?.role === UserRole.ADMIN ||
    currentUser?.id === id ||
    (currentUser?.role === UserRole.DEPARTMENT_HEAD &&
      currentUser?.department_id === user?.department_id)

  const canActivate = [UserRole.ADMIN, UserRole.HR].includes(currentUser?.role as UserRole)

  const fullName = user
    ? [user.last_name, user.first_name, user.patronymic].filter(Boolean).join(' ')
    : ''

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Профиль сотрудника</Title>
        <Group>
          {canEdit && (
            <Button variant="outline" size="sm">
              Редактировать
            </Button>
          )}
          {canActivate && user && !user.is_active && (
            <Button color="green" size="sm">
              Активировать
            </Button>
          )}
          {canActivate && user?.is_active && (
            <Button color="red" variant="outline" size="sm">
              Деактивировать
            </Button>
          )}
        </Group>
      </Group>

      <Paper p="lg" withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />

        {user && (
          <Stack gap="md">
            <Group>
              <Title order={3}>{fullName}</Title>
              <RoleBadge role={user.role} />
              <Badge color={user.is_active ? 'green' : 'red'} variant="dot">
                {user.is_active ? 'Активен' : 'Неактивен'}
              </Badge>
            </Group>

            <Divider />

            <Group gap="xl">
              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Email
                </Text>
                <Text size="sm">{user.email}</Text>
              </Stack>

              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Должность
                </Text>
                <Text size="sm">{user.position ?? '—'}</Text>
              </Stack>

              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Отдел
                </Text>
                <Text size="sm">{user.department?.name ?? '—'}</Text>
              </Stack>

              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Команда
                </Text>
                <Text size="sm">{user.team?.name ?? '—'}</Text>
              </Stack>

              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Telegram
                </Text>
                <Text size="sm">{user.telegram_username ?? '—'}</Text>
              </Stack>

              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  Дата найма
                </Text>
                <Text size="sm">{user.hire_date ?? '—'}</Text>
              </Stack>
            </Group>
          </Stack>
        )}
      </Paper>
    </Stack>
  )
}
