import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import axios from 'axios';
import { useWsEvents } from './useWsEvents';

const PROTOCOLS = ['snmp','ves','protobuf','avro','sftp','webhook'];
const COLORS    = ['#3b5bdb','#e03131','#f76707','#2f9e44','#f59f00','#74c0fc'];
const SLOTS = 20;
const BUCKET_MS = 30_000;

interface DataPoint { t: string; [proto: string]: number | string; }

function buildTimeline(events: {timestamp:string;protocol:string}[]): DataPoint[] {
  const now = Date.now();
  return Array.from({ length: SLOTS }, (_, i) => {
    const start = now - (SLOTS - 1 - i) * BUCKET_MS;
    const end   = start + BUCKET_MS;
    const pt: DataPoint = { t: new Date(start).toLocaleTimeString() };
    PROTOCOLS.forEach(p => {
      pt[p] = events.filter(e => {
        const et = new Date(e.timestamp).getTime();
        return e.protocol === p && et >= start && et < end;
      }).length;
    });
    return pt;
  });
}

export default function PmDashboardModule() {
  const allEvents = useWsEvents(undefined, 'PM');
  const [timeline, setTimeline] = useState<DataPoint[]>(() => buildTimeline([]));
  const [simProto, setSimProto] = useState('snmp');
  const [simCount, setSimCount] = useState(10);
  const [loading,  setLoading]  = useState(false);
  const rafRef = useRef<number>(0);

  // Rebuild timeline whenever new PM events arrive
  useEffect(() => {
    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => setTimeline(buildTimeline(allEvents)));
  }, [allEvents]);

  const simulate = async () => {
    setLoading(true);
    try { await axios.post(`/api/v1/${simProto}/simulate`, { count: simCount }); }
    finally { setLoading(false); }
  };

  const totals = PROTOCOLS.map(p => ({ name: p, count: allEvents.filter(e => e.protocol === p).length }));
  const maxTotal = Math.max(...totals.map(t => t.count), 1);

  return (
    <div className="space-y-4 text-white">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">PM Dashboard</h2>
        <span className="text-white/30 text-xs">{allEvents.length} PM events in buffer</span>
      </div>

      {/* Simulate panel */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs text-white/40 mb-1">Protocol</label>
          <select value={simProto} onChange={e => setSimProto(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
            {PROTOCOLS.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-white/40 mb-1">Count</label>
          <input type="number" min={1} max={200} value={simCount}
            onChange={e => setSimCount(Number(e.target.value))}
            className="w-20 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none" />
        </div>
        <button onClick={simulate} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50 transition-colors">
          {loading ? 'Running…' : '▶ Simulate PM'}
        </button>
      </div>

      {/* Per-protocol ingestion bars */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">Ingestion by Protocol</p>
        <div className="space-y-2">
          {totals.map((t, i) => (
            <div key={t.name} className="flex items-center gap-3">
              <span className="w-16 text-xs font-mono text-white/50">{t.name}</span>
              <div className="flex-1 bg-white/5 rounded-full h-1.5 overflow-hidden">
                <div className="h-full rounded-full transition-all"
                  style={{ width: `${(t.count/maxTotal)*100}%`, background: COLORS[i] }} />
              </div>
              <span className="text-xs text-white/40 w-6 text-right">{t.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline chart */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">
          PM Event Rate — 30s buckets (last 10 min)
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
            <XAxis dataKey="t" tick={{ fill:'#ffffff40', fontSize:10 }} />
            <YAxis tick={{ fill:'#ffffff40', fontSize:10 }} allowDecimals={false} />
            <Tooltip contentStyle={{ background:'#12121f', border:'1px solid #ffffff15', fontSize:11 }} />
            <Legend wrapperStyle={{ fontSize:11, color:'#ffffff60' }} />
            {PROTOCOLS.map((p, i) => (
              <Line key={p} type="monotone" dataKey={p} stroke={COLORS[i]}
                    strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
