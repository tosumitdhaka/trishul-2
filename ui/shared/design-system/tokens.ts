/**
 * Trishul shared design tokens — imported by all MFE remotes.
 * Shell exposes this as "./design-system" via vite-plugin-federation.
 */
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
    800:  '#1c1c2e',
    900:  '#12121f',
    950:  '#0a0a14',
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
