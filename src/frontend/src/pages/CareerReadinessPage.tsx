import { useState } from 'react'
import {
  Badge,
  Group,
  LoadingOverlay,
  Paper,
  Progress,
  Select,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { careerPathsApi } from '../api/career_paths'

const LEVEL_LABELS = ['Нет', 'Новичок', 'Базовый', 'Продвинутый', 'Эксперт']

export function CareerReadinessPage() {
  const { userId } = useParams<{ userId: string }>()
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null)

  const { data: paths } = useQuery({
    queryKey: ['career-paths-readiness'],
    queryFn: careerPathsApi.list,
  })

  const { data: readiness, isLoading } = useQuery({
    queryKey: ['readiness', selectedPathId, userId],
    queryFn: () => careerPathsApi.getReadiness(selectedPathId!, userId!),
    enabled: !!selectedPathId && !!userId,
  })

  const pathOptions = paths?.map((p) => ({
    value: p.id,
    label: `${p.from_department.name} → ${p.to_department.name}`,
  })) ?? []

  return (
    <Stack>
      <Title order={2}>Готовность к переходу</Title>

      <Select
        placeholder="Выберите карьерный путь"
        data={pathOptions}
        value={selectedPathId}
        onChange={setSelectedPathId}
        w={400}
      />

      {readiness && (
        <Paper p="md" withBorder>
          <Stack>
            <Group justify="space-between">
              <Group gap="xs">
                <Badge
                  size="lg"
                  color={readiness.is_ready ? 'green' : 'red'}
                >
                  {readiness.is_ready ? 'Готов к переходу' : 'Не готов'}
                </Badge>
                {!readiness.mandatory_met && (
                  <Badge size="sm" color="red" variant="outline">
                    Не все обязательные выполнены
                  </Badge>
                )}
              </Group>
              <Text size="sm" fw={600}>{readiness.readiness_pct}%</Text>
            </Group>
            <Progress
              value={readiness.readiness_pct}
              color={readiness.is_ready ? 'green' : 'orange'}
              size="md"
            />
          </Stack>
        </Paper>
      )}

      <Paper withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        {readiness && (
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Компетенция</Table.Th>
                <Table.Th>Тип</Table.Th>
                <Table.Th>Текущий</Table.Th>
                <Table.Th>Требуется</Table.Th>
                <Table.Th>Статус</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {readiness.items.map((item) => (
                <Table.Tr key={item.competency_id}>
                  <Table.Td>{item.competency_name}</Table.Td>
                  <Table.Td>
                    {item.is_mandatory ? (
                      <Badge color="red" size="xs">Обяз.</Badge>
                    ) : (
                      <Badge color="gray" size="xs" variant="outline">Желат.</Badge>
                    )}
                  </Table.Td>
                  <Table.Td>
                    {item.current_score !== null
                      ? `${LEVEL_LABELS[Math.round(item.current_score)]} (${item.current_score.toFixed(1)})`
                      : <Text c="dimmed" size="sm">Нет оценки</Text>
                    }
                  </Table.Td>
                  <Table.Td>{LEVEL_LABELS[item.required_level]}</Table.Td>
                  <Table.Td>
                    <Badge color={item.is_met ? 'green' : 'red'} size="sm">
                      {item.is_met ? '✓' : `−${item.gap?.toFixed(1)}`}
                    </Badge>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
        {!selectedPathId && (
          <Text c="dimmed" ta="center" py="xl">Выберите карьерный путь</Text>
        )}
      </Paper>
    </Stack>
  )
}
