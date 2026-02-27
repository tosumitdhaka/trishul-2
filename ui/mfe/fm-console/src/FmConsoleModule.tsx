import { useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import { useWsEvents } from './useWsEvents';

type Sev = 'CRITICAL'|'MAJOR'|'MINOR'|'WARNING'|'CLEARED';

const SEV_CLASS: Record<string,string> = {
  CRITICAL: 'bg-red-900/40 text-red-400',
  MAJOR:    'bg-orange-900/40 text-orange-400',
  MINOR:    'bg-yellow-900/40 text-yellow-400',
  WARNING:  'bg-blue-900/40 text-blue-400',
  CLEARED:  'bg-green-900/40 text-green-400',
};
const SEV_ICON: Record<string,string> = { CRITICAL:'🔴',MAJOR:'🟠',MINOR:'🟡',WARNING:'🔵',CLEARED:'🟢' };
const ALL_SEV: Sev[] = ['CRITICAL','MAJOR','MINOR','WARNING','CLEARED'];

export default function FmConsoleModule() {
  const allEvents = useWsEvents(undefined, 'FM');
  const [filter, setFilter]     = useState<Sev|'ALL'>('ALL');
  const [simProto, setSimProto] = useState('snmp');
  const [simCount, setSimCount] = useState(5);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<string|null>(null);

  const filtered = filter === 'ALL' ? allEvents : allEvents.filter(a => a.severity === filter);

  const simulate = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.post(`/api/v1/${simProto}/simulate`, { count: simCount });
      setResult(`✅ ${res.data.simulated ?? simCount} events via ${simProto.toUpperCase()}`);
    } catch (e: unknown) { setResult(`❌ ${(e as Error).message}`); }
    finally { setLoading(false); }
  };

  const critical = allEvents.filter(e => e.severity === 'CRITICAL').length;
  const major    = allEvents.filter(e => e.severity === 'MAJOR').length;

  return (
    <div className="space-y-4 text-white">
      {/* Header + stat chips */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">FM Alarm Console</h2>
        <div className="flex items-center gap-2">
          {critical > 0 && <span className="bg-red-900/40 text-red-400 text-xs px-2 py-0.5 rounded-full">{critical} CRITICAL</span>}
          {major    > 0 && <span className="bg-orange-900/40 text-orange-400 text-xs px-2 py-0.5 rounded-full">{major} MAJOR</span>}
          <span className="text-white/30 text-xs">{allEvents.length} total</span>
        </div>
      </div>

      {/* Simulate panel */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs text-white/40 mb-1">Protocol</label>
          <select value={simProto} onChange={e => setSimProto(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
            {['snmp','ves','webhook','protobuf','avro','sftp'].map(p =>
              <option key={p} value={p}>{p.toUpperCase()}</option>
            )}
          </select>
        </div>
        <div>
          <label className="block text-xs text-white/40 mb-1">Count</label>
          <input type="number" min={1} max={100} value={simCount}
            onChange={e => setSimCount(Number(e.target.value))}
            className="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none" />
        </div>
        <button onClick={simulate} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50 transition-colors">
          {loading ? 'Running…' : '▶ Simulate FM Events'}
        </button>
        {result && <p className="text-sm font-mono text-white/60">{result}</p>}
      </div>

      {/* Severity filter pills */}
      <div className="flex items-center gap-2 flex-wrap">
        {(['ALL',...ALL_SEV] as const).map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${
              filter === s
                ? 'bg-blue-600/40 text-blue-300 border border-blue-500/40'
                : 'bg-white/5 text-white/40 hover:text-white border border-white/10'
            }`}>
            {s === 'ALL' ? `All (${allEvents.length})` : `${SEV_ICON[s]} ${s} (${allEvents.filter(e=>e.severity===s).length})`}
          </button>
        ))}
      </div>

      {/* Alarm table */}
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              {['Time','Source NE','Protocol','Severity','Message'].map(h => (
                <th key={h} className="text-left text-xs font-semibold uppercase tracking-wider text-white/30 px-4 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-sm text-white/20">
                No FM alarms. Run a simulation or wait for live events.
              </td></tr>
            ) : filtered.map(a => (
              <tr key={a.id} className="hover:bg-white/5">
                <td className="px-4 py-2 text-xs text-white/40 font-mono">
                  {formatDistanceToNow(new Date(a.timestamp), { addSuffix: true })}
                </td>
                <td className="px-4 py-2 font-medium text-white/80">{a.source_ne}</td>
                <td className="px-4 py-2 text-white/40 font-mono text-xs">{a.protocol}</td>
                <td className="px-4 py-2">
                  {a.severity ? (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SEV_CLASS[a.severity]??''}`}>
                      {SEV_ICON[a.severity]} {a.severity}
                    </span>
                  ) : <span className="text-white/20 text-xs">—</span>}
                </td>
                <td className="px-4 py-2 text-white/50 truncate max-w-xs">{a.message || a.envelope_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
