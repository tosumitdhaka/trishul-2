import { usePluginsStore } from '@/store/plugins';
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export default function PluginsPage() {
  const plugins     = usePluginsStore(s => s.plugins);
  const fetchPlugins = usePluginsStore(s => s.fetch);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Plugin Registry</h1>
        <button
          onClick={fetchPlugins}
          className="flex items-center gap-2 text-xs text-surface-200/50 hover:text-white
                     bg-surface-200/10 px-3 py-1.5 rounded-lg transition-colors"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-200/10">
              {['Plugin', 'Version', 'Domains', 'Protocols', 'Subjects', 'Health'].map(h => (
                <th key={h} className="text-left text-xs font-semibold uppercase tracking-wider
                                       text-surface-200/40 px-4 py-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-200/10">
            {plugins.map(p => (
              <tr key={p.name} className="hover:bg-surface-200/5 transition-colors">
                <td className="px-4 py-3 font-mono font-medium text-white">{p.name}</td>
                <td className="px-4 py-3 text-surface-200/50">{p.version}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {p.domains.map(d => (
                      <span key={d} className="badge-info">{d}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-surface-200/50 font-mono text-xs">
                  {p.protocols?.join(', ')}
                </td>
                <td className="px-4 py-3 text-surface-200/50">2</td>
                <td className="px-4 py-3">
                  {p.health === 'healthy'
                    ? <CheckCircle size={16} className="text-severity-cleared" />
                    : <XCircle    size={16} className="text-severity-critical" />
                  }
                </td>
              </tr>
            ))}
            {plugins.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-surface-200/30">
                  No plugins loaded. Start core-api to auto-discover plugins.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
