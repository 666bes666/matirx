import {
  Badge,
  Button,
  Group,
  LoadingOverlay,
  Paper,
  Progress,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { assessmentsApi } from '../api/assessments'
import { usePermissions } from '../hooks/usePermissions'
import { CampaignStatus } from '../types/enums'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  active: 'Активна',
  collecting: 'Сбор оценок',
  calibration: 'Калибровка',
  finalized: 'Завершена',
  archived: 'В архиве',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'gray',
  active: 'blue',
  collecting: 'cyan',
  calibration: 'orange',
  finalized: 'green',
  archived: 'dark',
}

export function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { canCreateCampaign } = usePermissions()

  const { data: campaign, isLoading } = useQuery({
    queryKey: ['campaign', id],
    queryFn: () => assessmentsApi.getCampaign(id!),
    enabled: !!id,
  })

  const { data: progress } = useQuery({
    queryKey: ['campaign-progress', id],
    queryFn: () => assessmentsApi.getCampaignProgress(id!),
    enabled: !!id,
  })

  const { data: assessments } = useQuery({
    queryKey: ['assessments', id],
    queryFn: () => assessmentsApi.listAssessments({ campaign_id: id }),
    enabled: !!id,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['campaign', id] })
    queryClient.invalidateQueries({ queryKey: ['campaign-progress', id] })
  }

  const activateMutation = useMutation({
    mutationFn: () => assessmentsApi.activateCampaign(id!),
    onSuccess: invalidate,
  })

  const closeMutation = useMutation({
    mutationFn: () => assessmentsApi.closeCampaign(id!),
    onSuccess: invalidate,
  })

  const finalizeMutation = useMutation({
    mutationFn: () => assessmentsApi.finalizeCampaign(id!),
    onSuccess: invalidate,
  })

  const archiveMutation = useMutation({
    mutationFn: () => assessmentsApi.archiveCampaign(id!),
    onSuccess: invalidate,
  })

  return (
    <Stack>
      <Paper p="lg" withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        {campaign && (
          <Stack>
            <Group justify="space-between">
              <Title order={2}>{campaign.name}</Title>
              <Badge size="lg" color={STATUS_COLORS[campaign.status]}>
                {STATUS_LABELS[campaign.status]}
              </Badge>
            </Group>
            <Text size="sm" c="dimmed">
              {campaign.start_date} — {campaign.end_date} · Охват: {campaign.scope}
            </Text>

            {progress && (
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text size="sm">Прогресс оценок</Text>
                  <Text size="sm" fw={600}>
                    {progress.completed_assessments} / {progress.total_assessments} ({progress.completion_pct}%)
                  </Text>
                </Group>
                <Progress value={progress.completion_pct} size="md" />
              </Stack>
            )}

            {canCreateCampaign && (
              <Group>
                {campaign.status === CampaignStatus.DRAFT && (
                  <Button
                    loading={activateMutation.isPending}
                    onClick={() => activateMutation.mutate()}
                  >
                    Активировать
                  </Button>
                )}
                {(campaign.status === CampaignStatus.ACTIVE || campaign.status === CampaignStatus.COLLECTING) && (
                  <Button
                    color="orange"
                    loading={closeMutation.isPending}
                    onClick={() => closeMutation.mutate()}
                  >
                    Перейти к калибровке
                  </Button>
                )}
                {campaign.status !== CampaignStatus.FINALIZED &&
                  campaign.status !== CampaignStatus.ARCHIVED && (
                    <Button
                      color="green"
                      loading={finalizeMutation.isPending}
                      onClick={() => finalizeMutation.mutate()}
                    >
                      Финализировать
                    </Button>
                  )}
                {campaign.status === CampaignStatus.FINALIZED && (
                  <Button
                    color="gray"
                    variant="outline"
                    loading={archiveMutation.isPending}
                    onClick={() => archiveMutation.mutate()}
                  >
                    В архив
                  </Button>
                )}
              </Group>
            )}
          </Stack>
        )}
      </Paper>

      <Paper withBorder>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Оцениваемый</Table.Th>
              <Table.Th>Оценщик</Table.Th>
              <Table.Th>Тип</Table.Th>
              <Table.Th>Статус</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {assessments?.map((a) => (
              <Table.Tr key={a.id}>
                <Table.Td>{a.assessee.last_name} {a.assessee.first_name}</Table.Td>
                <Table.Td>{a.assessor.last_name} {a.assessor.first_name}</Table.Td>
                <Table.Td>{a.assessor_type}</Table.Td>
                <Table.Td>
                  <Badge color={a.status === 'completed' ? 'green' : 'gray'}>
                    {a.status}
                  </Badge>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  )
}
