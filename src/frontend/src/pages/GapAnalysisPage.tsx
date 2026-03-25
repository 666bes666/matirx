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
import { targetProfilesApi } from '../api/target_profiles'
import { usersApi } from '../api/users'

const LEVEL_LABELS = ['Нет', 'Новичок', 'Базовый', 'Продвинутый', 'Эксперт']
const LEVEL_COLORS = ['red', 'orange', 'yellow', 'lime', 'green']

function gapColor(current: number | null, required: number): string {
  if (current === null) return 'red'
  if (current >= required) return 'green'
  if (current >= required - 1) return 'yellow'
  return 'red'
}

export function GapAnalysisPage() {
  const { userId } = useParams<{ userId: string }>()
  const [profileId, setProfileId] = useState<string | null>(null)

  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => usersApi.get(userId!),
    enabled: !!userId,
  })

  const { data: profiles } = useQuery({
    queryKey: ['target-profiles'],
    queryFn: () => targetProfilesApi.list(),
  })

  const { data: gap, isLoading } = useQuery({
    queryKey: ['gap', profileId, userId],
    queryFn: () => targetProfilesApi.getGap(profileId!, userId!),
    enabled: !!profileId && !!userId,
  })

  const profileOptions = profiles?.map((p) => ({
    value: p.id,
    label: `${p.name}${p.position ? ` (${p.position})` : ''}`,
  })) ?? []

  const met = gap?.filter((g) => g.current_score !== null && g.current_score >= g.required_level).length ?? 0
  const total = gap?.length ?? 0

  return (
    <Stack>
      <Title order={2}>
        Gap-анализ{user ? `: ${user.last_name} ${user.first_name}` : ''}
      </Title>

      <Select
        placeholder="Выберите целевой профиль"
        data={profileOptions}
        value={profileId}
        onChange={setProfileId}
        w={400}
      />

      {gap && (
        <Group>
          <Text size="sm">
            Выполнено: <b>{met}</b> из <b>{total}</b>
          </Text>
          <Progress value={total > 0 ? (met / total) * 100 : 0} w={200} size="sm" />
        </Group>
      )}

      <Paper withBorder pos="relative">
        <LoadingOverlay visible={isLoading} />
        {gap && (
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Компетенция</Table.Th>
                <Table.Th>Обязательная</Table.Th>
                <Table.Th>Текущий уровень</Table.Th>
                <Table.Th>Требуемый уровень</Table.Th>
                <Table.Th>Разрыв</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {gap.map((item) => {
                const current = item.current_score
                const gap_val = current !== null ? item.required_level - current : null
                return (
                  <Table.Tr key={item.competency_id}>
                    <Table.Td>{item.competency_name}</Table.Td>
                    <Table.Td>
                      {item.is_mandatory ? (
                        <Badge color="red" size="sm">Обязательная</Badge>
                      ) : (
                        <Badge color="gray" size="sm" variant="outline">Желательная</Badge>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {current !== null ? (
                        <Badge color={LEVEL_COLORS[Math.round(current)]} size="sm">
                          {LEVEL_LABELS[Math.round(current)]} ({current.toFixed(1)})
                        </Badge>
                      ) : (
                        <Text c="dimmed" size="sm">Нет оценки</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Badge color={LEVEL_COLORS[item.required_level]} size="sm">
                        {LEVEL_LABELS[item.required_level]}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      {gap_val !== null ? (
                        <Badge color={gapColor(current, item.required_level)} size="sm">
                          {gap_val <= 0 ? '✓ выполнено' : `−${gap_val.toFixed(1)}`}
                        </Badge>
                      ) : (
                        <Badge color="red" size="sm">Нет данных</Badge>
                      )}
                    </Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>
        )}
        {!profileId && (
          <Text c="dimmed" ta="center" py="xl">
            Выберите целевой профиль для отображения gap-анализа
          </Text>
        )}
      </Paper>
    </Stack>
  )
}
