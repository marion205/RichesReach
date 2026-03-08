/**
 * Private Markets — design tokens for premium fintech look (2025–2026).
 * Use for list + detail screens; easy to extend for dark mode later.
 */

export const COLORS = {
  primary: '#0F172A',       // slate-900
  accent: '#3B82F6',        // blue-500
  text: '#0F172A',
  textSecondary: '#475569',
  bgCard: '#FFFFFF',
  border: '#E2E8F0',
  scoreBg: '#1E293B',
  promiseBg: '#F8FAFC',
};

/** Spacing (px) — use for margins/padding consistency */
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
};

/** Border radius (px) */
export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
};

/** Category stripe colors for deal cards (e.g. Fintech, Climate, Health) */
export const CATEGORY_STRIPE: Record<string, string> = {
  fintech: '#3B82F6',
  climate: '#10B981',
  health: '#06B6D4',
  default: COLORS.accent,
};
