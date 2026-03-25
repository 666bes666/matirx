import { create } from 'zustand';

import type { UserBrief } from '../types/models';

interface AuthState {
  user: UserBrief | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: UserBrief, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  setAuth: (user, token) => set({ user, accessToken: token, isAuthenticated: true }),
  clearAuth: () => set({ user: null, accessToken: null, isAuthenticated: false }),
}));
