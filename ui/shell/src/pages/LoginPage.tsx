import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';

export default function LoginPage() {
  const login    = useAuthStore(s => s.login);
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <span className="text-5xl">🔱</span>
          <h1 className="mt-3 text-2xl font-bold tracking-tight">Trishul</h1>
          <p className="text-surface-200/50 text-sm mt-1">FCAPS Simulation Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-xs font-medium text-surface-200/60 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full bg-surface-800 border border-surface-200/10 rounded-lg px-3 py-2
                         text-sm text-white placeholder-surface-200/30 focus:outline-none
                         focus:ring-1 focus:ring-brand-500"
              placeholder="admin"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-surface-200/60 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-surface-800 border border-surface-200/10 rounded-lg px-3 py-2
                         text-sm text-white placeholder-surface-200/30 focus:outline-none
                         focus:ring-1 focus:ring-brand-500"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-severity-critical text-xs">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-500 hover:bg-brand-600 text-white font-medium
                       py-2 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
