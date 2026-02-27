import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  source_ne: string;
  protocol: string;
  message: string;
}

const LEVEL_CLASS: Record<string, string> = {
  INFO:  'text-blue-400',
  WARN:  'text-yellow-400',
  ERROR: 'text-red-400',
  DEBUG: 'text-gray-500',
};

export default function LogViewerModule() {
  const [logs]     = useState<LogEntry[]>([]);
  const [query, setQuery] = useState('');
  const [level, setLevel] = useState<string>('ALL');

  const filtered = logs.filter(l => {
    const matchLevel = level === 'ALL' || l.level === level;
    const matchQuery = !query || l.message.toLowerCase().includes(query.toLowerCase())
                                || l.source_ne.toLowerCase().includes(query.toLowerCase());
    return matchLevel && matchQuery;
  });

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold">Log Viewer</h2>

      {/* Search + filter */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text" value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search logs…"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5
                       text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select value={level} onChange={e => setLevel(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white">
          {['ALL','INFO','WARN','ERROR','DEBUG'].map(l => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>

      {/* Log table */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
        <div className="font-mono text-xs divide-y divide-gray-800 max-h-[500px] overflow-y-auto">
          {filtered.length === 0 && (
            <div className="px-4 py-8 text-center text-gray-600">No log entries. Events appear here via WebSocket.</div>
          )}
          {filtered.map(l => (
            <div key={l.id} className="flex items-start gap-3 px-4 py-2 hover:bg-gray-800/40">
              <span className="text-gray-500 flex-shrink-0 w-20">
                {new Date(l.timestamp).toLocaleTimeString()}
              </span>
              <span className={`flex-shrink-0 w-12 font-semibold ${LEVEL_CLASS[l.level]}`}>{l.level}</span>
              <span className="text-gray-500 flex-shrink-0 w-16 truncate">{l.protocol}</span>
              <span className="text-gray-400 flex-shrink-0 w-24 truncate">{l.source_ne}</span>
              <span className="text-gray-300 flex-1">{l.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
