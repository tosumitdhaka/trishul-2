import React, { useState } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

type Severity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'WARNING' | 'CLEARED' | 'NORMAL';

const SEV_BADGE: Record<string, string> = {
  CRITICAL: 'bg-red-900/40 text-red-400',
  MAJOR:    'bg-orange-900/40 text-orange-400',
  MINOR:    'bg-yellow-900/40 text-yellow-400',
  WARNING:  'bg-blue-900/40 text-blue-400',
  CLEARED:  'bg-green-900/40 text-green-400',
};

const SEV_ICON: Record<string, string> = {
  CRITICAL: '🔴', MAJOR: '🟠', MINOR: '🟡', WARNING: '🔵', CLEARED: '🟢',
};

const ALL_SEVERITIES: Severity[] = ['CRITICAL', 'MAJOR', 'MINOR', 'WARNING', 'CLEARED'];

interface Alarm {
  id: string;
  timestamp: string;
  source_ne: string;
  protocol: string;
  severity: Severity;
  message: string;
  domain: string;
}

export default function FmConsoleModule() {
  const [alarms]    = useState<Alarm[]>([]);
  const [filter, setFilter] = useState<Severity | 'ALL'>('ALL');
  const [simLoading, setSimLoading] = useState(false);
  const [simCount, setSimCount]     = useState(5);
  const [simProto, setSimProto]     = useState('snmp');

  const filtered = filter === 'ALL' ? alarms : alarms.filter(a => a.severity === filter);

  const simulate = async () => {
    setSimLoading(true);
    try {
      await axios.post(`/api/v1/${simProto}/simulate`, { count: simCount });
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">FM Console</h2>
        <span className="text-xs text-gray-500">{alarms.length} alarms in buffer</span>
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
            {['snmp','ves','webhook','protobuf','avro','sftp'].map(p =>
              <option key={p} value={p}>{p.toUpperCase()}</option>
            )}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Count</label>
          <input
            type="number" min={1} max={100}
            value={simCount}
            onChange={e => setSimCount(Number(e.target.value))}
            className="w-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white"
          />
        </div>
        <button
          onClick={simulate}
          disabled={simLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50"
        >
          {simLoading ? 'Running…' : '▶ Simulate'}
        </button>
      </div>

      {/* Severity filter */}
      <div className="flex items-center gap-2">
        {(['ALL', ...ALL_SEVERITIES] as const).map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${
              filter === s
                ? 'bg-blue-500/20 text-blue-300'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {s === 'ALL' ? 'All' : `${SEV_ICON[s]} ${s}`}
          </button>
        ))}
      </div>

      {/* Alarm table */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              {['Time', 'Source NE', 'Protocol', 'Severity', 'Message'].map(h => (
                <th key={h} className="text-left text-xs font-semibold uppercase tracking-wider text-gray-500 px-4 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {filtered.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-600">
                No alarms. Run a simulation or wait for live events via WebSocket.
              </td></tr>
            )}
            {filtered.map(a => (
              <tr key={a.id} className="hover:bg-gray-800/50">
                <td className="px-4 py-2 text-xs text-gray-500 font-mono">
                  {formatDistanceToNow(new Date(a.timestamp), { addSuffix: true })}
                </td>
                <td className="px-4 py-2 font-medium">{a.source_ne}</td>
                <td className="px-4 py-2 text-gray-400 font-mono text-xs">{a.protocol}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SEV_BADGE[a.severity] ?? ''}`}>
                    {SEV_ICON[a.severity]} {a.severity}
                  </span>
                </td>
                <td className="px-4 py-2 text-gray-300 truncate max-w-xs">{a.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
