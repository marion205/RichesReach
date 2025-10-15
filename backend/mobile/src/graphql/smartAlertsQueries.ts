import { gql } from '@apollo/client';

// ---------- Enums / Narrow types ----------
export type Priority = 'high' | 'medium' | 'low';
export type Timeframe = '1D' | '1W' | '1M' | '3M' | '1Y' | 'YTD' | 'All';
// Keep these aligned with backend categories
export type CategoryId =
  | 'performance'
  | 'risk'
  | 'allocation'
  | 'attribution'
  | 'market_regime'
  | 'rebalancing'
  | 'opportunity'
  | 'portfolio'
  | 'transaction'
  | 'behavior'
  | 'spending'
  | 'cashflow'
  | 'concentration'
  | 'diversification'
  | 'general';

export interface SmartAlert {
  id: string;
  type: string;
  priority: Priority;
  category: CategoryId | string; // fallback to string in case BE adds new categories
  title: string;
  message: string;
  details: Record<string, any>;
  actionable: boolean;
  suggested_actions: string[];
  coaching_tip: string;
  timestamp: string; // ISO
}

export interface AlertCategory {
  category: CategoryId | string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export interface AlertPreferences {
  enabled_categories: (CategoryId | string)[];
  priority_threshold: Priority | 'all';
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly';
  delivery_method: 'in_app' | 'push' | 'email';
  quiet_hours: { enabled: boolean; start: string; end: string };
  custom_thresholds: {
    performance_threshold: number;             // %
    volatility_threshold: number;              // %
    drawdown_threshold: number;                // % (ABS magnitude; see note below)
    sector_concentration_threshold: number;    // weight 0..1
  };
}

// ---------- GraphQL Fragments ----------
export const SMART_ALERT_FIELDS = gql`
  fragment SmartAlertFields on SmartAlert {
    id
    type
    priority
    category
    title
    message
    details
    actionable
    suggested_actions
    coaching_tip
    timestamp
  }
`;

export const ALERT_CATEGORY_FIELDS = gql`
  fragment AlertCategoryFields on AlertCategory {
    category
    name
    description
    icon
    color
  }
`;

export const ALERT_PREFERENCES_FIELDS = gql`
  fragment AlertPreferencesFields on AlertPreferences {
    enabled_categories
    priority_threshold
    frequency
    delivery_method
    quiet_hours { enabled start end }
    custom_thresholds {
      performance_threshold
      volatility_threshold
      drawdown_threshold
      sector_concentration_threshold
    }
  }
`;

// ---------- Queries ----------
export const GET_SMART_ALERTS = gql`
  ${SMART_ALERT_FIELDS}
  query GetSmartAlerts($portfolioId: String, $timeframe: String) {
    smartAlerts(portfolioId: $portfolioId, timeframe: $timeframe) {
      ...SmartAlertFields
    }
  }
`;

export const GET_ALERT_CATEGORIES = gql`
  ${ALERT_CATEGORY_FIELDS}
  query GetAlertCategories {
    alertCategories { ...AlertCategoryFields }
  }
`;

export const GET_ALERT_PREFERENCES = gql`
  ${ALERT_PREFERENCES_FIELDS}
  query GetAlertPreferences {
    alertPreferences { ...AlertPreferencesFields }
  }
`;

export const GET_ML_ANOMALIES = gql`
  query GetMLAnomalies($portfolioId: String, $timeframe: String) {
    mlAnomalies(portfolioId: $portfolioId, timeframe: $timeframe)
  }
`;

export const GET_DELIVERY_PREFERENCES = gql`
  query GetDeliveryPreferences {
    deliveryPreferences
  }
`;

export const GET_DELIVERY_HISTORY = gql`
  query GetDeliveryHistory($alertId: String!) {
    deliveryHistory(alertId: $alertId)
  }
`;

// ---------- Mutations ----------
export const UPDATE_ALERT_PREFERENCES = gql`
  mutation UpdateAlertPreferences($input: AlertPreferencesInput!) {
    updateAlertPreferences(input: $input) {
      success
      preferences {
        ...AlertPreferencesFields
      }
      error
    }
  }
  ${ALERT_PREFERENCES_FIELDS}
`;

// ---------- Safe parsers (no mutation) ----------
// If the backend already returns the correct shapes (recommended), these are light guards.
// (Optional) If you want runtime validation, swap with zod schemas later.
export const parseSmartAlerts = (data: unknown): SmartAlert[] => {
  if (!data || !Array.isArray(data)) return [];
  return data.map((a: any): SmartAlert => ({
    id: String(a?.id ?? ''),
    type: String(a?.type ?? ''),
    priority: (a?.priority ?? 'low') as Priority,
    category: (a?.category ?? 'general') as CategoryId,
    title: String(a?.title ?? ''),
    message: String(a?.message ?? ''),
    details: a?.details && typeof a.details === 'object' ? a.details : {},
    actionable: Boolean(a?.actionable),
    suggested_actions: Array.isArray(a?.suggested_actions) ? a.suggested_actions : [],
    coaching_tip: String(a?.coaching_tip ?? ''),
    timestamp: String(a?.timestamp ?? new Date().toISOString()),
  }));
};

export const parseAlertCategories = (data: unknown): AlertCategory[] => {
  if (!data || !Array.isArray(data)) return [];
  return data.map((c: any): AlertCategory => ({
    category: String(c?.category ?? 'general'),
    name: String(c?.name ?? ''),
    description: String(c?.description ?? ''),
    icon: String(c?.icon ?? 'bell'),
    color: String(c?.color ?? '#6B7280'),
  }));
};

export const parseAlertPreferences = (data: any): AlertPreferences | null => {
  if (!data) return null;
  return {
    enabled_categories: Array.isArray(data.enabled_categories) ? data.enabled_categories : [],
    priority_threshold: (data.priority_threshold ?? 'medium') as AlertPreferences['priority_threshold'],
    frequency: (data.frequency ?? 'daily') as AlertPreferences['frequency'],
    delivery_method: (data.delivery_method ?? 'in_app') as AlertPreferences['delivery_method'],
    quiet_hours: {
      enabled: Boolean(data?.quiet_hours?.enabled),
      start: String(data?.quiet_hours?.start ?? '22:00'),
      end: String(data?.quiet_hours?.end ?? '08:00'),
    },
    custom_thresholds: {
      performance_threshold: Number(data?.custom_thresholds?.performance_threshold ?? 2.0),
      volatility_threshold: Number(data?.custom_thresholds?.volatility_threshold ?? 20.0),
      // NOTE: use absolute % here (e.g. 15 for -15% drawdown) for consistency in UI
      drawdown_threshold: Math.abs(Number(data?.custom_thresholds?.drawdown_threshold ?? 15.0)),
      sector_concentration_threshold: Number(data?.custom_thresholds?.sector_concentration_threshold ?? 0.35),
    },
  };
};

// ---------- UI helpers ----------
export const getPriorityColor = (priority: Priority, isDark = false): string => {
  switch (priority) {
    case 'high': return isDark ? '#EF4444' : '#DC2626';
    case 'medium': return isDark ? '#F59E0B' : '#D97706';
    case 'low': return isDark ? '#06B6D4' : '#0891B2';
    default: return isDark ? '#A1A7AF' : '#6B7280';
  }
};

export const getPriorityIcon = (priority: Priority): string => {
  switch (priority) {
    case 'high': return 'alert-triangle';
    case 'medium': return 'alert-circle';
    case 'low': return 'info';
  }
};

export const getCategoryIcon = (category: string, categories: AlertCategory[]): string =>
  categories.find(c => c.category === category)?.icon || 'bell';

export const getCategoryColor = (category: string, categories: AlertCategory[]): string =>
  categories.find(c => c.category === category)?.color || '#6B7280';

// Time-safe "time ago"
export const formatAlertTimestamp = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return 'Just now';
  const now = new Date();
  const diff = Math.max(0, now.getTime() - date.getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
  return date.toLocaleDateString();
};

// Filters
export const filterAlertsByCategory = (alerts: SmartAlert[], category: string): SmartAlert[] =>
  category === 'all' ? alerts : alerts.filter(a => a.category === category);

export const filterAlertsByPriority = (alerts: SmartAlert[], priority: 'all' | Priority): SmartAlert[] =>
  priority === 'all' ? alerts : alerts.filter(a => a.priority === priority);

// Non-mutating sort (stable enough for UI)
export const sortAlertsByPriority = (alerts: SmartAlert[]): SmartAlert[] => {
  const order: Record<Priority, number> = { high: 3, medium: 2, low: 1 };
  return [...alerts].sort((a, b) => {
    const pa = order[a.priority] ?? 0;
    const pb = order[b.priority] ?? 0;
    if (pa !== pb) return pb - pa;
    return (new Date(b.timestamp).getTime() || 0) - (new Date(a.timestamp).getTime() || 0);
  });
};

export const getAlertSummary = (alerts: SmartAlert[]) => ({
  total: alerts.length,
  high: alerts.filter(a => a.priority === 'high').length,
  medium: alerts.filter(a => a.priority === 'medium').length,
  low: alerts.filter(a => a.priority === 'low').length,
  actionable: alerts.filter(a => a.actionable).length,
});

// Group by category (handy for a sectioned list)
export const groupAlertsByCategory = (alerts: SmartAlert[]) =>
  alerts.reduce<Record<string, SmartAlert[]>>((acc, a) => {
    (acc[a.category] ||= []).push(a);
    return acc;
  }, {});

// ---------- Legacy interfaces for backward compatibility ----------
export interface MLAnomaly {
  type: string;
  anomaly_score: number;
  confidence: number;
  description: string;
  details: Record<string, any>;
  severity: 'high' | 'medium' | 'low';
  detected_at: string;
}

export interface DeliveryPreference {
  category: string;
  priority_level: string;
  delivery_method: 'in_app' | 'push' | 'email' | 'sms' | 'all';
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  max_alerts_per_day: number;
  digest_frequency: 'immediate' | 'daily' | 'weekly';
  enabled: boolean;
}

export interface DeliveryHistory {
  delivery_method: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';
  delivery_attempted_at: string;
  delivery_confirmed_at?: string;
  error_message?: string;
  external_id?: string;
}