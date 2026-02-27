import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import ShellLayout from '@/layout/ShellLayout';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import PluginsPage from '@/pages/PluginsPage';
import SettingsPage from '@/pages/SettingsPage';
import ProfilePage from '@/pages/ProfilePage';
import RemotePage from '@/pages/RemotePage';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <ShellLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="plugins"  element={<PluginsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile"  element={<ProfilePage />} />
        {/* Phase 5: protocol plugin MFE pages loaded dynamically */}
        <Route path=":pluginName" element={<RemotePage />} />
      </Route>
    </Routes>
  );
}
