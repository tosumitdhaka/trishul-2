import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import NotificationPanel from './NotificationPanel';
import { startWebSocket, stopWebSocket } from '@/ws/client';
import { usePluginsStore } from '@/store/plugins';
import { useAuthStore } from '@/store/auth';
import { useState } from 'react';

export default function ShellLayout() {
  const fetchPlugins = usePluginsStore(s => s.fetch);
  const token        = useAuthStore(s => s.token);
  const [notifOpen, setNotifOpen] = useState(false);

  useEffect(() => {
    if (token) {
      fetchPlugins();
      startWebSocket();
    }
    return () => stopWebSocket();
  }, [token]);

  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Topbar onNotifClick={() => setNotifOpen(o => !o)} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      {notifOpen && <NotificationPanel onClose={() => setNotifOpen(false)} />}
    </div>
  );
}
