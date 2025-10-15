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
      entry_price
      quantity
      entry_time
      stop_loss_price
      take_profit_price
      max_hold_until
      atr_stop_price
      current_pnl
      time_remaining_minutes
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
        entry_price
        quantity
        entry_time
        stop_loss_price
        take_profit_price
        max_hold_until
        atr_stop_price
      }
    }
  }
`;

export const CHECK_POSITION_EXITS = gql`
  mutation CheckPositionExits($currentPrices: JSON) {
    checkPositionExits(currentPrices: $currentPrices) {
      success
      message
      exited_positions {
        symbol
        side
        entry_price
        exit_price
        quantity
        pnl
        exit_reason
        exit_time
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
      current_settings {
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
  entry_price: number;
  quantity: number;
  entry_time: string;
  stop_loss_price: number;
  take_profit_price: number;
  max_hold_until: string;
  atr_stop_price: number;
  current_pnl?: number;
  time_remaining_minutes: number;
}

export interface ExitedPosition {
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  exit_reason: string;
  exit_time: string;
}

export interface CreatePositionResponse {
  success: boolean;
  message: string;
  position?: Position;
}

export interface CheckExitsResponse {
  success: boolean;
  message: string;
  exited_positions: ExitedPosition[];
}

export interface UpdateRiskSettingsResponse {
  success: boolean;
  message: string;
  current_settings: RiskSummary;
}
