import { gql } from '@apollo/client';

export const GET_SWING_TRADING_PICKS = gql`
  query GetSwingTradingPicks($strategy: String!) {
    swingTradingPicks(strategy: $strategy) {
      asOf
      strategy
      picks {
        symbol
        side
        strategy
        score
        entryPrice
        features {
          momentum5d
          rvol5d
          atr1d
          breakoutStrength
          rsi
          distFromMA20
          reversionPotential
          high20d
        }
        risk {
          atr1d
          sizeShares
          stop
          targets
          holdDays
        }
        notes
      }
      universeSize
      universeSource
    }
  }
`;

