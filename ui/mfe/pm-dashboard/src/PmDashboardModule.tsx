import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import axios from 'axios';

const PROTOCOLS = ['snmp', 'ves', 'protobuf', 'avro', 'sftp', 'webhook'];
const COLORS    = ['#3b5bdb','#e03131','#f76707','#2f9e44','#f59f00','#74c0fc'];

interface DataPoint { t: string; [proto: string]: number | string; }

export default function PmDashboardModule() {
  const [data, setData]         = useState<DataPoint[]>([]);
  const [loading, setLoading]   = useState(false);
  const [simProto, setSimProto] = useState('snmp');
  const [simCount, setSimCount] = useState(10);

  // Generate empty timeline buckets for demo
  useEffect(() => {
    const now = Date.now();
    const pts: DataPoint[] = Array.from({ length: 20 }, (_, i) => {
      const pt: DataPoint = { t: new Date(now - (19 - i) * 30_000).toLocaleTimeString() };
      PROTOCOLS.forEach(p => { pt[p] = 0; });
      return pt;
    });
    setData(pts);
  }, []);

  const simulate = async () => {
    setLoading(true);
    try {
      await axios.post(`/api/v1/${simProto}/simulate`, { count: simCount });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">PM Dashboard</h2>
      </div>

      {/* Simulate panel */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 flex items-end gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Protocol</label>
          <select
            value={simProto}
            onChange={e => setSimProto(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white"
          >
            {PROTOCOLS.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Count</label>
          <input type="number" min={1} max={200} value={simCount}
            onChange={e => setSimCount(Number(e.target.value))}
            className="w-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white"
          />
        </div>
        <button onClick={simulate} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50">
          {loading ? 'Running…' : '▶ Simulate'}
        </button>
      </div>

      {/* Chart */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">PM Ingestion Rate (per protocol)</p>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
            <XAxis dataKey="t" tick={{ fill: '#ffffff40', fontSize: 10 }} />
            <YAxis tick={{ fill: '#ffffff40', fontSize: 10 }} />
            <Tooltip contentStyle={{ background: '#12121f', border: '1px solid #ffffff15', fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#ffffff60' }} />
            {PROTOCOLS.map((p, i) => (
              <Line key={p} type="monotone" dataKey={p} stroke={COLORS[i]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
