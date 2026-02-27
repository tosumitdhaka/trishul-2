import React, { useState } from 'react';
import axios from 'axios';

const EVENT_TYPES = ['fault', 'measurement', 'heartbeat', 'syslog', 'thresholdCrossingAlert'];

export default function VesModule() {
  const [eventType, setEventType] = useState(EVENT_TYPES[0]);
  const [count,     setCount]     = useState(5);
  const [neTarget,  setNeTarget]  = useState('ems-01');
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<string | null>(null);

  const simulate = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.post('/api/v1/ves/simulate', {
        count, event_type: eventType, source_ne: neTarget,
      });
      setResult(`✅ ${res.data.simulated ?? count} VES events submitted`);
    } catch (e: unknown) {
      setResult(`❌ ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">VES Plugin</h2>
        <span className="text-xs bg-green-900/40 text-green-400 px-2 py-0.5 rounded-full">✅ Healthy</span>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Simulate VES Events</p>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Event Type</label>
            <select value={eventType} onChange={e => setEventType(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white">
              {EVENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Source NE</label>
            <input value={neTarget} onChange={e => setNeTarget(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Count</label>
            <input type="number" min={1} max={100} value={count}
              onChange={e => setCount(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white" />
          </div>
        </div>
        <button onClick={simulate} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2
                     rounded-lg text-sm disabled:opacity-50 transition-colors">
          {loading ? 'Running…' : '▶ Run Simulation'}
        </button>
        {result && <p className="text-sm font-mono">{result}</p>}
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[['Protocol','VES 7.x'],['FCAPS Domains','FM, PM, LOG'],['NATS Subjects','fcaps.ingest.ves\nfcaps.simulated.ves']].map(([k,v]) => (
          <div key={k} className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{k}</p>
            <p className="text-sm font-mono text-gray-300 whitespace-pre">{v}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
