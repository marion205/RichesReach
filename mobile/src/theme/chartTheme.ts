/**
 * Chart Theme System
 * Provides consistent colors, gradients, and styling for charts
 */

export type ChartTheme = 'light' | 'dark';

export interface ChartThemeColors {
  background: string;
  gridLines: string;
  priceLineUp: string;
  priceLineDown: string;
  priceAreaUp: string;
  priceAreaDown: string;
  momentDot: string;
  momentDotActive: string;
  momentGlow: string;
  text: string;
  textSecondary: string;
  crosshair: string;
  crosshairLabel: string;
}

export interface CategoryStyle {
  color: string;
  gradient: [string, string];
  icon: string;
  shadowColor: string;
}

export const chartThemes: Record<ChartTheme, ChartThemeColors> = {
  light: {
    background: '#FFFFFF',
    gridLines: '#F0F0F0',
    priceLineUp: '#10B981',      // Green
    priceLineDown: '#EF4444',    // Red
    priceAreaUp: 'rgba(16, 185, 129, 0.1)',
    priceAreaDown: 'rgba(239, 68, 68, 0.1)',
    momentDot: '#2F80ED',
    momentDotActive: '#1E40AF',
    momentGlow: 'rgba(47, 128, 237, 0.4)',
    text: '#111827',
    textSecondary: '#6B7280',
    crosshair: '#7AA2FF',
    crosshairLabel: '#1F2937',
  },
  dark: {
    background: '#0F172A',
    gridLines: '#1E293B',
    priceLineUp: '#10B981',
    priceLineDown: '#EF4444',
    priceAreaUp: 'rgba(16, 185, 129, 0.15)',
    priceAreaDown: 'rgba(239, 68, 68, 0.15)',
    momentDot: '#60A5FA',
    momentDotActive: '#3B82F6',
    momentGlow: 'rgba(96, 165, 250, 0.5)',
    text: '#F1F5F9',
    textSecondary: '#94A3B8',
    crosshair: '#7AA2FF',
    crosshairLabel: '#E2E8F0',
  },
};

export const categoryStyles: Record<string, CategoryStyle> = {
  EARNINGS: {
    color: '#10B981',
    gradient: ['#10B981', '#059669'],
    icon: '💰',
    shadowColor: '#10B981',
  },
  NEWS: {
    color: '#3B82F6',
    gradient: ['#3B82F6', '#2563EB'],
    icon: '📰',
    shadowColor: '#3B82F6',
  },
  INSIDER: {
    color: '#F59E0B',
    gradient: ['#F59E0B', '#D97706'],
    icon: '👤',
    shadowColor: '#F59E0B',
  },
  MACRO: {
    color: '#8B5CF6',
    gradient: ['#8B5CF6', '#7C3AED'],
    icon: '🌍',
    shadowColor: '#8B5CF6',
  },
  SENTIMENT: {
    color: '#EF4444',
    gradient: ['#EF4444', '#DC2626'],
    icon: '😊',
    shadowColor: '#EF4444',
  },
  OTHER: {
    color: '#6B7280',
    gradient: ['#6B7280', '#4B5563'],
    icon: '•',
    shadowColor: '#6B7280',
  },
};

export const getCategoryStyle = (category: string): CategoryStyle => {
  return categoryStyles[category] || categoryStyles.OTHER;
};

