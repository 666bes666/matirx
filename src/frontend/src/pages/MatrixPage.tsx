import { useState } from 'react'
import { Button, Group, LoadingOverlay, Paper, Select, Stack, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { analyticsApi } from '../api/analytics'
import { usersApi } from '../api/users'
import { competenciesApi } from '../api/competencies'
import { exportApi } from '../api/export'
import { MatrixGrid } from '../components/assessment/MatrixGrid'

export function MatrixPage() {
  const navigate = useNavigate()
  const [departmentId, setDepartmentId] = useState<string | null>(null)
  const [teamId, setTeamId] = useState<string | null>(null)
  const [categoryId, setCategoryId] = useState<string | null>(null)

  const { data: matrix, isLoading } = useQuery({
    queryKey: ['matrix', departmentId, teamId, categoryId],
    queryFn: () =>
      analyticsApi.getMatrix({
        department_id: departmentId ?? undefined,
        team_id: teamId ?? undefined,
        category_id: categoryId ?? undefined,
      }),
  })

  const { data: departments } = useQuery({
    queryKey: ['users-departments'],
    queryFn: () => usersApi.list().then((users) => {
      const seen = new Set<string>()
      const result: { value: string; label: string }[] = []
      for (const u of users) {
        if (u.department && !seen.has(u.department.id)) {
          seen.add(u.department.id)
          result.push({ value: u.department.id, label: u.department.name })
        }
      }
      return result
    }),
  })

  const { data: categories } = useQuery({
    queryKey: ['competency-categories-matrix'],
    queryFn: () =>
      competenciesApi.listCategories().then((cats) =>
        cats.map((c) => ({ value: c.id, label: c.name }))
      ),
  })

  const handleCellClick = (userId: string, _competencyId: string) => {
    navigate(`/users/${userId}`)
  }

  return (
    <Stack>
      <Title order={2}>Матрица компетенций</Title>

      <Group>
        <Select
          placeholder="Все отделы"
          data={departments ?? []}
          value={departmentId}
          onChange={(v) => { setDepartmentId(v); setTeamId(null) }}
          clearable
          w={220}
        />
        <Select
          placeholder="Все категории"
          data={categories ?? []}
          value={categoryId}
          onChange={setCategoryId}
          clearable
          w={220}
        />
        <Button
          variant="outline"
          onClick={() => exportApi.downloadMatrixXlsx()}
        >
          Экспорт Excel
        </Button>
      </Group>

      <Paper p="md" withBorder pos="relative" style={{ minHeight: 200 }}>
        <LoadingOverlay visible={isLoading} />
        {matrix && (
          <MatrixGrid data={matrix} onCellClick={handleCellClick} />
        )}
      </Paper>
    </Stack>
  )
}
