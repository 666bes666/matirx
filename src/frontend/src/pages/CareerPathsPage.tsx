import { useState } from 'react'
import {
  Badge,
  Button,
  Card,
  Group,
  LoadingOverlay,
  Modal,
  Paper,
  Select,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { careerPathsApi } from '../api/career_paths'
import { usersApi } from '../api/users'
import { usePermissions } from '../hooks/usePermissions'

export function CareerPathsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [opened, { open, close }] = useDisclosure(false)
  const { canCreateDepartment } = usePermissions()
  const [fromDept, setFromDept] = useState<string | null>(null)
  const [toDept, setToDept] = useState<string | null>(null)

  const { data: paths, isLoading } = useQuery({
    queryKey: ['career-paths'],
    queryFn: careerPathsApi.list,
  })

  const { data: departments } = useQuery({
    queryKey: ['departments-career'],
    queryFn: () =>
      usersApi.list().then((users) => {
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

  const createMutation = useMutation({
    mutationFn: () =>
      careerPathsApi.create({
        from_department_id: fromDept!,
        to_department_id: toDept!,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['career-paths'] })
      close()
    },
  })

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Карьерные треки</Title>
        {canCreateDepartment && (
          <Button onClick={open}>Добавить путь</Button>
        )}
      </Group>

      <Paper withBorder pos="relative" p="md">
        <LoadingOverlay visible={isLoading} />
        {paths?.length === 0 && (
          <Text c="dimmed" ta="center" py="xl">Карьерных путей нет</Text>
        )}
        <Stack gap="sm">
          {paths?.map((path) => (
            <Card
              key={path.id}
              withBorder
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/career-paths/${path.id}`)}
              p="md"
            >
              <Group justify="space-between">
                <Group gap="xs">
                  <Badge color="blue" size="md">{path.from_department.name}</Badge>
                  <Text fw={600}>→</Text>
                  <Badge color="green" size="md">{path.to_department.name}</Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  {path.requirements.length} требований
                </Text>
              </Group>
            </Card>
          ))}
        </Stack>
      </Paper>

      <Modal opened={opened} onClose={close} title="Новый карьерный путь">
        <Stack>
          <Select
            label="Из отдела"
            data={departments ?? []}
            value={fromDept}
            onChange={setFromDept}
            placeholder="Выберите отдел"
          />
          <Select
            label="В отдел"
            data={departments ?? []}
            value={toDept}
            onChange={setToDept}
            placeholder="Выберите отдел"
          />
          <Group justify="flex-end">
            <Button variant="outline" onClick={close}>Отмена</Button>
            <Button
              disabled={!fromDept || !toDept || fromDept === toDept}
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
