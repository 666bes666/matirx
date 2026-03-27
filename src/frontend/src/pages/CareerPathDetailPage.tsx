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
  Switch,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { careerPathsApi } from '../api/career_paths'
import { competenciesApi } from '../api/competencies'
import { usePermissions } from '../hooks/usePermissions'
import type { CareerPathRequirementInput } from '../types/career_path'

const LEVEL_LABELS = ['0 — Нет', '1 — Новичок', '2 — Базовый', '3 — Продвинутый', '4 — Эксперт']

export function CareerPathDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [reqOpened, { open: openReq, close: closeReq }] = useDisclosure(false)
  const { canCreateDepartment } = usePermissions()
  const [reqForm, setReqForm] = useState<Partial<CareerPathRequirementInput & { is_mandatory: boolean }>>({})

  const { data: path, isLoading } = useQuery({
    queryKey: ['career-path', id],
    queryFn: () => careerPathsApi.get(id!),
    enabled: !!id,
  })

  const { data: competencies } = useQuery({
    queryKey: ['competencies-career'],
    queryFn: () =>
      competenciesApi.list().then((list) =>
        list.map((c) => ({ value: c.id, label: c.name }))
      ),
  })

  const setReqMutation = useMutation({
    mutationFn: (reqs: CareerPathRequirementInput[]) =>
      careerPathsApi.setRequirements(id!, reqs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['career-path', id] }),
  })

  const handleAddRequirement = () => {
    if (!reqForm.competency_id || reqForm.required_level === undefined) return
    const existing = path?.requirements ?? []
    const newReq: CareerPathRequirementInput = {
      competency_id: reqForm.competency_id,
      required_level: reqForm.required_level,
      is_mandatory: reqForm.is_mandatory ?? false,
    }
    const updated = [
      ...existing.map((r) => ({
        competency_id: r.competency_id,
        required_level: r.required_level,
        is_mandatory: r.is_mandatory,
      })),
      newReq,
    ]
    setReqMutation.mutate(updated)
    closeReq()
    setReqForm({})
  }

  const handleRemoveRequirement = (competencyId: string) => {
    const updated = (path?.requirements ?? [])
      .filter((r) => r.competency_id !== competencyId)
      .map((r) => ({
        competency_id: r.competency_id,
        required_level: r.required_level,
        is_mandatory: r.is_mandatory,
      }))
    setReqMutation.mutate(updated)
  }

  return (
    <Stack>
      <Paper p="lg" withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        {path && (
          <Stack>
            <Group>
              <Badge color="blue" size="lg">{path.from_department.name}</Badge>
              <Text fw={700} size="xl">→</Text>
              <Badge color="green" size="lg">{path.to_department.name}</Badge>
            </Group>
            <Text size="sm" c="dimmed">Карьерный переход · {path.requirements.length} требований</Text>
          </Stack>
        )}
      </Paper>

      <Group justify="space-between">
        <Title order={3}>Требования к компетенциям</Title>
        {canCreateDepartment && (
          <Button size="sm" onClick={openReq}>Добавить требование</Button>
        )}
      </Group>

      <Paper withBorder>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Компетенция</Table.Th>
              <Table.Th>Требуемый уровень</Table.Th>
              <Table.Th>Обязательная</Table.Th>
              {canCreateDepartment && <Table.Th></Table.Th>}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {path?.requirements.map((req) => (
              <Table.Tr key={req.id}>
                <Table.Td>{req.competency.name}</Table.Td>
                <Table.Td>
                  <Badge color="blue" size="sm">{LEVEL_LABELS[req.required_level]}</Badge>
                </Table.Td>
                <Table.Td>
                  {req.is_mandatory ? (
                    <Badge color="red" size="sm">Обязательная</Badge>
                  ) : (
                    <Badge color="gray" size="sm" variant="outline">Желательная</Badge>
                  )}
                </Table.Td>
                {canCreateDepartment && (
                  <Table.Td>
                    <Button
                      size="xs"
                      color="red"
                      variant="subtle"
                      onClick={() => handleRemoveRequirement(req.competency_id)}
                    >
                      Удалить
                    </Button>
                  </Table.Td>
                )}
              </Table.Tr>
            ))}
            {path?.requirements.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Text c="dimmed" ta="center" py="md">Нет требований</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal opened={reqOpened} onClose={closeReq} title="Добавить требование">
        <Stack>
          <Select
            label="Компетенция"
            data={competencies ?? []}
            value={reqForm.competency_id ?? null}
            onChange={(v) => setReqForm((p) => ({ ...p, competency_id: v ?? undefined }))}
            searchable
            required
          />
          <Select
            label="Требуемый уровень"
            data={LEVEL_LABELS.map((l, i) => ({ value: String(i), label: l }))}
            value={reqForm.required_level !== undefined ? String(reqForm.required_level) : null}
            onChange={(v) => setReqForm((p) => ({ ...p, required_level: v !== null ? Number(v) : undefined }))}
            required
          />
          <Switch
            label="Обязательная"
            checked={reqForm.is_mandatory ?? false}
            onChange={(e) => setReqForm((p) => ({ ...p, is_mandatory: e.currentTarget.checked }))}
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={closeReq}>Отмена</Button>
            <Button
              loading={setReqMutation.isPending}
              disabled={!reqForm.competency_id || reqForm.required_level === undefined}
              onClick={handleAddRequirement}
            >
              Добавить
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
