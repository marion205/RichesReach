import { gql } from '@apollo/client';

// Risk Management Queries
export const GET_RISK_SUMMARY = gql`
  query GetRiskSummary {
    riskSummary {
      account_value
      daily_pnl
      daily_pnl_pct
      daily_trades
      active_positions
      total_exposure
      exposure_pct
      sector_exposure
      risk_level
      risk_limits {
        max_position_size
        max_daily_loss
        max_concurrent_trades
        max_sector_exposure
      }
    }
  }
`;

export const GET_ACTIVE_POSITIONS = gql`
  query GetActivePositions {
    getActivePositions {
      symbol
      side
      entryPrice
      quantity
      entryTime
      stopLossPrice
      takeProfitPrice
      maxHoldUntil
      atrStopPrice
      currentPnl
      timeRemainingMinutes
    }
  }
`;

// Risk Management Mutations
export const CREATE_POSITION = gql`
  mutation CreatePosition(
    $symbol: String!
    $side: String!
    $price: Float!
    $quantity: Int
    $atr: Float!
    $sector: String
    $confidence: Float
  ) {
    createPosition(
      symbol: $symbol
      side: $side
      price: $price
      quantity: $quantity
      atr: $atr
      sector: $sector
      confidence: $confidence
    ) {
      success
      message
      position {
        symbol
        side
        entryPrice
        quantity
        entryTime
        stopLossPrice
        takeProfitPrice
        maxHoldUntil
        atrStopPrice
      }
    }
  }
`;

export const CHECK_POSITION_EXITS = gql`
  mutation CheckPositionExits($currentPrices: JSON) {
    checkPositionExits(currentPrices: $currentPrices) {
      success
      message
      exitedPositions {
        symbol
        side
        entryPrice
        exitPrice
        quantity
        pnl
        exitReason
        exitTime
      }
    }
  }
`;

export const UPDATE_RISK_SETTINGS = gql`
  mutation UpdateRiskSettings(
    $accountValue: Float
    $riskLevel: String
  ) {
    updateRiskSettings(
      accountValue: $accountValue
      riskLevel: $riskLevel
    ) {
      success
      message
      currentSettings {
        account_value
        daily_pnl
        daily_pnl_pct
        daily_trades
        active_positions
        total_exposure
        exposure_pct
        sector_exposure
        risk_level
        risk_limits {
          max_position_size
          max_daily_loss
          max_concurrent_trades
          max_sector_exposure
        }
      }
    }
  }
`;

// Risk Management Types
export interface RiskSummary {
  account_value: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  daily_trades: number;
  active_positions: number;
  total_exposure: number;
  exposure_pct: number;
  sector_exposure: Record<string, number>;
  risk_level: string;
  risk_limits: {
    max_position_size: number;
    max_daily_loss: number;
    max_concurrent_trades: number;
    max_sector_exposure: number;
  };
}

export interface Position {
  symbol: string;
  side: string;
  entryPrice: number;
  quantity: number;
  entryTime: string;
  stopLossPrice: number;
  takeProfitPrice: number;
  maxHoldUntil: string;
  atrStopPrice: number;
  currentPnl?: number;
  timeRemainingMinutes: number;
}

export interface ExitedPosition {
  symbol: string;
  side: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  exitReason: string;
  exitTime: string;
}

export interface CreatePositionResponse {
  success: boolean;
  message: string;
  position?: Position;
}

export interface CheckExitsResponse {
  success: boolean;
  message: string;
  exitedPositions: ExitedPosition[];
}

export interface UpdateRiskSettingsResponse {
  success: boolean;
  message: string;
  currentSettings: RiskSummary;
}
