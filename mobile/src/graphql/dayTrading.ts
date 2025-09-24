import { gql } from '@apollo/client';

export const GET_DAY_TRADING_PICKS = gql`
  query GetDayTradingPicks($mode: String!) {
    dayTradingPicks(mode: $mode) {
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
    logDayTradingOutcome(input: $input) {
      success
      message
    }
  }
`;

export const SUBSCRIBE_DAY_TRADING_UPDATES = gql`
  subscription SubscribeDayTradingUpdates($mode: String!) {
    dayTradingUpdates(mode: $mode) {
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