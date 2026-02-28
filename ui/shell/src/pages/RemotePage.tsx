import { useParams } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import { Suspense, useEffect, useState } from 'react';

/**
 * Loads a Vite Module Federation remote.
 *
 * Fresh build (esnext target) confirmed to use window[federationName] registration.
 * remoteEntry.js also contains import.meta so must be loaded as type="module".
 * ESM module evaluation is async, so we poll window[name] up to 3s instead
 * of relying on a fixed timeout.
 */
async function loadRemoteModule(
  federationName: string,
  remoteUrl: string,
  exposedModule: string,
): Promise<{ default: React.ComponentType }> {
  // Inject as ES module (required for import.meta in esnext output)
  await new Promise<void>((resolve, reject) => {
    if (document.getElementById(`remote-${federationName}`)) { resolve(); return; }
    const s  = document.createElement('script');
    s.id     = `remote-${federationName}`;
    s.src    = remoteUrl;
    s.type   = 'module';
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Failed to fetch ${remoteUrl}`));
    document.head.appendChild(s);
  });

  // Poll for window[federationName] — ESM evaluation is async after onload
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const container = await (async () => {
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const c = (window as any)[federationName];
      if (c) return c;
      await new Promise(r => setTimeout(r, 50));
    }
    return null;
  })();

  if (!container) {
    throw new Error(
      `window.${federationName} not found after 3s.\n` +
      `remoteEntry.js loaded from ${remoteUrl} but the federation container did not register.\n` +
      `Check federation({ name: '${federationName}' }) in the MFE's vite.config.ts.`,
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const shareScope = (window as any).__federation_shared_scope__ ?? {};
  try { await container.init(shareScope); } catch { /* already initialised */ }

  const factory = await container.get(exposedModule);
  return factory();
}

export default function RemotePage() {
  const { pluginName } = useParams<{ pluginName: string }>();
  const plugins = usePluginsStore(s => s.plugins);
  const plugin  = plugins.find(p => p.name === pluginName);

  const [RemoteComp, setRemoteComp] = useState<React.ComponentType | null>(null);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    if (!plugin?.remote_url || !plugin?.exposed || !plugin?.federation_name) return;
    setError(null);
    setRemoteComp(null);
    loadRemoteModule(plugin.federation_name, plugin.remote_url, plugin.exposed)
      .then(mod => setRemoteComp(() => mod.default ?? (mod as any)))
      .catch(e  => setError(String(e)));
  }, [plugin?.federation_name, plugin?.remote_url, plugin?.exposed]);

  if (!plugin) {
    return (
      <div className="card text-center py-12">
        <p className="text-surface-200/40 text-sm">
          Plugin <code className="font-mono">{pluginName}</code> not found in registry.
        </p>
      </div>
    );
  }

  if (RemoteComp) {
    return (
      <Suspense fallback={<div className="card animate-pulse h-64" />}>
        <RemoteComp />
      </Suspense>
    );
  }

  if (error) {
    return (
      <div className="card border border-severity-critical/30 space-y-3 p-4">
        <p className="text-severity-critical text-sm font-semibold">⚠ Failed to load MFE remote</p>
        <pre className="text-surface-200/50 text-xs font-mono whitespace-pre-wrap break-all bg-black/30 rounded p-3">{error}</pre>
        <div className="text-surface-200/30 text-xs space-y-1">
          <p>Container: <code className="font-mono text-white/50">{plugin.federation_name}</code></p>
          <p>URL: <code className="font-mono text-white/50">{plugin.remote_url}</code></p>
          <p>Exposed: <code className="font-mono text-white/50">{plugin.exposed}</code></p>
        </div>
        <button
          onClick={() => {
            document.getElementById(`remote-${plugin.federation_name}`)?.remove();
            setError(null);
          }}
          className="text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded px-3 py-1.5 transition-colors"
        >
          ↺ Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold capitalize">{plugin.name} Plugin</h1>
        <span className="badge-cleared">v{plugin.version}</span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">FCAPS Domains</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.domains?.map(d => <span key={d} className="badge-info">{d}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Protocols</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.protocols?.map(p => <span key={p} className="badge-info font-mono">{p}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Remote</p>
          <p className="text-white/40 font-mono text-xs mt-2 break-all">{plugin.remote_url}</p>
        </div>
      </div>
      <div className="card">
        <div className="flex items-center gap-3 py-1">
          <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <p className="text-xs text-surface-200/40">
            Loading <code className="font-mono text-white/50">{plugin.federation_name}</code>…
          </p>
        </div>
      </div>
    </div>
  );
}
