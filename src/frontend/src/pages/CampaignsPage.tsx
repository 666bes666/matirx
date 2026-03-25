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
  TextInput,
  Title,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { assessmentsApi } from '../api/assessments'
import { usePermissions } from '../hooks/usePermissions'
import { CampaignStatus } from '../types/enums'
import type { CampaignCreate } from '../types/assessment'

const STATUS_COLORS: Record<CampaignStatus, string> = {
  [CampaignStatus.DRAFT]: 'gray',
  [CampaignStatus.ACTIVE]: 'blue',
  [CampaignStatus.COLLECTING]: 'cyan',
  [CampaignStatus.CALIBRATION]: 'orange',
  [CampaignStatus.FINALIZED]: 'green',
  [CampaignStatus.ARCHIVED]: 'dark',
}

const STATUS_LABELS: Record<CampaignStatus, string> = {
  [CampaignStatus.DRAFT]: 'Черновик',
  [CampaignStatus.ACTIVE]: 'Активна',
  [CampaignStatus.COLLECTING]: 'Сбор оценок',
  [CampaignStatus.CALIBRATION]: 'Калибровка',
  [CampaignStatus.FINALIZED]: 'Завершена',
  [CampaignStatus.ARCHIVED]: 'В архиве',
}

export function CampaignsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [opened, { open, close }] = useDisclosure(false)
  const { canCreateCampaign } = usePermissions()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const [form, setForm] = useState<Partial<CampaignCreate>>({
    scope: 'division',
  })

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns', statusFilter],
    queryFn: () => assessmentsApi.listCampaigns(statusFilter ?? undefined),
  })

  const createMutation = useMutation({
    mutationFn: (data: CampaignCreate) => assessmentsApi.createCampaign(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      close()
      setForm({ scope: 'division' })
    },
  })

  const handleSubmit = () => {
    if (!form.name || !form.start_date || !form.end_date || !form.scope) return
    createMutation.mutate(form as CampaignCreate)
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Кампании оценки</Title>
        {canCreateCampaign && (
          <Button onClick={open}>Создать кампанию</Button>
        )}
      </Group>

      <Select
        placeholder="Все статусы"
        data={Object.entries(STATUS_LABELS).map(([v, l]) => ({ value: v, label: l }))}
        value={statusFilter}
        onChange={setStatusFilter}
        clearable
        w={200}
      />

      <Paper withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Название</Table.Th>
              <Table.Th>Статус</Table.Th>
              <Table.Th>Начало</Table.Th>
              <Table.Th>Конец</Table.Th>
              <Table.Th>Охват</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {campaigns?.map((c) => (
              <Table.Tr
                key={c.id}
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/campaigns/${c.id}`)}
              >
                <Table.Td>{c.name}</Table.Td>
                <Table.Td>
                  <Badge color={STATUS_COLORS[c.status as CampaignStatus]}>
                    {STATUS_LABELS[c.status as CampaignStatus] ?? c.status}
                  </Badge>
                </Table.Td>
                <Table.Td>{c.start_date}</Table.Td>
                <Table.Td>{c.end_date}</Table.Td>
                <Table.Td>{c.scope}</Table.Td>
              </Table.Tr>
            ))}
            {campaigns?.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Text c="dimmed" ta="center" py="md">
                    Кампаний нет
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal opened={opened} onClose={close} title="Новая кампания оценки" size="md">
        <Stack>
          <TextInput
            label="Название"
            required
            value={form.name ?? ''}
            onChange={(e) => setForm((p) => ({ ...p, name: e.currentTarget.value }))}
          />
          <Select
            label="Охват"
            required
            data={[
              { value: 'division', label: 'Всё управление' },
              { value: 'department', label: 'Отдел' },
              { value: 'team', label: 'Команда' },
            ]}
            value={form.scope ?? 'division'}
            onChange={(v) => setForm((p) => ({ ...p, scope: v as CampaignCreate['scope'] }))}
          />
          <TextInput
            label="Дата начала (ГГГГ-ММ-ДД)"
            placeholder="2026-04-01"
            value={form.start_date ?? ''}
            onChange={(e) => setForm((p) => ({ ...p, start_date: e.currentTarget.value as unknown as Date }))}
          />
          <TextInput
            label="Дата окончания (ГГГГ-ММ-ДД)"
            placeholder="2026-04-30"
            value={form.end_date ?? ''}
            onChange={(e) => setForm((p) => ({ ...p, end_date: e.currentTarget.value as unknown as Date }))}
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={close}>Отмена</Button>
            <Button loading={createMutation.isPending} onClick={handleSubmit}>
              Создать
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
