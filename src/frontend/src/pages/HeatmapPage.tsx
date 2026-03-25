import { useState } from 'react'
import { Box, LoadingOverlay, Paper, Select, Stack, Text, Title, Tooltip } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analytics'
import { competenciesApi } from '../api/competencies'

const SCORE_COLOR = (score: number | null | undefined): string => {
  if (score === null || score === undefined) return '#dee2e6'
  const level = Math.round(score)
  const colors = ['#c92a2a', '#e67700', '#fab005', '#2f9e44', '#1971c2']
  return colors[Math.min(4, Math.max(0, level))]
}

export function HeatmapPage() {
  const [categoryId, setCategoryId] = useState<string | null>(null)

  const { data: heatmap, isLoading } = useQuery({
    queryKey: ['heatmap', categoryId],
    queryFn: () => analyticsApi.getHeatmap({ category_id: categoryId ?? undefined }),
  })

  const { data: categories } = useQuery({
    queryKey: ['competency-categories-heatmap'],
    queryFn: () =>
      competenciesApi.listCategories().then((cats) =>
        cats.map((c) => ({ value: c.id, label: c.name }))
      ),
  })

  return (
    <Stack>
      <Title order={2}>Тепловая карта компетенций</Title>
      <Text c="dimmed" size="sm">Средние оценки по отделам</Text>

      <Select
        placeholder="Все категории"
        data={categories ?? []}
        value={categoryId}
        onChange={setCategoryId}
        clearable
        w={240}
      />

      <Paper p="md" withBorder pos="relative" style={{ minHeight: 200 }}>
        <LoadingOverlay visible={isLoading} />
        {heatmap && heatmap.departments.length > 0 && heatmap.competencies.length > 0 && (
          <Box style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{
                    minWidth: 180,
                    padding: '8px',
                    textAlign: 'left',
                    borderBottom: '1px solid var(--mantine-color-gray-3)',
                  }}>
                    <Text size="sm" fw={600}>Отдел</Text>
                  </th>
                  {heatmap.competencies.map((comp) => (
                    <th key={comp.id} style={{
                      width: 40,
                      padding: '4px',
                      borderBottom: '1px solid var(--mantine-color-gray-3)',
                      textAlign: 'center',
                    }}>
                      <Tooltip label={comp.name} withArrow position="top">
                        <Text size="xs" style={{
                          writingMode: 'vertical-rl',
                          transform: 'rotate(180deg)',
                          whiteSpace: 'nowrap',
                          maxHeight: 100,
                          overflow: 'hidden',
                          cursor: 'default',
                        }}>
                          {comp.name}
                        </Text>
                      </Tooltip>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmap.departments.map((dept) => (
                  <tr key={dept.id}>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
                      <Text size="sm" fw={500}>{dept.name}</Text>
                    </td>
                    {heatmap.competencies.map((comp) => {
                      const score = heatmap.averages[dept.id]?.[comp.id]
                      return (
                        <td key={comp.id} style={{ padding: '4px', borderBottom: '1px solid var(--mantine-color-gray-2)', textAlign: 'center' }}>
                          <Tooltip
                            label={`${dept.name} — ${comp.name}: ${score !== null && score !== undefined ? score.toFixed(1) : 'нет данных'}`}
                            withArrow
                          >
                            <Box style={{
                              width: 32,
                              height: 32,
                              backgroundColor: SCORE_COLOR(score),
                              borderRadius: 4,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              margin: '0 auto',
                            }}>
                              {score !== null && score !== undefined && (
                                <Text size="xs" c="white" fw={700}>{score.toFixed(1)}</Text>
                              )}
                            </Box>
                          </Tooltip>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        )}
        {heatmap && (heatmap.departments.length === 0 || heatmap.competencies.length === 0) && (
          <Text c="dimmed" ta="center" py="xl">Нет данных для отображения</Text>
        )}
      </Paper>
    </Stack>
  )
}
