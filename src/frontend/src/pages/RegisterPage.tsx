import { useState } from 'react';
import { Anchor, Button, Container, Paper, PasswordInput, Text, TextInput, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { Link } from 'react-router-dom';
import axios from 'axios';

import { authApi } from '../api/auth';

export function RegisterPage() {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: { email: '', password: '', first_name: '', last_name: '', patronymic: '' },
    validate: {
      email: (v) => (/^\S+@\S+$/.test(v) ? null : 'Некорректный email'),
      password: (v) =>
        /^(?=.*[a-zA-Zа-яА-ЯёЁ])(?=.*\d).{8,}$/.test(v)
          ? null
          : 'Минимум 8 символов, 1 буква и 1 цифра',
      first_name: (v) => (v.trim() ? null : 'Обязательное поле'),
      last_name: (v) => (v.trim() ? null : 'Обязательное поле'),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setError('');
    setLoading(true);
    try {
      await authApi.register(values);
      setSuccess(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Ошибка регистрации');
      } else {
        setError('Ошибка соединения');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Container size={420} my={80}>
        <Title ta="center">Регистрация отправлена</Title>
        <Text ta="center" mt="md">
          Ожидайте активации учётной записи администратором.
        </Text>
        <Text ta="center" mt="sm">
          <Anchor component={Link} to="/login">
            Вернуться ко входу
          </Anchor>
        </Text>
      </Container>
    );
  }

  return (
    <Container size={420} my={80}>
      <Title ta="center">Регистрация</Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Уже есть аккаунт?{' '}
        <Anchor component={Link} to="/login" size="sm">
          Войти
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput label="Фамилия" required {...form.getInputProps('last_name')} />
          <TextInput label="Имя" required mt="md" {...form.getInputProps('first_name')} />
          <TextInput label="Отчество" mt="md" {...form.getInputProps('patronymic')} />
          <TextInput label="Email" placeholder="user@example.com" required mt="md" {...form.getInputProps('email')} />
          <PasswordInput label="Пароль" required mt="md" {...form.getInputProps('password')} />
          {error && (
            <Text c="red" size="sm" mt="sm">
              {error}
            </Text>
          )}
          <Button type="submit" fullWidth mt="xl" loading={loading}>
            Зарегистрироваться
          </Button>
        </form>
      </Paper>
    </Container>
  );
}
