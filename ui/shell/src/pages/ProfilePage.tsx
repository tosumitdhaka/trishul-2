import { useAuthStore } from '@/store/auth';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const user     = useAuthStore(s => s.user);
  const logout   = useAuthStore(s => s.logout);
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Profile</h1>
      <div className="card space-y-3">
        {[['Username', user?.username], ['Role', user?.role]].map(([k, v]) => (
          <div key={k} className="flex items-center justify-between py-2
                                   border-b border-surface-200/10 last:border-0">
            <span className="text-sm text-surface-200/60">{k}</span>
            <span className="text-sm font-medium">{v ?? '—'}</span>
          </div>
        ))}
        <button
          onClick={() => { logout(); navigate('/login'); }}
          className="w-full mt-2 bg-severity-critical/20 hover:bg-severity-critical/30
                     text-severity-critical font-medium py-2 rounded-lg text-sm transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}
