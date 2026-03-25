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
import { useParams } from 'react-router-dom'
import { developmentPlansApi } from '../api/development_plans'
import { competenciesApi } from '../api/competencies'
import { usePermissions } from '../hooks/usePermissions'
import type { DevelopmentGoalCreate } from '../types/development_plan'

const GOAL_STATUS_COLORS: Record<string, string> = {
  planned: 'blue',
  in_progress: 'orange',
  completed: 'green',
  cancelled: 'gray',
}

const LEVEL_LABELS = ['0 — Нет', '1 — Новичок', '2 — Базовый', '3 — Продвинутый', '4 — Эксперт']

export function IDPDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [opened, { open, close }] = useDisclosure(false)
  const { canCreateUser } = usePermissions()
  const [goalForm, setGoalForm] = useState<Partial<DevelopmentGoalCreate>>({})

  const { data: plan, isLoading } = useQuery({
    queryKey: ['idp', id],
    queryFn: () => developmentPlansApi.get(id!),
    enabled: !!id,
  })

  const { data: competencies } = useQuery({
    queryKey: ['competencies-idp'],
    queryFn: () =>
      competenciesApi.list().then((list) =>
        list.map((c) => ({ value: c.id, label: c.name }))
      ),
  })

  const addGoalMutation = useMutation({
    mutationFn: (data: DevelopmentGoalCreate) => developmentPlansApi.addGoal(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['idp', id] })
      close()
      setGoalForm({})
    },
  })

  const deleteGoalMutation = useMutation({
    mutationFn: (goalId: string) => developmentPlansApi.deleteGoal(id!, goalId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['idp', id] }),
  })

  return (
    <Stack>
      <Paper p="lg" withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        {plan && (
          <Stack>
            <Group justify="space-between">
              <Title order={2}>
                ИПР: {plan.user.last_name} {plan.user.first_name}
              </Title>
              <Badge size="lg" color="blue">{plan.status}</Badge>
            </Group>
            <Text size="sm" c="dimmed">
              Создан: {plan.created_at.slice(0, 10)} · Согласование: {plan.approval}
            </Text>
          </Stack>
        )}
      </Paper>

      <Group justify="space-between">
        <Title order={3}>Цели</Title>
        {canCreateUser && (
          <Button size="sm" onClick={open}>Добавить цель</Button>
        )}
      </Group>

      <Paper withBorder>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Компетенция</Table.Th>
              <Table.Th>С уровня</Table.Th>
              <Table.Th>До уровня</Table.Th>
              <Table.Th>Статус</Table.Th>
              <Table.Th>Обязательная</Table.Th>
              <Table.Th>Срок</Table.Th>
              <Table.Th></Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {plan?.goals.map((goal) => (
              <Table.Tr key={goal.id}>
                <Table.Td>{goal.competency.name}</Table.Td>
                <Table.Td>{goal.current_level}</Table.Td>
                <Table.Td>{goal.target_level}</Table.Td>
                <Table.Td>
                  <Badge color={GOAL_STATUS_COLORS[goal.status] ?? 'gray'} size="sm">
                    {goal.status}
                  </Badge>
                </Table.Td>
                <Table.Td>{goal.is_mandatory ? 'Да' : 'Нет'}</Table.Td>
                <Table.Td>{goal.deadline ?? '—'}</Table.Td>
                <Table.Td>
                  {canCreateUser && (
                    <Button
                      size="xs"
                      color="red"
                      variant="subtle"
                      loading={deleteGoalMutation.isPending}
                      onClick={() => deleteGoalMutation.mutate(goal.id)}
                    >
                      Удалить
                    </Button>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal opened={opened} onClose={close} title="Добавить цель">
        <Stack>
          <Select
            label="Компетенция"
            data={competencies ?? []}
            value={goalForm.competency_id ?? null}
            onChange={(v) => setGoalForm((p) => ({ ...p, competency_id: v ?? undefined }))}
            searchable
            required
          />
          <Select
            label="Текущий уровень"
            data={LEVEL_LABELS.map((l, i) => ({ value: String(i), label: l }))}
            value={goalForm.current_level !== undefined ? String(goalForm.current_level) : null}
            onChange={(v) => setGoalForm((p) => ({ ...p, current_level: v ? Number(v) : undefined }))}
          />
          <Select
            label="Целевой уровень"
            data={LEVEL_LABELS.map((l, i) => ({ value: String(i), label: l }))}
            value={goalForm.target_level !== undefined ? String(goalForm.target_level) : null}
            onChange={(v) => setGoalForm((p) => ({ ...p, target_level: v ? Number(v) : undefined }))}
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={close}>Отмена</Button>
            <Button
              loading={addGoalMutation.isPending}
              disabled={!goalForm.competency_id || goalForm.current_level === undefined || goalForm.target_level === undefined}
              onClick={() => addGoalMutation.mutate(goalForm as DevelopmentGoalCreate)}
            >
              Добавить
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
