import { gql } from '@apollo/client';

// Query with diagnostic fields (will work once Apollo schema cache refreshes)
export const GET_DAY_TRADING_PICKS = gql`
  query GetDayTradingPicks($mode: String!) {
    dayTradingPicks(mode: $mode) {
      asOf
      mode
      picks {
        symbol
        side
        score
        features {
          momentum15m
          rvol10m
          vwapDist
          breakoutPct
          spreadBps
          catalystScore
        }
        risk {
          atr5m
          sizeShares
          stop
          targets
          timeStopMin
        }
        notes
      }
      universeSize
      qualityThreshold
      universeSource
      # Diagnostic fields - will be available once Apollo schema cache refreshes
      # Temporarily commented out to prevent errors until cache clears
      # scannedCount
      # passedLiquidity
      # passedQuality
      # failedDataFetch
      # filteredByMicrostructure
      # filteredByVolatility
      # filteredByMomentum
    }
  }
`;

export const LOG_DAY_TRADING_OUTCOME = gql`
  mutation LogDayTradingOutcome($input: DayTradingOutcomeInput!) {
    logDayTradingOutcome(input: $input) {
      success
      message
    }
  }
`;

export const SUBSCRIBE_DAY_TRADING_UPDATES = gql`
  subscription SubscribeDayTradingUpdates($mode: String!) {
    dayTradingUpdates(mode: $mode) {
      asOf
      mode
      picks {
        symbol
        side
        score
        features {
          momentum15m
          rvol10m
          vwapDist
          breakoutPct
          spreadBps
          catalystScore
        }
        risk {
          atr5m
          sizeShares
          stop
          targets
          timeStopMin
        }
        notes
      }
      universeSize
      qualityThreshold
      universeSource
    }
  }
`;