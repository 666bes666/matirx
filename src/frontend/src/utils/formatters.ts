import dayjs from 'dayjs';

export function formatDate(date: string | null): string {
  if (!date) return '—';
  return dayjs(date).format('DD.MM.YYYY');
}

export function formatDateTime(date: string | null): string {
  if (!date) return '—';
  return dayjs(date).format('DD.MM.YYYY HH:mm');
}

export function fullName(firstName: string, lastName: string, patronymic?: string | null): string {
  const parts = [lastName, firstName];
  if (patronymic) parts.push(patronymic);
  return parts.join(' ');
}
