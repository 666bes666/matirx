import { useState } from 'react'
import {
  Alert,
  Button,
  FileInput,
  Group,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface ImportResult {
  created: number
  errors: string[]
}

function useImportMutation(url: string) {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const r = await apiClient.post<ImportResult>(url, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return r.data
    },
  })
}

function ImportSection({ title, url, template }: { title: string; url: string; template: string }) {
  const [file, setFile] = useState<File | null>(null)
  const mutation = useImportMutation(url)

  return (
    <Paper p="lg" withBorder>
      <Stack>
        <Text fw={600}>{title}</Text>
        <Text size="sm" c="dimmed">Формат: {template}</Text>
        <Group>
          <FileInput
            placeholder="Выберите CSV-файл"
            accept=".csv"
            value={file}
            onChange={setFile}
            w={300}
          />
          <Button
            disabled={!file}
            loading={mutation.isPending}
            onClick={() => file && mutation.mutate(file)}
          >
            Импортировать
          </Button>
        </Group>
        {mutation.isSuccess && (
          <Alert color="green" title="Результат импорта">
            Создано записей: {mutation.data.created}
            {mutation.data.errors.length > 0 && (
              <Stack mt="xs" gap="xs">
                <Text size="sm" fw={600}>Ошибки ({mutation.data.errors.length}):</Text>
                {mutation.data.errors.slice(0, 10).map((e, i) => (
                  <Text key={i} size="xs" c="red">{e}</Text>
                ))}
                {mutation.data.errors.length > 10 && (
                  <Text size="xs" c="dimmed">...и ещё {mutation.data.errors.length - 10}</Text>
                )}
              </Stack>
            )}
          </Alert>
        )}
        {mutation.isError && (
          <Alert color="red" title="Ошибка">
            Не удалось выполнить импорт
          </Alert>
        )}
      </Stack>
    </Paper>
  )
}

export function ImportPage() {
  return (
    <Stack>
      <Title order={2}>Импорт данных</Title>
      <ImportSection
        title="Импорт сотрудников"
        url="/import/users"
        template="email, first_name, last_name, password, role, department (опционально), patronymic (опционально), position (опционально)"
      />
      <ImportSection
        title="Импорт компетенций"
        url="/import/competencies"
        template="name, category, description (опционально)"
      />
    </Stack>
  )
}
