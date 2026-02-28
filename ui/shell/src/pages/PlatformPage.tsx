/**
 * Platform Manager — operational visibility into NATS streams, service health, and storage.
 * Polls /health and /api/v1/platform/streams every 10 s.
 */
import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, ExternalLink } from 'lucide-react';
import clsx from 'clsx';

interface HealthDep  { status: string; detail?: string; }
interface StreamInfo {
  name: string; subjects: string[];
  messages: number; bytes: number; consumers: number;
}
interface PlatformData {
  health:   Record<string, HealthDep>;
  overall:  string;
  streams:  StreamInfo[];
  totalMsg: number;
  totalBytes: number;
  serverId: string;
}

const SERVICE_LINKS: Record<string, string> = {
  influxdb:     'http://localhost:8086',
  victorialogs: '/vlogs/select/vmui',
};

function fmt(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function PlatformPage() {
  const [data,    setData]    = useState<PlatformData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastAt,  setLastAt]  = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [hr, sr] = await Promise.all([
        fetch('/health').then(r => r.json()),
        fetch('/api/v1/platform/streams').then(r => r.json()),
      ]);
      setData({
        health:     hr.dependencies ?? {},
        overall:    hr.status ?? 'unknown',
        streams:    sr.data?.streams    ?? [],
        totalMsg:   sr.data?.total_messages  ?? 0,
        totalBytes: sr.data?.total_bytes     ?? 0,
        serverId:   sr.data?.server_id       ?? '',
      });
      setLastAt(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 10_000);
    return () => clearInterval(t);
  }, [refresh]);

  const overallColor = data?.overall === 'healthy' ? 'text-green-400'
                     : data?.overall === 'degraded'  ? 'text-yellow-400'
                     : 'text-red-400';

  return (
    <div className="space-y-6 text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Platform Manager</h1>
          <p className="text-white/40 text-xs mt-0.5">
            {lastAt ? `Last refreshed ${lastAt.toLocaleTimeString()}` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data && (
            <span className={clsx('text-sm font-semibold capitalize', overallColor)}>
              ● {data.overall}
            </span>
          )}
          <button onClick={refresh} disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10
                       border border-white/10 rounded-lg text-sm transition-colors disabled:opacity-40">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Service health grid */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">Service Health</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {data && Object.entries(data.health).map(([key, dep]) => {
            const ok   = dep.status !== 'error';
            const link = SERVICE_LINKS[key];
            const card = (
              <div className={clsx(
                'bg-white/5 border rounded-xl p-4 space-y-1',
                ok ? 'border-green-500/20' : 'border-red-500/30',
              )}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold capitalize">{key}</span>
                  {link && <ExternalLink size={12} className="text-white/30" />}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={clsx('w-2 h-2 rounded-full', ok ? 'bg-green-400' : 'bg-red-400 animate-pulse')} />
                  <span className={clsx('text-xs font-medium', ok ? 'text-green-400' : 'text-red-400')}>
                    {ok ? 'OK' : 'ERROR'}
                  </span>
                </div>
                {dep.detail && (
                  <p className="text-xs text-white/30 truncate">{dep.detail}</p>
                )}
              </div>
            );
            return link ? (
              <a key={key} href={link} target="_blank" rel="noreferrer"
                className="hover:scale-[1.01] transition-transform block">
                {card}
              </a>
            ) : (
              <div key={key}>{card}</div>
            );
          })}
        </div>
      </section>

      {/* NATS JetStream streams */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-white/40">NATS JetStream Streams</h2>
          <span className="text-xs text-white/30">
            {data?.totalMsg.toLocaleString()} msgs · {fmt(data?.totalBytes ?? 0)} total
          </span>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                {['Stream','Subjects','Messages','Size','Consumers'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold uppercase tracking-wider
                                         text-white/30 px-4 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {!data || data.streams.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-white/20 text-sm">
                  {loading ? 'Fetching stream data…' : 'No streams found.'}
                </td></tr>
              ) : data.streams.map(s => (
                <tr key={s.name} className="hover:bg-white/5">
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-brand-200">{s.name}</td>
                  <td className="px-4 py-3">
                    <div className="space-y-0.5">
                      {s.subjects.map(sub => (
                        <span key={sub} className="block text-xs font-mono text-white/40">{sub}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm">
                    <span className={s.messages > 0 ? 'text-green-400' : 'text-white/20'}>
                      {s.messages.toLocaleString()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white/50 text-xs font-mono">{fmt(s.bytes)}</td>
                  <td className="px-4 py-3 text-white/40 text-sm">{s.consumers}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data?.serverId && (
          <p className="text-xs text-white/20 mt-2 font-mono">Server ID: {data.serverId}</p>
        )}
      </section>

      {/* Quick links */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">External UIs</h2>
        <div className="flex gap-3 flex-wrap">
          {[
            { label: 'InfluxDB UI',     href: 'http://localhost:8086',  note: 'Dashboards, Flux queries' },
            { label: 'VictoriaLogs UI', href: '/vlogs/select/vmui',    note: 'LogsQL search' },
            { label: 'NATS Monitor',    href: 'http://localhost:8222',  note: 'Server stats (internal)' },
            { label: 'API Docs',        href: '/docs',                  note: 'FastAPI Swagger UI' },
          ].map(l => (
            <a key={l.label} href={l.href} target="_blank" rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2.5 bg-white/5 hover:bg-white/10
                         border border-white/10 rounded-xl text-sm transition-colors group">
              <span className="font-medium group-hover:text-white">{l.label}</span>
              <ExternalLink size={12} className="text-white/30" />
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
