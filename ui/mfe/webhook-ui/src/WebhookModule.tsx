import React, { useState } from 'react';
import axios from 'axios';

const DEFAULT_PAYLOAD = JSON.stringify({
  source_ne: 'router-01',
  event_type: 'linkDown',
  severity: 'CRITICAL',
  message: 'Interface GigabitEthernet0/0 is down',
}, null, 2);

export default function WebhookModule() {
  const [payload,  setPayload]  = useState(DEFAULT_PAYLOAD);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<string | null>(null);
  const [parseErr, setParseErr] = useState<string | null>(null);

  const send = async () => {
    setResult(null);
    try { JSON.parse(payload); setParseErr(null); } catch { setParseErr('Invalid JSON'); return; }
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/webhook/receive', JSON.parse(payload));
      setResult(`✅ 202 Accepted — envelope: ${res.data.envelope_id ?? 'ok'}`);
    } catch (e: unknown) {
      setResult(`❌ ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Webhook Plugin</h2>
        <span className="text-xs bg-green-900/40 text-green-400 px-2 py-0.5 rounded-full">✅ Healthy</span>
      </div>
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Send Payload</p>
        <div>
          <label className="block text-xs text-gray-400 mb-1">JSON Body</label>
          <textarea
            value={payload}
            onChange={e => setPayload(e.target.value)}
            rows={8}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                       text-sm font-mono text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          {parseErr && <p className="text-xs text-red-400 mt-1">{parseErr}</p>}
        </div>
        <button onClick={send} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2
                     rounded-lg text-sm disabled:opacity-50 transition-colors">
          {loading ? 'Sending…' : '▶ Send'}
        </button>
        {result && <p className="text-sm font-mono">{result}</p>}
      </div>
    </div>
  );
}
