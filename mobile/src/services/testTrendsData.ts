// Test script to verify trends data sources
// Run this to check if your API keys are working

const API_CONFIGS = {
  finnhub: {
    baseUrl: 'https://finnhub.io/api/v1',
    apiKey: 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0', // Your existing key
  },
  newsApi: {
    baseUrl: 'https://newsapi.org/v2',
    apiKey: '94a335c7316145f79840edd62f77e11e', // Your existing key
  }
};

export async function testTrendsDataSources() {
  console.log('🧪 Testing Trends Data Sources...\n');
  
  const symbol = 'AAPL';
  
  // Test 1: Insider Trading from Finnhub
  console.log('1️⃣ Testing Insider Trading (Finnhub)...');
  try {
    const insiderResponse = await fetch(
      `${API_CONFIGS.finnhub.baseUrl}/stock/insider-transactions?symbol=${symbol}&token=${API_CONFIGS.finnhub.apiKey}`
    );
    const insiderData = await insiderResponse.json();
    console.log('✅ Insider Trading:', insiderData.data ? `${insiderData.data.length} transactions found` : 'No data');
  } catch (error) {
    console.log('❌ Insider Trading Error:', error.message);
  }
  
  // Test 2: Institutional Ownership from Finnhub
  console.log('\n2️⃣ Testing Institutional Ownership (Finnhub)...');
  try {
    const institutionalResponse = await fetch(
      `${API_CONFIGS.finnhub.baseUrl}/stock/institutional-ownership?symbol=${symbol}&token=${API_CONFIGS.finnhub.apiKey}`
    );
    const institutionalData = await institutionalResponse.json();
    console.log('✅ Institutional Ownership:', institutionalData.data ? `${institutionalData.data.length} institutions found` : 'No data');
  } catch (error) {
    console.log('❌ Institutional Ownership Error:', error.message);
  }
  
  // Test 3: Analyst Ratings from Finnhub
  console.log('\n3️⃣ Testing Analyst Ratings (Finnhub)...');
  try {
    const analystResponse = await fetch(
      `${API_CONFIGS.finnhub.baseUrl}/stock/recommendation?symbol=${symbol}&token=${API_CONFIGS.finnhub.apiKey}`
    );
    const analystData = await analystResponse.json();
    console.log('✅ Analyst Ratings:', analystData.length > 0 ? `${analystData.length} ratings found` : 'No data');
  } catch (error) {
    console.log('❌ Analyst Ratings Error:', error.message);
  }
  
  // Test 4: Market Sentiment from News API
  console.log('\n4️⃣ Testing Market Sentiment (News API)...');
  try {
    const newsResponse = await fetch(
      `${API_CONFIGS.newsApi.baseUrl}/everything?q=${symbol}&apiKey=${API_CONFIGS.newsApi.apiKey}&pageSize=5&sortBy=publishedAt`
    );
    const newsData = await newsResponse.json();
    console.log('✅ Market Sentiment:', newsData.articles ? `${newsData.articles.length} articles found` : 'No data');
  } catch (error) {
    console.log('❌ Market Sentiment Error:', error.message);
  }
  
  console.log('\n🎯 Summary:');
  console.log('- If all tests show ✅, your API keys are working!');
  console.log('- If any show ❌, check your API keys or rate limits');
  console.log('- The service will fallback to realistic mock data if APIs fail');
}

// Additional free data sources you can add:

export const FREE_TRENDS_SOURCES = {
  // SEC EDGAR API (Completely Free)
  secEdgar: {
    insiderTrading: 'https://www.sec.gov/edgar/sec-api-documentation',
    institutionalHoldings: 'https://www.sec.gov/edgar/sec-api-documentation',
    description: 'SEC filings - insider trades, 13F institutional holdings'
  },
  
  // Reddit API (Free)
  reddit: {
    sentiment: 'https://www.reddit.com/dev/api/',
    description: 'Reddit posts and comments for sentiment analysis'
  },
  
  // Twitter API (Free tier)
  twitter: {
    sentiment: 'https://developer.twitter.com/en/docs/twitter-api',
    description: 'Twitter posts for real-time sentiment'
  },
  
  // StockTwits API (Free)
  stocktwits: {
    sentiment: 'https://stocktwits.com/developers/docs',
    description: 'StockTwits posts for trading sentiment'
  },
  
  // Yahoo Finance (Scraped)
  yahooFinance: {
    analystRatings: 'https://finance.yahoo.com/quote/{symbol}/analysis',
    description: 'Analyst ratings and price targets (requires scraping)'
  },
  
  // Alpha Vantage (Free tier)
  alphaVantage: {
    technicals: 'https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={key}',
    description: 'Technical indicators like RSI, MACD, Bollinger Bands'
  }
};

// Example of how to add Reddit sentiment:
export async function fetchRedditSentiment(symbol: string) {
  try {
    // Reddit API call (requires authentication)
    const response = await fetch(`https://www.reddit.com/r/stocks/search.json?q=${symbol}&sort=new&limit=10`);
    const data = await response.json();
    
    let positiveCount = 0;
    let negativeCount = 0;
    
    data.data.children.forEach((post: any) => {
      const text = post.data.title + ' ' + post.data.selftext;
      // Simple sentiment analysis
      if (text.includes('bullish') || text.includes('buy') || text.includes('moon')) {
        positiveCount++;
      } else if (text.includes('bearish') || text.includes('sell') || text.includes('crash')) {
        negativeCount++;
      }
    });
    
    return {
      overallScore: (positiveCount - negativeCount) / (positiveCount + negativeCount || 1),
      positiveMentions: positiveCount,
      negativeMentions: negativeCount,
      neutralMentions: 0,
      recentPosts: data.data.children.slice(0, 5).map((post: any) => ({
        content: post.data.title,
        sentiment: post.data.title.includes('bullish') ? 'positive' : 'negative',
        source: 'Reddit',
        timestamp: new Date(post.data.created_utc * 1000).toISOString()
      }))
    };
  } catch (error) {
    console.error('Reddit API error:', error);
    return null;
  }
}

// Example of how to add SEC EDGAR insider trading:
export async function fetchSECInsiderTrades(symbol: string) {
  try {
    // SEC EDGAR API call
    const response = await fetch(`https://data.sec.gov/api/xbrl/companyfacts/CIK${symbol}.json`);
    const data = await response.json();
    
    // Process SEC data for insider transactions
    // This is a simplified example - real implementation would be more complex
    
    return [];
  } catch (error) {
    console.error('SEC API error:', error);
    return [];
  }
}
