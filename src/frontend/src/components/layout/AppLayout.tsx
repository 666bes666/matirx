import { AppShell, Burger, Group, Text, Button, Badge } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconLogout } from '@tabler/icons-react';
import { NavLink, Outlet } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';
import { ROLE_LABELS } from '../../types/enums';

export function AppLayout() {
  const [opened, { toggle }] = useDisclosure();
  const { user, logout } = useAuth();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text size="lg" fw={700}>
              Matrix
            </Text>
          </Group>
          <Group>
            {user && (
              <>
                <Text size="sm">
                  {user.first_name} {user.last_name}
                </Text>
                <Badge variant="light">{ROLE_LABELS[user.role]}</Badge>
              </>
            )}
            <Button
              variant="subtle"
              size="compact-sm"
              leftSection={<IconLogout size={16} />}
              onClick={logout}
            >
              Выход
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <NavLink to="/" style={{ textDecoration: 'none' }}>
          <Text size="sm" c="dimmed" py="xs">
            Главная
          </Text>
        </NavLink>
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
