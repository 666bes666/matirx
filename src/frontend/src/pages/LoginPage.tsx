import { useState } from 'react';
import { Anchor, Button, Container, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { Link } from 'react-router-dom';
import axios from 'axios';

import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email: (v) => (/^\S+@\S+$/.test(v) ? null : 'Некорректный email'),
      password: (v) => (v.length > 0 ? null : 'Введите пароль'),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setError('');
    setLoading(true);
    try {
      await login(values.email, values.password);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Ошибка авторизации');
      } else {
        setError('Ошибка соединения');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={80}>
      <Title ta="center">Matrix</Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Нет аккаунта?{' '}
        <Anchor component={Link} to="/register" size="sm">
          Зарегистрироваться
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput label="Email" placeholder="user@example.com" required {...form.getInputProps('email')} />
          <PasswordInput label="Пароль" placeholder="Ваш пароль" required mt="md" {...form.getInputProps('password')} />
          {error && (
            <Text c="red" size="sm" mt="sm">
              {error}
            </Text>
          )}
          <Button type="submit" fullWidth mt="xl" loading={loading}>
            Войти
          </Button>
        </form>
      </Paper>
    </Container>
  );
}
