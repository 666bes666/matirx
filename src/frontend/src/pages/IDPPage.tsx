import { useState } from 'react'
import {
  Badge,
  Button,
  Group,
  LoadingOverlay,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { developmentPlansApi } from '../api/development_plans'
import { usersApi } from '../api/users'
import { usePermissions } from '../hooks/usePermissions'

const APPROVAL_COLORS: Record<string, string> = {
  pending: 'yellow',
  approved: 'green',
  rejected: 'red',
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  active: 'Активен',
  completed: 'Выполнен',
  archived: 'В архиве',
}

export function IDPPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [opened, { open, close }] = useDisclosure(false)
  const { canCreateUser } = usePermissions()
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)

  const { data: plans, isLoading } = useQuery({
    queryKey: ['development-plans'],
    queryFn: developmentPlansApi.list,
  })

  const { data: users } = useQuery({
    queryKey: ['users-idp'],
    queryFn: () => usersApi.list().then((u) => u.map((x) => ({
      value: x.id,
      label: `${x.last_name} ${x.first_name}`,
    }))),
  })

  const createMutation = useMutation({
    mutationFn: () => developmentPlansApi.create({ user_id: selectedUserId! }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['development-plans'] })
      close()
    },
  })

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Планы развития (ИПР)</Title>
        {canCreateUser && (
          <Button onClick={open}>Создать ИПР</Button>
        )}
      </Group>

      <Paper withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Сотрудник</Table.Th>
              <Table.Th>Статус</Table.Th>
              <Table.Th>Согласование</Table.Th>
              <Table.Th>Целей</Table.Th>
              <Table.Th>Дата создания</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {plans?.map((plan) => (
              <Table.Tr
                key={plan.id}
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/idp/${plan.id}`)}
              >
                <Table.Td>{plan.user.last_name} {plan.user.first_name}</Table.Td>
                <Table.Td>
                  <Badge color="blue" size="sm">{STATUS_LABELS[plan.status] ?? plan.status}</Badge>
                </Table.Td>
                <Table.Td>
                  <Badge color={APPROVAL_COLORS[plan.approval] ?? 'gray'} size="sm">
                    {plan.approval}
                  </Badge>
                </Table.Td>
                <Table.Td>{plan.goals.length}</Table.Td>
                <Table.Td>{plan.created_at.slice(0, 10)}</Table.Td>
              </Table.Tr>
            ))}
            {plans?.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Text c="dimmed" ta="center" py="md">Нет планов развития</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal opened={opened} onClose={close} title="Новый ИПР">
        <Stack>
          <Select
            label="Сотрудник"
            placeholder="Выберите сотрудника"
            data={users ?? []}
            value={selectedUserId}
            onChange={setSelectedUserId}
            searchable
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={close}>Отмена</Button>
            <Button
              disabled={!selectedUserId}
              loading={createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Создать
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
