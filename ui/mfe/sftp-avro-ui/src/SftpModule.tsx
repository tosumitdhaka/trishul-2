import { useState } from 'react';
import axios from 'axios';
import { useWsEvents } from './useWsEvents';

const FILE_TYPES = ['pm_counters.csv','alarm_log.txt','interface_stats.json','config_backup.xml'];

export default function SftpModule() {
  const [fileType, setFileType] = useState(FILE_TYPES[0]);
  const [count,    setCount]    = useState(3);
  const [ne,       setNe]       = useState('sftp-ne-01');
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState<string | null>(null);
  const events = useWsEvents('sftp');

  const simulate = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.post('/api/v1/sftp/simulate', { count, file_pattern: fileType, source_ne: ne });
      setResult(`✅ ${res.data.simulated ?? count} SFTP files processed`);
    } catch (e: unknown) { setResult(`❌ ${(e as Error).message}`); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4 text-white">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">SFTP Plugin</h2>
        <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-400" /><span className="text-xs text-green-400">Healthy</span></div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
        <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">Simulate SFTP File Ingest</p>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-white/40 mb-1">File Type</label>
            <select value={fileType} onChange={e => setFileType(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
              {FILE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Source NE</label>
            <input value={ne} onChange={e => setNe(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Count</label>
            <input type="number" min={1} max={50} value={count} onChange={e => setCount(Number(e.target.value))}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none" />
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

      <div className="grid grid-cols-3 gap-4">
        {[['Protocol','SFTP / File'],['FCAPS Domains','PM, LOG'],['Transport','SSH file transfer']]
          .map(([k,v])=>(
          <div key={k} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">{k}</p>
            <p className="text-sm font-mono text-white/70">{v}</p>
          </div>
        ))}
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">Live SFTP Feed</p>
          <span className="text-xs text-white/30">{events.length} events</span>
        </div>
        <div className="max-h-64 overflow-y-auto divide-y divide-white/5">
          {events.length === 0
            ? <p className="p-4 text-sm text-white/20 text-center">Waiting for SFTP events…</p>
            : events.map(ev => (
              <div key={ev.id} className="flex items-center gap-3 px-4 py-2 text-xs font-mono hover:bg-white/5">
                <span className="text-white/30 w-20 flex-shrink-0">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                <span className="text-white/60 w-24 truncate flex-shrink-0">{ev.source_ne}</span>
                <span className="text-white/50 flex-1 truncate">{ev.message || ev.envelope_id}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
