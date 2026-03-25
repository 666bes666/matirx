import { useState } from 'react'
import {
  Badge,
  Button,
  Group,
  LoadingOverlay,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { IconSearch, IconUserPlus } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { usersApi } from '../api/users'
import { RoleBadge } from '../components/ui/RoleBadge'
import { useAuthStore } from '../stores/authStore'
import { UserRole } from '../types/enums'
import type { UserRead } from '../types/models'

const ROLE_OPTIONS = [
  { value: '', label: 'Все роли' },
  { value: UserRole.ADMIN, label: 'Администратор' },
  { value: UserRole.HEAD, label: 'Рук. управления' },
  { value: UserRole.DEPARTMENT_HEAD, label: 'Рук. отдела' },
  { value: UserRole.TEAM_LEAD, label: 'Тимлид' },
  { value: UserRole.HR, label: 'HR' },
  { value: UserRole.EMPLOYEE, label: 'Сотрудник' },
]

export function UsersPage() {
  const { user: currentUser } = useAuthStore()
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [isActiveFilter, setIsActiveFilter] = useState<string | null>(null)

  const { data: users, isLoading } = useQuery({
    queryKey: ['users', search, roleFilter, isActiveFilter],
    queryFn: () =>
      usersApi.list({
        search: search || undefined,
        role: roleFilter || undefined,
        is_active: isActiveFilter === null ? undefined : isActiveFilter === 'true',
      }),
  })

  const canCreate = [UserRole.ADMIN, UserRole.HR, UserRole.HEAD].includes(
    currentUser?.role as UserRole,
  )

  const fullName = (u: UserRead) =>
    [u.last_name, u.first_name, u.patronymic].filter(Boolean).join(' ')

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Сотрудники</Title>
        {canCreate && (
          <Button leftSection={<IconUserPlus size={16} />} size="sm">
            Добавить сотрудника
          </Button>
        )}
      </Group>

      <Group>
        <TextInput
          placeholder="Поиск по имени или email"
          leftSection={<IconSearch size={16} />}
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          style={{ flex: 1 }}
        />
        <Select
          data={ROLE_OPTIONS}
          value={roleFilter}
          onChange={(v) => setRoleFilter(v ?? '')}
          placeholder="Роль"
          clearable
          style={{ width: 180 }}
        />
        <Select
          data={[
            { value: '', label: 'Все' },
            { value: 'true', label: 'Активные' },
            { value: 'false', label: 'Неактивные' },
          ]}
          value={isActiveFilter ?? ''}
          onChange={(v) => setIsActiveFilter(v || null)}
          placeholder="Статус"
          clearable
          style={{ width: 150 }}
        />
      </Group>

      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={isLoading} />
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ФИО</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Роль</Table.Th>
              <Table.Th>Отдел</Table.Th>
              <Table.Th>Команда</Table.Th>
              <Table.Th>Статус</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {users?.map((u) => (
              <Table.Tr key={u.id}>
                <Table.Td>
                  <Text size="sm" fw={500}>
                    {fullName(u)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">
                    {u.email}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <RoleBadge role={u.role} />
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{u.department?.name ?? '—'}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{u.team?.name ?? '—'}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge color={u.is_active ? 'green' : 'red'} variant="dot" size="sm">
                    {u.is_active ? 'Активен' : 'Неактивен'}
                  </Badge>
                </Table.Td>
              </Table.Tr>
            ))}
            {!isLoading && !users?.length && (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center" c="dimmed" py="md">
                    Нет сотрудников
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </div>
    </Stack>
  )
}
