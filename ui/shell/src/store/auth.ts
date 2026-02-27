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
        const { access_token } = res.data;
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        // Decode payload (no verify — server already verified)
        const payload = JSON.parse(atob(access_token.split('.')[1]));
        set({ token: access_token, user: { username: payload.sub, role: payload.role ?? 'viewer' } });
      },

      logout: () => {
        delete axios.defaults.headers.common['Authorization'];
        set({ token: null, user: null });
      },
    }),
    {
      name: 'trishul-auth',
      // only persist token — user is re-derived from it
      partialize: (s) => ({ token: s.token, user: s.user }),
    },
  ),
);
