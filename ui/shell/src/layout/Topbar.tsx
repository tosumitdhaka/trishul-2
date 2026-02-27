import { Bell, LogOut } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useEventsStore } from '@/store/events';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

interface StatusDotProps { label: string; ok?: boolean; }
function StatusDot({ label, ok = true }: StatusDotProps) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-surface-200/50">
      <span className={clsx('w-1.5 h-1.5 rounded-full', ok ? 'bg-severity-cleared' : 'bg-severity-critical')} />
      {label}
    </span>
  );
}

export default function Topbar({ onNotifClick }: { onNotifClick: () => void }) {
  const user     = useAuthStore(s => s.user);
  const logout   = useAuthStore(s => s.logout);
  const unread   = useEventsStore(s => s.unread);
  const markRead = useEventsStore(s => s.markRead);
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  const handleBell = () => { markRead(); onNotifClick(); };

  return (
    <header className="h-12 flex-shrink-0 bg-surface-900 border-b border-surface-200/10
                       flex items-center px-4 gap-4">
      {/* System health dots */}
      <div className="flex items-center gap-4 text-xs">
        <StatusDot label="NATS" />
        <StatusDot label="Redis" />
        <StatusDot label="InfluxDB" />
      </div>

      <div className="flex-1" />

      {/* Notification bell */}
      <button
        onClick={handleBell}
        className="relative p-2 rounded-lg hover:bg-surface-200/10 text-surface-200/60 hover:text-white transition-colors"
      >
        <Bell size={16} />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1
                           bg-severity-critical rounded-full text-[10px] font-bold
                           flex items-center justify-center text-white">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {/* User */}
      <span className="text-sm text-surface-200/60 font-medium">{user?.username}</span>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="p-2 rounded-lg hover:bg-surface-200/10 text-surface-200/60 hover:text-white transition-colors"
      >
        <LogOut size={16} />
      </button>
    </header>
  );
}
