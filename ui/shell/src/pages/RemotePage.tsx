import { useParams } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import { Suspense, useEffect, useState } from 'react';

/**
 * RemotePage — dynamically loads a Module Federation remote for a protocol plugin.
 *
 * Phase 4: shows a placeholder card for each plugin (no remote MFEs exist yet).
 * Phase 5: when plugin.remote_url is a real URL, uses loadRemoteModule() to mount the MFE.
 */
async function loadRemoteModule(
  remoteName: string,
  remoteUrl:  string,
  exposedModule: string,
): Promise<{ default: React.ComponentType }> {
  await new Promise<void>((resolve, reject) => {
    if (document.getElementById(`remote-${remoteName}`)) { resolve(); return; }
    const script    = document.createElement('script');
    script.id       = `remote-${remoteName}`;
    script.src      = remoteUrl;
    script.type     = 'text/javascript';
    script.onload   = () => resolve();
    script.onerror  = reject;
    document.head.appendChild(script);
  });

  // Vite Module Federation exposes the container on window under the federation name.
  // The federation name in each MFE's vite.config matches the camelCase form below.
  const federationName = remoteName
    .replace(/-([a-z])/g, (_, c: string) => c.toUpperCase()); // kebab → camelCase

  // @ts-expect-error — dynamic MFE container
  const container = window[federationName] as {
    init: (shareScope: object) => Promise<void>;
    get:  (mod: string) => Promise<() => { default: React.ComponentType }>;
  };

  if (!container) throw new Error(`MFE container "${federationName}" not found on window`);

  // @ts-expect-error — __webpack_share_scopes__ not in types
  await container.init(__webpack_share_scopes__.default);
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
    if (!plugin?.remote_url?.startsWith('http') && !plugin?.remote_url?.startsWith('/mfe')) return;
    if (!plugin.exposed) return;
    loadRemoteModule(plugin.name, plugin.remote_url, plugin.exposed)
      .then(mod => setRemoteComp(() => mod.default))
      .catch(e  => setError(String(e)));
  }, [plugin]);

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
      <div className="card border border-severity-critical/30 space-y-2">
        <p className="text-severity-critical text-sm font-semibold">Failed to load MFE remote</p>
        <p className="text-surface-200/50 text-xs font-mono">{error}</p>
        <p className="text-surface-200/40 text-xs">Is the <code className="font-mono">{plugin.name}-ui</code> container running?</p>
      </div>
    );
  }

  // Phase 4 placeholder
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
            {plugin.domains.map(d => <span key={d} className="badge-info">{d}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Protocols</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.protocols?.map(p => <span key={p} className="badge-info font-mono">{p}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Status</p>
          <p className="text-severity-cleared font-medium mt-2 text-sm">✅ Healthy</p>
        </div>
      </div>
      <div className="card">
        <div className="flex items-center gap-3 py-2">
          <div className="w-2 h-2 rounded-full bg-severity-warning animate-pulse" />
          <p className="text-xs text-surface-200/40">
            MFE container loading… ensure <code className="font-mono">{plugin.name}-ui</code> is running.
          </p>
        </div>
      </div>
    </div>
  );
}
