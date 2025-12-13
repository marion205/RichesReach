// src/reinforcement_learning.rs
// Reinforcement Learning Meta-Layer
// Adaptive strategy selection per user based on performance feedback

use std::collections::HashMap;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::portfolio_memory::{PortfolioMemoryEngine, UserProfile};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyAction {
    pub user_id: String, // User identifier for policy tracking
    pub strategy_name: String,
    pub symbol: String,
    pub context: StrategyContext,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyContext {
    pub regime_mood: String,
    pub iv_regime: String, // "Low" | "Medium" | "High"
    pub dte_bucket: String, // "0-7" | "8-30" | "31-60" | "60+"
    pub account_size_tier: String, // "Small" | "Medium" | "Large"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RewardSignal {
    pub action: StrategyAction,
    pub reward: f64, // PnL percentage or normalized score
    pub outcome: String, // "Win" | "Loss" | "Breakeven"
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyPolicy {
    pub user_id: String,
    pub strategy_weights: HashMap<String, f64>, // strategy -> weight (0.0-1.0)
    pub context_preferences: HashMap<String, HashMap<String, f64>>, // context_key -> (value -> weight)
    pub exploration_rate: f64, // Epsilon: probability of trying new strategies
    pub learning_rate: f64, // Alpha: how fast to update weights
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyRecommendation {
    pub user_id: String,
    pub recommended_strategies: Vec<RecommendedStrategy>,
    pub reasoning: String,
    pub confidence: f64,
    pub exploration_suggestion: Option<String>, // Strategy to try for exploration
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecommendedStrategy {
    pub strategy_name: String,
    pub symbol: String,
    pub weight: f64, // How much to allocate to this strategy
    pub expected_reward: f64, // Predicted PnL %
    pub confidence: f64,
    pub reasoning: String,
}

pub struct ReinforcementLearningEngine {
    pme: Arc<PortfolioMemoryEngine>,
    policies: Arc<RwLock<HashMap<String, StrategyPolicy>>>, // user_id -> policy
    reward_history: Arc<RwLock<HashMap<String, Vec<RewardSignal>>>>, // user_id -> rewards
}

impl ReinforcementLearningEngine {
    pub fn new(pme: Arc<PortfolioMemoryEngine>) -> Self {
        Self {
            pme,
            policies: Arc::new(RwLock::new(HashMap::new())),
            reward_history: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Update policy based on reward signal (Q-learning style)
    pub async fn update_policy(&self, reward: RewardSignal) -> anyhow::Result<()> {
        let user_id = reward.user_id();
        
        let mut policies = self.policies.write().await;
        let policy = policies
            .entry(user_id.clone())
            .or_insert_with(|| self.create_default_policy(&user_id));

        // Update strategy weight using Q-learning update rule
        let strategy_key = format!("{}::{}", reward.action.strategy_name, reward.action.symbol);
        let current_weight = policy.strategy_weights.get(&strategy_key).copied().unwrap_or(0.5);
        
        // Q-learning update: Q(s,a) = Q(s,a) + alpha * (reward + gamma * max_future_Q - Q(s,a))
        // Simplified: weight = weight + learning_rate * (reward - weight)
        let new_weight = current_weight + policy.learning_rate * (reward.reward - current_weight);
        policy.strategy_weights.insert(strategy_key, new_weight.clamp(0.0, 1.0));

        // Update context preferences
        let context_key = format!("{}::{}", reward.action.context.regime_mood, reward.action.context.iv_regime);
        let context_prefs = policy.context_preferences
            .entry(context_key)
            .or_insert_with(HashMap::new);
        context_prefs.insert(reward.action.strategy_name.clone(), new_weight);

        policy.last_updated = Utc::now();

        // Store reward in history
        let mut rewards = self.reward_history.write().await;
        rewards
            .entry(user_id)
            .or_insert_with(Vec::new)
            .push(reward);

        Ok(())
    }

    /// Get strategy recommendation for a user based on learned policy
    pub async fn recommend_strategies(
        &self,
        user_id: &str,
        context: StrategyContext,
        available_strategies: Vec<String>,
    ) -> anyhow::Result<StrategyRecommendation> {
        let policies = self.policies.read().await;
        let policy = policies
            .get(user_id)
            .cloned()
            .unwrap_or_else(|| self.create_default_policy(user_id));

        // Get user profile for additional context
        let profile = self.pme.get_profile(user_id).await?;

        // Score each available strategy
        let mut strategy_scores: Vec<(String, f64, String)> = Vec::new();

        for strategy in &available_strategies {
            let strategy_key = format!("{}::{}", strategy, context.regime_mood);
            let base_weight = policy.strategy_weights.get(&strategy_key).copied().unwrap_or(0.5);

            // Adjust based on user's historical performance with this strategy
            let user_strategy_win_rate = profile
                .preferred_strategies
                .get(strategy)
                .copied()
                .unwrap_or(0.5);

            // Context bonus
            let context_key = format!("{}::{}", context.regime_mood, context.iv_regime);
            let context_bonus = policy.context_preferences
                .get(&context_key)
                .and_then(|prefs| prefs.get(strategy))
                .copied()
                .unwrap_or(0.0);

            // Combined score
            let score = (base_weight * 0.4 + user_strategy_win_rate * 0.4 + context_bonus * 0.2).clamp(0.0, 1.0);

            let reasoning = if user_strategy_win_rate > 0.6 {
                format!("Strong historical performance ({:.1}% win rate)", user_strategy_win_rate * 100.0)
            } else if user_strategy_win_rate < 0.4 {
                format!("Weak historical performance ({:.1}% win rate) - consider avoiding", user_strategy_win_rate * 100.0)
            } else {
                format!("Moderate performance ({:.1}% win rate)", user_strategy_win_rate * 100.0)
            };

            strategy_scores.push((strategy.clone(), score, reasoning));
        }

        // Sort by score (descending)
        strategy_scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        // Select top strategies (exploitation) or random (exploration)
        let exploration_rate = policy.exploration_rate;
        let use_exploration = rand::random::<f64>() < exploration_rate;

        let recommended_strategies: Vec<RecommendedStrategy> = if use_exploration && strategy_scores.len() > 1 {
            // Exploration: try a strategy that's not the top one
            let exploration_idx = (strategy_scores.len() as f64 * 0.3) as usize; // Try 30th percentile
            let (strategy, score, reasoning) = &strategy_scores[exploration_idx];
            vec![RecommendedStrategy {
                strategy_name: strategy.clone(),
                symbol: "SPX".to_string(), // Default, should be passed in
                weight: 0.3, // Lower weight for exploration
                expected_reward: score * 0.1, // Conservative estimate
                confidence: 0.5,
                reasoning: format!("Exploration: {}", reasoning),
            }]
        } else {
            // Exploitation: top strategies
            strategy_scores
                .into_iter()
                .take(3)
                .enumerate()
                .map(|(idx, (strategy, score, reasoning))| {
                    let weight = match idx {
                        0 => 0.5, // Top strategy gets 50%
                        1 => 0.3, // Second gets 30%
                        _ => 0.2, // Third gets 20%
                    };
                    RecommendedStrategy {
                        strategy_name: strategy,
                        symbol: "SPX".to_string(), // Default
                        weight,
                        expected_reward: score * 0.15, // Estimate 15% max return
                        confidence: score,
                        reasoning,
                    }
                })
                .collect()
        };

        let reasoning = if use_exploration {
            format!("Exploration mode ({}% chance) - trying new strategy", exploration_rate * 100.0)
        } else {
            format!("Exploitation mode - using top performing strategies")
        };

        let confidence = if recommended_strategies.is_empty() {
            0.5
        } else {
            recommended_strategies.iter().map(|s| s.confidence).sum::<f64>() / recommended_strategies.len() as f64
        };

        Ok(StrategyRecommendation {
            user_id: user_id.to_string(),
            recommended_strategies,
            reasoning,
            confidence,
            exploration_suggestion: if use_exploration {
                Some("Trying new strategy for learning".to_string())
            } else {
                None
            },
            timestamp: Utc::now(),
        })
    }

    /// Get current policy for a user
    pub async fn get_policy(&self, user_id: &str) -> anyhow::Result<StrategyPolicy> {
        let policies = self.policies.read().await;
        Ok(policies
            .get(user_id)
            .cloned()
            .unwrap_or_else(|| self.create_default_policy(user_id)))
    }

    /// Update exploration rate (decay over time as user learns)
    pub async fn update_exploration_rate(&self, user_id: &str, new_rate: f64) -> anyhow::Result<()> {
        let mut policies = self.policies.write().await;
        if let Some(policy) = policies.get_mut(user_id) {
            policy.exploration_rate = new_rate.clamp(0.0, 1.0);
            policy.last_updated = Utc::now();
        }
        Ok(())
    }

    fn create_default_policy(&self, user_id: &str) -> StrategyPolicy {
        StrategyPolicy {
            user_id: user_id.to_string(),
            strategy_weights: HashMap::new(),
            context_preferences: HashMap::new(),
            exploration_rate: 0.2, // Start with 20% exploration
            learning_rate: 0.1, // 10% learning rate
            last_updated: Utc::now(),
        }
    }
}

// Helper to extract user_id from reward
impl RewardSignal {
    pub fn user_id(&self) -> String {
        self.action.user_id.clone()
    }
}

