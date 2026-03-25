import { useState } from 'react'
import {
  Badge,
  Button,
  Group,
  LoadingOverlay,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { IconPlus, IconSearch } from '@tabler/icons-react'
import { useQuery } from '@tanstack/react-query'
import { competenciesApi } from '../api/competencies'
import { useAuthStore } from '../stores/authStore'
import { UserRole, CATEGORY_LABELS, CompetencyCategoryType } from '../types/enums'
import type { CompetencyRead } from '../types/competency'

const LEVEL_LABELS = ['Нет', 'Новичок', 'Базовый', 'Продвинутый', 'Эксперт']

export function CompetenciesPage() {
  const { user: currentUser } = useAuthStore()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)
  const [showArchived, setShowArchived] = useState(false)

  const { data: categories } = useQuery({
    queryKey: ['competency-categories'],
    queryFn: competenciesApi.listCategories,
  })

  const { data: competencies, isLoading } = useQuery({
    queryKey: ['competencies', search, categoryFilter, showArchived],
    queryFn: () =>
      competenciesApi.list({
        search: search || undefined,
        category_id: categoryFilter || undefined,
        is_archived: showArchived ? undefined : false,
      }),
  })

  const canManage = [UserRole.ADMIN, UserRole.HEAD, UserRole.DEPARTMENT_HEAD].includes(
    currentUser?.role as UserRole,
  )

  const categoryOptions = [
    { value: '', label: 'Все категории' },
    ...(categories?.map((c) => ({
      value: c.id,
      label: CATEGORY_LABELS[c.name as CompetencyCategoryType] ?? c.name,
    })) ?? []),
  ]

  const byCategory = (competencies ?? []).reduce<Record<string, CompetencyRead[]>>((acc, comp) => {
    const catId = comp.category_id
    if (!acc[catId]) acc[catId] = []
    acc[catId].push(comp)
    return acc
  }, {})

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Каталог компетенций</Title>
        {canManage && (
          <Button leftSection={<IconPlus size={16} />} size="sm">
            Добавить компетенцию
          </Button>
        )}
      </Group>

      <Group>
        <TextInput
          placeholder="Поиск по названию"
          leftSection={<IconSearch size={16} />}
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          style={{ flex: 1 }}
        />
        <Select
          data={categoryOptions}
          value={categoryFilter}
          onChange={setCategoryFilter}
          placeholder="Категория"
          clearable
          style={{ width: 220 }}
        />
        <Button
          variant={showArchived ? 'filled' : 'outline'}
          size="sm"
          onClick={() => setShowArchived((v) => !v)}
        >
          {showArchived ? 'Скрыть архивные' : 'Показать архивные'}
        </Button>
      </Group>

      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={isLoading} />

        {Object.entries(byCategory).map(([catId, comps]) => {
          const catName = comps[0]?.category?.name
          const catLabel = catName
            ? (CATEGORY_LABELS[catName as CompetencyCategoryType] ?? catName)
            : catId
          return (
            <Stack key={catId} mb="lg">
              <Text fw={600} size="md" tt="uppercase" c="dimmed">
                {catLabel}
              </Text>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Название</Table.Th>
                    <Table.Th>Тип</Table.Th>
                    <Table.Th>Уровни</Table.Th>
                    <Table.Th>Отделы</Table.Th>
                    <Table.Th>Статус</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {comps.map((comp) => (
                    <Table.Tr key={comp.id}>
                      <Table.Td>
                        <Text size="sm" fw={500}>
                          {comp.name}
                        </Text>
                        {comp.description && (
                          <Text size="xs" c="dimmed">
                            {comp.description}
                          </Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {comp.is_common ? (
                          <Badge color="blue" variant="light" size="xs">
                            Общая
                          </Badge>
                        ) : (
                          <Badge color="gray" variant="light" size="xs">
                            Отдельная
                          </Badge>
                        )}
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs" c="dimmed">
                          {comp.level_criteria.length > 0
                            ? `${comp.level_criteria.length} из ${LEVEL_LABELS.length}`
                            : 'Не заданы'}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs">{comp.departments.map((d) => d.name).join(', ') || '—'}</Text>
                      </Table.Td>
                      <Table.Td>
                        {comp.is_archived ? (
                          <Badge color="gray" variant="dot" size="sm">
                            Архив
                          </Badge>
                        ) : (
                          <Badge color="green" variant="dot" size="sm">
                            Активна
                          </Badge>
                        )}
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Stack>
          )
        })}

        {!isLoading && !competencies?.length && (
          <Text ta="center" c="dimmed" py="xl">
            Нет компетенций
          </Text>
        )}
      </div>
    </Stack>
  )
}
