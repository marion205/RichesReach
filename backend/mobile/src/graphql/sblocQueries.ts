import { gql } from '@apollo/client';

// SBLOC Bank Type
export const SBLOC_BANK_FRAGMENT = gql`
  fragment SBLOCBankFragment on SBLOCBankType {
    id
    name
    logoUrl
    minLtv
    maxLtv
    minLineUsd
    maxLineUsd
    typicalAprMin
    typicalAprMax
    isActive
    priority
  }
`;

// SBLOC Referral Type
export const SBLOC_REFERRAL_FRAGMENT = gql`
  fragment SBLOCReferralFragment on SBLOCReferralType {
    id
    requestedAmountUsd
    aggregatorAppId
    status
    portfolioValueUsd
    eligibleCollateralUsd
    estimatedLtv
    consentGiven
    dataScope
    consentTimestamp
    timeline
    notes
    createdAt
    updatedAt
    bank {
      ...SBLOCBankFragment
    }
  }
  ${SBLOC_BANK_FRAGMENT}
`;

// SBLOC Session Type
export const SBLOC_SESSION_FRAGMENT = gql`
  fragment SBLOCSessionFragment on SBLOCSessionType {
    id
    sessionUrl
    sessionToken
    expiresAt
    isUsed
    isExpired
    createdAt
  }
`;

// Queries
export const GET_SBLOC_BANKS = gql`
  query GetSBLOCBanks {
    sblocBanks {
      ...SBLOCBankFragment
    }
  }
  ${SBLOC_BANK_FRAGMENT}
`;

export const GET_SBLOC_REFERRAL = gql`
  query GetSBLOCReferral($id: ID!) {
    sblocReferral(id: $id) {
      ...SBLOCReferralFragment
    }
  }
  ${SBLOC_REFERRAL_FRAGMENT}
`;

export const GET_SBLOC_REFERRALS = gql`
  query GetSBLOCReferrals {
    sblocReferrals {
      ...SBLOCReferralFragment
    }
  }
  ${SBLOC_REFERRAL_FRAGMENT}
`;

// Mutations
export const CREATE_SBLOC_SESSION = gql`
  mutation CreateSBLOCSession(
    $bankId: ID!
    $requestedAmountUsd: Float!
    $consentData: JSONString!
  ) {
    createSblocSession(
      bankId: $bankId
      requestedAmountUsd: $requestedAmountUsd
      consentData: $consentData
    ) {
      success
      message
      sessionPayload {
        sessionUrl
        expiresAt
        referral {
          ...SBLOCReferralFragment
        }
      }
    }
  }
  ${SBLOC_REFERRAL_FRAGMENT}
`;

export const CREATE_SBLOC_REFERRAL = gql`
  mutation CreateSBLOCReferral(
    $bankId: ID!
    $requestedAmountUsd: Float!
    $consentData: JSONString!
  ) {
    createSblocReferral(
      bankId: $bankId
      requestedAmountUsd: $requestedAmountUsd
      consentData: $consentData
    ) {
      success
      message
      referral {
        ...SBLOCReferralFragment
      }
    }
  }
  ${SBLOC_REFERRAL_FRAGMENT}
`;

export const SYNC_SBLOC_BANKS = gql`
  mutation SyncSBLOCBanks {
    syncSblocBanks {
      success
      message
      banksCreated
    }
  }
`;

// Types for TypeScript
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
  status: string;
  portfolioValueUsd: number;
  eligibleCollateralUsd: number;
  estimatedLtv: number;
  consentGiven: boolean;
  dataScope: any;
  consentTimestamp?: string;
  timeline: any[];
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

export interface CreateSBLOCSessionResult {
  success: boolean;
  message: string;
  sessionPayload?: SBLOCSessionPayload;
}

export interface CreateSBLOCReferralResult {
  success: boolean;
  message: string;
  referral?: SBLOCReferral;
}

export interface SyncSBLOCBanksResult {
  success: boolean;
  message: string;
  banksCreated: number;
}
