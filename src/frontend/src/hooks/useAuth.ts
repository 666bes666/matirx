import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { notifications } from '@mantine/notifications';

import { authApi } from '../api/auth';
import { useAuthStore } from '../stores/authStore';

export function useAuth() {
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const login = useCallback(
    async (email: string, password: string) => {
      const { data } = await authApi.login(email, password);
      setAuth(data.user, data.access_token);
      navigate('/');
    },
    [setAuth, navigate],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    clearAuth();
    navigate('/login');
  }, [clearAuth, navigate]);

  const tryRefresh = useCallback(async () => {
    try {
      const { data } = await authApi.refresh();
      const meResp = await authApi.me();
      setAuth(meResp.data, data.access_token);
      return true;
    } catch {
      clearAuth();
      return false;
    }
  }, [setAuth, clearAuth]);

  return { user, isAuthenticated, login, logout, tryRefresh };
}
