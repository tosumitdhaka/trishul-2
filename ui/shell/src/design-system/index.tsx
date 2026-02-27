/**
 * Trishul shared design tokens — inlined here for Docker build context isolation.
 * Source of truth lives in ui/shared/design-system/ for local dev.
 * Shell exposes this as "./design-system" via vite-plugin-federation.
 */
import React from 'react';
import clsx from 'clsx';

// ---- Tokens ----
export const colors = {
  brand:    { 500: '#3b5bdb', 600: '#2f4ac7', 700: '#2540b0' },
  severity: {
    critical: '#e03131',
    major:    '#f76707',
    minor:    '#f59f00',
    warning:  '#74c0fc',
    cleared:  '#2f9e44',
    info:     '#6c757d',
  },
  surface: {
    800: '#1c1c2e',
    900: '#12121f',
    950: '#0a0a14',
  },
} as const;

export type Severity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'WARNING' | 'CLEARED' | 'NORMAL';

export const SEV_COLOR: Record<Severity, string> = {
  CRITICAL: colors.severity.critical,
  MAJOR:    colors.severity.major,
  MINOR:    colors.severity.minor,
  WARNING:  colors.severity.warning,
  CLEARED:  colors.severity.cleared,
  NORMAL:   colors.severity.cleared,
};

export const SEV_ICON: Record<Severity, string> = {
  CRITICAL: '🔴',
  MAJOR:    '🟠',
  MINOR:    '🟡',
  WARNING:  '🔵',
  CLEARED:  '🟢',
  NORMAL:   '🟢',
};

export const SEV_BADGE_CLASS: Record<Severity, string> = {
  CRITICAL: 'badge-critical',
  MAJOR:    'badge-major',
  MINOR:    'badge-minor',
  WARNING:  'badge-info',
  CLEARED:  'badge-cleared',
  NORMAL:   'badge-cleared',
};

// ---- Components ----

export function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) return null;
  return (
    <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full', SEV_BADGE_CLASS[severity] ?? 'badge-info')}>
      {SEV_ICON[severity]} {severity}
    </span>
  );
}

export function StatCard({
  label, value, sub, colorClass = 'text-white',
}: {
  label: string; value: string | number; sub?: string; colorClass?: string;
}) {
  return (
    <div className="card flex flex-col gap-1">
      <p className="text-xs text-surface-200/50 font-medium uppercase tracking-wider">{label}</p>
      <p className={clsx('text-3xl font-bold', colorClass)}>{value}</p>
      {sub && <p className="text-xs text-surface-200/40">{sub}</p>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse bg-surface-200/10 rounded', className)} />;
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <p className="text-sm text-surface-200/30">{message}</p>
    </div>
  );
}

export function SimulateButton({
  onClick, loading = false,
}: {
  onClick: () => void; loading?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50"
    >
      {loading ? 'Running…' : '▶ Run Simulation'}
    </button>
  );
}

export function LiveFeedRow({
  timestamp, domain, protocol, sourceNe, message, severity,
}: {
  timestamp: string; domain: string; protocol: string;
  sourceNe: string; message: string; severity: Severity | null;
}) {
  return (
    <div className="flex items-center gap-3 py-2 text-xs font-mono border-b border-surface-200/10">
      <span className="text-surface-200/40 w-20 flex-shrink-0">
        {new Date(timestamp).toLocaleTimeString()}
      </span>
      <span className="badge-info w-10 text-center flex-shrink-0">{domain}</span>
      <span className="text-surface-200/60 w-16 flex-shrink-0 truncate">{protocol}</span>
      <span className="text-white flex-1 truncate">{sourceNe} — {message}</span>
      {severity && <SeverityBadge severity={severity} />}
    </div>
  );
}
