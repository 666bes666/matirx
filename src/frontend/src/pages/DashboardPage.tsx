import { Card, Grid, Text, Title } from '@mantine/core';

import { useAuthStore } from '../stores/authStore';
import { ROLE_LABELS } from '../types/enums';

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  if (!user) return null;

  return (
    <>
      <Title order={2} mb="lg">
        Добро пожаловать, {user.first_name}!
      </Title>

      <Grid>
        <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text fw={500} size="lg">
              Профиль
            </Text>
            <Text size="sm" c="dimmed" mt="sm">
              {user.first_name} {user.last_name}
            </Text>
            <Text size="sm" c="dimmed">
              {user.email}
            </Text>
            <Text size="sm" c="dimmed">
              Роль: {ROLE_LABELS[user.role]}
            </Text>
          </Card>
        </Grid.Col>
      </Grid>
    </>
  );
}
