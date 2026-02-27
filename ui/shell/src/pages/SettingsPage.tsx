export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Settings</h1>
      <div className="card">
        <p className="text-sm text-surface-200/50">Platform configuration coming in Phase 6 (Observability).</p>
        <div className="mt-4 space-y-3 text-sm">
          {[
            ['API Base URL', '/api/v1'],
            ['WebSocket', '/ws/events'],
            ['NATS Subject Prefix', 'fcaps.*'],
            ['Event Buffer Size', '200'],
          ].map(([k, v]) => (
            <div key={k} className="flex items-center justify-between py-2 border-b border-surface-200/10 last:border-0">
              <span className="text-surface-200/60">{k}</span>
              <span className="font-mono text-xs bg-surface-800 px-2 py-1 rounded">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
