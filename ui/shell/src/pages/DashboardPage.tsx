import { useEventsStore } from '@/store/events';
import { usePluginsStore } from '@/store/plugins';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { Pause, Play } from 'lucide-react';
import clsx from 'clsx';
import { formatDistanceToNow } from 'date-fns';

const SEV_COLOR: Record<string, string> = {
  CRITICAL: '#e03131',
  MAJOR:    '#f76707',
  MINOR:    '#f59f00',
  CLEARED:  '#2f9e44',
};

const SEV_ICON: Record<string, string> = {
  CRITICAL: '🔴',
  MAJOR:    '🟠',
  MINOR:    '🟡',
  WARNING:  '🔵',
  CLEARED:  '🟢',
  NORMAL:   '🟢',
};

function StatCard({ label, value, sub, color = 'text-white' }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="card flex flex-col gap-1">
      <p className="text-xs text-surface-200/50 font-medium uppercase tracking-wider">{label}</p>
      <p className={clsx('text-3xl font-bold', color)}>{value}</p>
      {sub && <p className="text-xs text-surface-200/40">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const events  = useEventsStore(s => s.events);
  const paused  = useEventsStore(s => s.paused);
  const setPaused = useEventsStore(s => s.setPaused);
  const plugins = usePluginsStore(s => s.plugins);

  const fmEvents  = events.filter(e => e.domain === 'FM');
  const criticals = fmEvents.filter(e => e.severity === 'CRITICAL').length;
  const total     = events.length;

  // Severity distribution for bar chart
  const sevData = ['CRITICAL', 'MAJOR', 'MINOR', 'CLEARED'].map(sev => ({
    name: sev,
    count: fmEvents.filter(e => e.severity === sev).length,
  }));

  // Per-protocol counts
  const protoData = plugins.map(p => ({
    name: p.name,
    count: events.filter(e => e.protocol === p.name).length,
  })).filter(d => d.count > 0);

  // Timeline: bucket events into last 20 slots of 30s each
  const now    = Date.now();
  const SLOTS  = 20;
  const WINDOW = 30_000;
  const timeline = Array.from({ length: SLOTS }, (_, i) => {
    const t = now - (SLOTS - 1 - i) * WINDOW;
    return {
      t: i,
      count: fmEvents.filter(e => {
        const et = new Date(e.timestamp).getTime();
        return et >= t && et < t + WINDOW;
      }).length,
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Dashboard</h1>
        <span className="text-xs text-surface-200/40">Live via WebSocket</span>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Active Alarms"  value={criticals} color="text-severity-critical" sub="CRITICAL severity" />
        <StatCard label="Total Events"   value={total}     sub="in buffer (last 200)" />
        <StatCard label="FM Events"      value={fmEvents.length} sub="fault management" />
        <StatCard label="Plugins Loaded" value={plugins.length}  sub="protocol plugins" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* FM Timeline */}
        <div className="card lg:col-span-2">
          <p className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider mb-3">
            FM Alarm Timeline
          </p>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="fmGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#e03131" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#e03131" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <XAxis dataKey="t" hide />
              <YAxis hide />
              <Tooltip
                contentStyle={{ background: '#12121f', border: '1px solid #ffffff15', fontSize: 11 }}
                labelFormatter={() => ''}
              />
              <Area type="monotone" dataKey="count" stroke="#e03131"
                    fill="url(#fmGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity distribution */}
        <div className="card">
          <p className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider mb-3">
            Severity Distribution
          </p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={sevData} layout="vertical">
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" width={60}
                     tick={{ fill: '#ffffff60', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#12121f', border: '1px solid #ffffff15', fontSize: 11 }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {sevData.map(entry => (
                  <Cell key={entry.name} fill={SEV_COLOR[entry.name] ?? '#6c757d'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Per-protocol ingestion */}
      {protoData.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider mb-3">
            Events by Protocol
          </p>
          <div className="space-y-2">
            {protoData.map(p => (
              <div key={p.name} className="flex items-center gap-3">
                <span className="w-16 text-xs text-surface-200/60 font-mono">{p.name}</span>
                <div className="flex-1 bg-surface-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-brand-500 h-full rounded-full transition-all"
                    style={{ width: `${Math.min((p.count / Math.max(...protoData.map(x => x.count))) * 100, 100)}%` }}
                  />
                </div>
                <span className="text-xs text-surface-200/50 w-8 text-right">{p.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live event feed */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider">
            Live Event Feed
          </p>
          <button
            onClick={() => setPaused(!paused)}
            className="flex items-center gap-1.5 text-xs text-surface-200/50 hover:text-white transition-colors"
          >
            {paused ? <Play size={12} /> : <Pause size={12} />}
            {paused ? 'Resume' : 'Pause'}
          </button>
        </div>
        <div className="space-y-0 divide-y divide-surface-200/10 max-h-64 overflow-y-auto">
          {events.length === 0 && (
            <p className="text-sm text-surface-200/30 py-4 text-center">Waiting for events…</p>
          )}
          {events.slice(0, 50).map(ev => (
            <div key={ev.id} className="flex items-center gap-3 py-2 text-xs font-mono">
              <span className="text-surface-200/40 w-20 flex-shrink-0">
                {new Date(ev.timestamp).toLocaleTimeString()}
              </span>
              <span className="badge-info w-10 text-center flex-shrink-0">{ev.domain}</span>
              <span className="text-surface-200/60 w-16 flex-shrink-0 truncate">{ev.protocol}</span>
              <span className="text-white flex-1 truncate">{ev.source_ne}</span>
              {ev.severity && (
                <span className="flex-shrink-0">{SEV_ICON[ev.severity] ?? ''} {ev.severity}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
