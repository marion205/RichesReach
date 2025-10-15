import { gql } from "@apollo/client";

export const GET_ML_SYSTEM_STATUS = gql`
  query GetMLSystemStatus {
    mlSystemStatus {
      outcome_tracking {
        total_outcomes
        recent_outcomes
      }
      models {
        safe_model
        aggressive_model
      }
      bandit {
        breakout {
          win_rate
          confidence
          alpha
          beta
        }
        mean_reversion {
          win_rate
          confidence
          alpha
          beta
        }
        momentum {
          win_rate
          confidence
          alpha
          beta
        }
        etf_rotation {
          win_rate
          confidence
          alpha
          beta
        }
      }
      last_training {
        SAFE
        AGGRESSIVE
      }
      ml_available
    }
  }
`;

export const TRAIN_MODELS = gql`
  mutation TrainModels($modes: [String!]) {
    trainModels(modes: $modes) {
      success
      message
      results {
        SAFE {
          model_id
          mode
          auc
          precision_at_3
          hit_rate
          avg_return
          sharpe_ratio
          max_drawdown
          training_samples
          validation_samples
          created_at
        }
        AGGRESSIVE {
          model_id
          mode
          auc
          precision_at_3
          hit_rate
          avg_return
          sharpe_ratio
          max_drawdown
          training_samples
          validation_samples
          created_at
        }
      }
    }
  }
`;

export const GET_BANDIT_STRATEGY = gql`
  mutation GetBanditStrategy($context: JSON) {
    banditStrategy(context: $context) {
      selected_strategy
      context {
        vix_level
        market_trend
        volatility_regime
        time_of_day
      }
      performance {
        breakout {
          win_rate
          confidence
          alpha
          beta
        }
        mean_reversion {
          win_rate
          confidence
          alpha
          beta
        }
        momentum {
          win_rate
          confidence
          alpha
          beta
        }
        etf_rotation {
          win_rate
          confidence
          alpha
          beta
        }
      }
    }
  }
`;

export const UPDATE_BANDIT_REWARD = gql`
  mutation UpdateBanditReward($strategy: String!, $reward: Float!) {
    updateBanditReward(strategy: $strategy, reward: $reward) {
      success
      message
      performance {
        breakout {
          win_rate
          confidence
          alpha
          beta
        }
        mean_reversion {
          win_rate
          confidence
          alpha
          beta
        }
        momentum {
          win_rate
          confidence
          alpha
          beta
        }
        etf_rotation {
          win_rate
          confidence
          alpha
          beta
        }
      }
    }
  }
`;

export const LOG_DAY_TRADING_OUTCOME_ENHANCED = gql`
  mutation LogDayTradingOutcomeEnhanced(
    $symbol: String!
    $side: String!
    $entryPrice: Float!
    $exitPrice: Float!
    $entryTime: String!
    $exitTime: String!
    $mode: String!
    $outcome: String!
    $features: JSON!
    $score: Float!
  ) {
    dayTradingOutcome(
      symbol: $symbol
      side: $side
      entryPrice: $entryPrice
      exitPrice: $exitPrice
      entryTime: $entryTime
      exitTime: $exitTime
      mode: $mode
      outcome: $outcome
      features: $features
      score: $score
    ) {
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
        features
        score
        timestamp
      }
      training_triggered
    }
  }
`;
