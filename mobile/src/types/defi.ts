/**
 * Shared types for DeFi-related functionality
 */

export interface Reserve {
  symbol: string;
  name: string;
  ltv: number;
  liquidationThreshold: number;
  canBeCollateral: boolean;
  supplyApy: number;
  variableBorrowApy: number;
  stableBorrowApy: number;
}

export interface CryptoHolding {
  cryptocurrency: {
    symbol: string;
    name: string;
  };
  quantity: number;
  current_value: number;
  unrealized_pnl_percentage: number;
}
