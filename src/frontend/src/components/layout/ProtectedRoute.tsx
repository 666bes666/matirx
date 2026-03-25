import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { Center, Loader } from '@mantine/core';

import { useAuthStore } from '../../stores/authStore';
import { authApi } from '../../api/auth';

export function ProtectedRoute() {
  const { isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const [loading, setLoading] = useState(!isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) {
      authApi
        .refresh()
        .then(async ({ data }) => {
          const meResp = await authApi.me();
          setAuth(meResp.data, data.access_token);
        })
        .catch(() => {
          clearAuth();
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isAuthenticated, setAuth, clearAuth]);

  if (loading) {
    return (
      <Center h="100vh">
        <Loader size="lg" />
      </Center>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
