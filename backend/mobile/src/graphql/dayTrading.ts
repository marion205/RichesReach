import { gql } from "@apollo/client";

export const GET_DAY_TRADING_PICKS = gql`
  query GetDayTradingPicks($mode: String, $maxPositions: Int, $minScore: Float) {
    dayTradingPicks {
      as_of
      mode
      picks {
        symbol
        side
        score
        features {
          momentum_15m
          rvol_10m
          vwap_dist
          breakout_pct
          spread_bps
          catalyst_score
        }
        risk {
          atr_5m
          size_shares
          stop
          targets
          time_stop_min
        }
        notes
      }
      universe_size
      quality_threshold
    }
  }
`;

export const LOG_DAY_TRADING_OUTCOME = gql`
  mutation LogDayTradingOutcome($input: DayTradingOutcomeInput!) {
    dayTradingOutcome(input: $input) {
      success
      message
      record {
        symbol
        side
        entry_price
        exit_price
        entry_time
        exit_time
        mode
        outcome
        timestamp
      }
    }
  }
`;
