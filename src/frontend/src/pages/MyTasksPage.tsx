import {
  Badge,
  Group,
  LoadingOverlay,
  Paper,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { assessmentsApi } from '../api/assessments'

export function MyTasksPage() {
  const navigate = useNavigate()

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['my-tasks'],
    queryFn: assessmentsApi.listMyTasks,
  })

  const pending = tasks?.filter((t) => t.status !== 'completed') ?? []

  return (
    <Stack>
      <Title order={2}>Мои задачи</Title>
      <Text c="dimmed" size="sm">
        Оценки, которые вам нужно заполнить
      </Text>

      <Paper withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Оцениваемый</Table.Th>
              <Table.Th>Тип оценки</Table.Th>
              <Table.Th>Статус</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {pending.map((t) => (
              <Table.Tr
                key={t.id}
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/assessments/${t.id}`)}
              >
                <Table.Td>
                  {t.assessee.last_name} {t.assessee.first_name}
                </Table.Td>
                <Table.Td>{t.assessor_type}</Table.Td>
                <Table.Td>
                  <Badge color={t.status === 'completed' ? 'green' : 'orange'}>
                    {t.status}
                  </Badge>
                </Table.Td>
              </Table.Tr>
            ))}
            {pending.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={3}>
                  <Text c="dimmed" ta="center" py="md">
                    Нет незавершённых задач
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  )
}
