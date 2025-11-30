use chrono::Utc;
use anyhow::Result;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SentimentAnalysisResponse {
    pub symbol: String,
    pub overall_sentiment: String,  // "BULLISH", "BEARISH", "NEUTRAL"
    pub sentiment_score: f64,       // -1.0 to 1.0
    pub news_sentiment: NewsSentiment,
    pub social_sentiment: SocialSentiment,
    pub confidence: f64,
    pub timestamp: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewsSentiment {
    pub score: f64,
    pub article_count: usize,
    pub positive_articles: usize,
    pub negative_articles: usize,
    pub neutral_articles: usize,
    pub top_headlines: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SocialSentiment {
    pub score: f64,
    pub mentions_24h: usize,
    pub positive_mentions: usize,
    pub negative_mentions: usize,
    pub engagement_score: f64,
    pub trending: bool,
}

pub struct SentimentAnalysisEngine {
    // In production, this would integrate with news APIs and social APIs
}

impl SentimentAnalysisEngine {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn analyze(&self, symbol: &str) -> Result<SentimentAnalysisResponse> {
        let start = std::time::Instant::now();
        
        // Analyze news sentiment
        let news_sentiment = self.analyze_news(symbol).await?;
        
        // Analyze social sentiment
        let social_sentiment = self.analyze_social(symbol).await?;
        
        // Combine into overall sentiment
        let overall_score = news_sentiment.score * 0.6 + social_sentiment.score * 0.4;
        let overall_sentiment = if overall_score > 0.3 {
            "BULLISH".to_string()
        } else if overall_score < -0.3 {
            "BEARISH".to_string()
        } else {
            "NEUTRAL".to_string()
        };
        
        // Calculate confidence based on data quality
        let confidence = self.calculate_confidence(&news_sentiment, &social_sentiment).await?;
        
        let response = SentimentAnalysisResponse {
            symbol: symbol.to_string(),
            overall_sentiment,
            sentiment_score: overall_score,
            news_sentiment,
            social_sentiment,
            confidence,
            timestamp: Utc::now(),
        };

        tracing::info!("Sentiment analysis completed for {} in {:?}", symbol, start.elapsed());
        Ok(response)
    }

    async fn analyze_news(&self, symbol: &str) -> Result<NewsSentiment> {
        // In production, integrate with news APIs (NewsAPI, Alpha Vantage News, etc.)
        // For now, generate mock data
        
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        let article_count = 50 + rng.gen_range(0..100);
        let positive = (article_count as f64 * (0.4 + rng.gen_range(-0.1..0.1))) as usize;
        let negative = (article_count as f64 * (0.3 + rng.gen_range(-0.1..0.1))) as usize;
        let neutral = article_count - positive - negative;
        
        let score = ((positive as f64 - negative as f64) / article_count as f64).max(-1.0).min(1.0);
        
        let top_headlines = vec![
            format!("{} shows strong momentum in latest trading session", symbol),
            format!("Analysts upgrade {} outlook following earnings", symbol),
            format!("{} volatility increases amid market uncertainty", symbol),
        ];

        Ok(NewsSentiment {
            score,
            article_count,
            positive_articles: positive,
            negative_articles: negative,
            neutral_articles: neutral,
            top_headlines,
        })
    }

    async fn analyze_social(&self, symbol: &str) -> Result<SocialSentiment> {
        // In production, integrate with Twitter/X API, Reddit API, etc.
        // For now, generate mock data
        
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        let mentions_24h = 1000 + rng.gen_range(0..5000);
        let positive = (mentions_24h as f64 * (0.45 + rng.gen_range(-0.15..0.15))) as usize;
        let negative = (mentions_24h as f64 * (0.35 + rng.gen_range(-0.15..0.15))) as usize;
        
        let score = ((positive as f64 - negative as f64) / mentions_24h as f64).max(-1.0).min(1.0);
        
        let engagement_score = {
            let mut rng = rand::thread_rng();
            0.6 + rng.gen_range(-0.2..0.2)
        };
        
        let trending = mentions_24h > 3000;

        Ok(SocialSentiment {
            score,
            mentions_24h,
            positive_mentions: positive,
            negative_mentions: negative,
            engagement_score,
            trending,
        })
    }

    async fn calculate_confidence(
        &self,
        news: &NewsSentiment,
        social: &SocialSentiment,
    ) -> Result<f64> {
        // Confidence based on data volume and consistency
        let news_confidence = (news.article_count.min(100) as f64 / 100.0) * 0.5;
        let social_confidence = (social.mentions_24h.min(5000) as f64 / 5000.0) * 0.5;
        
        // Consistency bonus (if news and social agree)
        let consistency = 1.0 - (news.score - social.score).abs();
        let consistency_bonus = consistency * 0.2;
        
        Ok((news_confidence + social_confidence + consistency_bonus).min(1.0))
    }
}

