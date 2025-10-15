// SBLOC Types for TypeScript

export interface SBLOCBank {
  id: string;
  name: string;
  logoUrl?: string;
  minLtv: number;
  maxLtv: number;
  minLineUsd: number;
  maxLineUsd: number;
  typicalAprMin: number;
  typicalAprMax: number;
  isActive: boolean;
  priority: number;
}

export interface SBLOCReferral {
  id: string;
  requestedAmountUsd: number;
  aggregatorAppId?: string;
  status: SBLOCStatus;
  portfolioValueUsd: number;
  eligibleCollateralUsd: number;
  estimatedLtv: number;
  consentGiven: boolean;
  dataScope: SBLOCDataScope;
  consentTimestamp?: string;
  timeline: SBLOCTimelineEvent[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
  bank: SBLOCBank;
}

export interface SBLOCSession {
  id: string;
  sessionUrl: string;
  sessionToken: string;
  expiresAt: string;
  isUsed: boolean;
  isExpired: boolean;
  createdAt: string;
}

export interface SBLOCSessionPayload {
  sessionUrl: string;
  expiresAt: string;
  referral: SBLOCReferral;
}

export type SBLOCStatus = 
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'CONDITIONAL_APPROVAL'
  | 'APPROVED'
  | 'DECLINED'
  | 'WITHDRAWN'
  | 'FUNDED';

export interface SBLOCDataScope {
  identity?: boolean;
  contact?: boolean;
  portfolioSummary?: boolean;
  positions?: boolean;
  fullPositions?: boolean;
  recentTransfers?: boolean;
  income?: boolean;
}

export interface SBLOCTimelineEvent {
  status: SBLOCStatus;
  timestamp: string;
  note?: string;
  source?: string;
  previousStatus?: SBLOCStatus;
}

export interface SBLOCConsentData {
  consent: boolean;
  dataScope: SBLOCDataScope;
  bankId: string;
  timestamp: string;
}

export interface SBLOCPreQualification {
  portfolioValue: number;
  eligibleCollateral: number;
  maxBorrow: number;
  estimatedLtv: number;
  estimatedAprRange: [number, number];
  haircuts: Record<string, number>;
  concentrationLimits: Record<string, number>;
}

export interface SBLOCApplicationData {
  user: {
    name: string;
    email: string;
    phone?: string;
  };
  portfolio: {
    totalValue: number;
    positions: Array<{
      symbol: string;
      assetClass: string;
      value: number;
      eligibleValue: number;
    }>;
    eligibleCollateral: number;
    estimatedMaxBorrow: number;
  };
  requestedAmount: number;
  bankId: string;
  metadata: {
    source: string;
    userId: string;
    idempotencyKey: string;
  };
}

// Status display helpers
export const SBLOC_STATUS_LABELS: Record<SBLOCStatus, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  IN_REVIEW: 'In Review',
  CONDITIONAL_APPROVAL: 'Conditional Approval',
  APPROVED: 'Approved',
  DECLINED: 'Declined',
  WITHDRAWN: 'Withdrawn',
  FUNDED: 'Funded',
};

export const SBLOC_STATUS_COLORS: Record<SBLOCStatus, string> = {
  DRAFT: '#6B7280',
  SUBMITTED: '#3B82F6',
  IN_REVIEW: '#F59E0B',
  CONDITIONAL_APPROVAL: '#8B5CF6',
  APPROVED: '#10B981',
  DECLINED: '#EF4444',
  WITHDRAWN: '#6B7280',
  FUNDED: '#059669',
};

export const SBLOC_STATUS_ICONS: Record<SBLOCStatus, string> = {
  DRAFT: 'edit-3',
  SUBMITTED: 'send',
  IN_REVIEW: 'clock',
  CONDITIONAL_APPROVAL: 'check-circle',
  APPROVED: 'check-circle',
  DECLINED: 'x-circle',
  WITHDRAWN: 'arrow-left',
  FUNDED: 'dollar-sign',
};

// Utility functions
export const getSBLOCStatusLabel = (status: SBLOCStatus): string => {
  return SBLOC_STATUS_LABELS[status] || status;
};

export const getSBLOCStatusColor = (status: SBLOCStatus): string => {
  return SBLOC_STATUS_COLORS[status] || '#6B7280';
};

export const getSBLOCStatusIcon = (status: SBLOCStatus): string => {
  return SBLOC_STATUS_ICONS[status] || 'help-circle';
};

export const isSBLOCStatusActive = (status: SBLOCStatus): boolean => {
  return ['SUBMITTED', 'IN_REVIEW', 'CONDITIONAL_APPROVAL'].includes(status);
};

export const isSBLOCStatusCompleted = (status: SBLOCStatus): boolean => {
  return ['APPROVED', 'DECLINED', 'WITHDRAWN', 'FUNDED'].includes(status);
};

export const isSBLOCStatusSuccessful = (status: SBLOCStatus): boolean => {
  return ['APPROVED', 'FUNDED'].includes(status);
};
