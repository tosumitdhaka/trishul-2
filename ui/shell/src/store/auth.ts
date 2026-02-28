import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

interface User {
  username: string;
  role: string;
}

interface AuthState {
  token:   string | null;
  user:    User | null;
  login:   (username: string, password: string) => Promise<void>;
  logout:  () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user:  null,

      login: async (username, password) => {
        const res = await axios.post('/api/v1/auth/login', { username, password });
        const { access_token } = res.data.data;
        if (!access_token) throw new Error('No access token in response');
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        // Decode payload to get role; use the login username directly (not payload.sub
        // which is the internal seed ID, not the display name).
        const payload = JSON.parse(atob(access_token.split('.')[1]));
        set({
          token: access_token,
          user: { username, role: payload.roles?.[0] ?? 'viewer' },
        });
      },

      logout: () => {
        delete axios.defaults.headers.common['Authorization'];
        set({ token: null, user: null });
      },
    }),
    {
      name: 'trishul-auth',
      partialize: (s) => ({ token: s.token, user: s.user }),
    },
  ),
);
