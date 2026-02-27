import { useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import { useWsEvents } from './useWsEvents';

const TRAP_TYPES = ['linkDown','linkUp','authenticationFailure','coldStart','warmStart'];

const SEV_CLASS: Record<string, string> = {
  CRITICAL: 'bg-red-900/40 text-red-400 border border-red-800/40',
  MAJOR:    'bg-orange-900/40 text-orange-400 border border-orange-800/40',
  MINOR:    'bg-yellow-900/40 text-yellow-400 border border-yellow-800/40',
  WARNING:  'bg-blue-900/40 text-blue-400 border border-blue-800/40',
  CLEARED:  'bg-green-900/40 text-green-400 border border-green-800/40',
};

const SEV_ICON: Record<string, string> = {
  CRITICAL:'🔴', MAJOR:'🟠', MINOR:'🟡', WARNING:'🔵', CLEARED:'🟢',
};

export default function SnmpModule() {
  const [trapType, setTrapType] = useState(TRAP_TYPES[0]);
  const [count,    setCount]    = useState(5);
  const [neTarget, setNeTarget] = useState('router-01');
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<string | null>(null);

  const events = useWsEvents('snmp');

  const simulate = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.post('/api/v1/snmp/simulate', {
        count, trap_type: trapType, source_ne: neTarget,
      });
      setResult(`✅ ${res.data.simulated ?? count} traps submitted (${res.data.job_id ?? 'sync'})`);
    } catch (e: unknown) {
      setResult(`❌ ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">SNMP Plugin</h2>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400" />
          <span className="text-xs text-green-400 font-medium">Healthy</span>
        </div>
      </div>

      {/* Simulate */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
        <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">Simulate Traps</p>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-white/40 mb-1">Trap Type</label>
            <select value={trapType} onChange={e => setTrapType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500">
              {TRAP_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Source NE</label>
            <input value={neTarget} onChange={e => setNeTarget(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Count</label>
            <input type="number" min={1} max={100} value={count}
              onChange={e => setCount(Number(e.target.value))}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500" />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={simulate} disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50 transition-colors">
            {loading ? 'Running…' : '▶ Run Simulation'}
          </button>
          {result && <p className="text-sm font-mono text-white/70">{result}</p>}
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          ['Protocol',      'SNMP v2c'],
          ['FCAPS Domains', 'FM, PM'],
          ['NATS Subjects', 'fcaps.ingest.snmp\nfcaps.simulated.snmp'],
        ].map(([k, v]) => (
          <div key={k} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">{k}</p>
            <p className="text-sm font-mono text-white/70 whitespace-pre">{v}</p>
          </div>
        ))}
      </div>

      {/* Live trap feed */}
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">Live Trap Feed</p>
          <span className="text-xs text-white/30">{events.length} events</span>
        </div>
        <div className="max-h-64 overflow-y-auto divide-y divide-white/5">
          {events.length === 0 ? (
            <p className="p-4 text-sm text-white/20 text-center">Waiting for SNMP traps…</p>
          ) : events.map(ev => (
            <div key={ev.id} className="flex items-center gap-3 px-4 py-2 text-xs font-mono hover:bg-white/5">
              <span className="text-white/30 w-20 flex-shrink-0">
                {new Date(ev.timestamp).toLocaleTimeString()}
              </span>
              <span className="text-white/60 w-24 truncate flex-shrink-0">{ev.source_ne}</span>
              {ev.severity ? (
                <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${SEV_CLASS[ev.severity] ?? ''}`}>
                  {SEV_ICON[ev.severity]} {ev.severity}
                </span>
              ) : <span className="w-20 flex-shrink-0" />}
              <span className="text-white/50 flex-1 truncate">{ev.message || ev.envelope_id}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
