import React, { useState } from 'react';
import axios from 'axios';

export default function ProtobufModule() {
  const [count,   setCount]   = useState(5);
  const [ne,      setNe]      = useState('gnmi-router-01');
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<string | null>(null);

  const simulate = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.post('/api/v1/protobuf/simulate', { count, source_ne: ne });
      setResult(`✅ ${res.data.simulated ?? count} gNMI messages submitted`);
    } catch (e: unknown) {
      setResult(`❌ ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Protobuf / gNMI Plugin</h2>
        <span className="text-xs bg-green-900/40 text-green-400 px-2 py-0.5 rounded-full">✅ Healthy</span>
      </div>
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Simulate gNMI Telemetry</p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Source NE</label>
            <input value={ne} onChange={e => setNe(e.target.value)}
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
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50">
          {loading ? 'Running…' : '▶ Simulate'}
        </button>
        {result && <p className="text-sm font-mono">{result}</p>}
      </div>
    </div>
  );
}
