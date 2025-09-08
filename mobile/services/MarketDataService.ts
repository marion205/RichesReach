import AsyncStorage from '@react-native-async-storage/async-storage';

// Market Data Interfaces
export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  timestamp: string;
  marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
}

export interface HistoricalData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketNews {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  url: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  relatedSymbols: string[];
}

export interface MarketStatus {
  isOpen: boolean;
  nextOpen?: string;
  nextClose?: string;
  timezone: string;
}

class MarketDataService {
  private apiKey: string = 'OHYSFF1AE446O7CR'; // Your Alpha Vantage API key
  private newsApiKey: string = '94a335c7316145f79840edd62f77e11e'; // Your NewsAPI key
  private baseUrl: string = 'https://www.alphavantage.co/query';
  private newsBaseUrl: string = 'https://newsapi.org/v2';
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout: number = 60000; // 1 minute cache

  constructor() {
    this.loadApiKey();
  }

  private async loadApiKey() {
    try {
      const storedKey = await AsyncStorage.getItem('alpha_vantage_api_key');
      if (storedKey) {
        this.apiKey = storedKey;
      }
    } catch (error) {
      console.log('No API key found, using demo key');
    }
  }

  public async setApiKey(apiKey: string) {
    this.apiKey = apiKey;
    try {
      await AsyncStorage.setItem('alpha_vantage_api_key', apiKey);
    } catch (error) {
      console.error('Failed to save API key:', error);
    }
  }

  private async makeApiCall(params: Record<string, string>): Promise<any> {
    const cacheKey = JSON.stringify(params);
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    const url = new URL(this.baseUrl);
    Object.entries({ ...params, apikey: this.apiKey }).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });

    try {
      const response = await fetch(url.toString());
      const data = await response.json();
      
      // Cache the response
      this.cache.set(cacheKey, { data, timestamp: Date.now() });
      
      return data;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  }

  // Get real-time stock quote
  public async getStockQuote(symbol: string): Promise<StockQuote> {
    try {
      const data = await this.makeApiCall({
        function: 'GLOBAL_QUOTE',
        symbol: symbol.toUpperCase()
      });

      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }

      const quote = data['Global Quote'];
      if (!quote) {
        throw new Error('No quote data available');
      }

      return {
        symbol: quote['01. symbol'],
        price: parseFloat(quote['05. price']),
        change: parseFloat(quote['09. change']),
        changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
        volume: parseInt(quote['06. volume']),
        high: parseFloat(quote['03. high']),
        low: parseFloat(quote['04. low']),
        open: parseFloat(quote['02. open']),
        previousClose: parseFloat(quote['08. previous close']),
        timestamp: quote['07. latest trading day'],
        marketStatus: this.getMarketStatus()
      };
    } catch (error) {
      console.error(`Failed to get quote for ${symbol}:`, error);
      // Return mock data as fallback
      return this.getMockQuote(symbol);
    }
  }

  // Get multiple stock quotes
  public async getMultipleQuotes(symbols: string[]): Promise<StockQuote[]> {
    const promises = symbols.map(symbol => this.getStockQuote(symbol));
    return Promise.all(promises);
  }

  // Get historical data
  public async getHistoricalData(symbol: string, interval: 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<HistoricalData[]> {
    try {
      const functionMap = {
        daily: 'TIME_SERIES_DAILY',
        weekly: 'TIME_SERIES_WEEKLY',
        monthly: 'TIME_SERIES_MONTHLY'
      };

      const data = await this.makeApiCall({
        function: functionMap[interval],
        symbol: symbol.toUpperCase(),
        outputsize: 'compact'
      });

      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }

      const timeSeries = data[`Time Series (${interval === 'daily' ? 'Daily' : interval === 'weekly' ? 'Weekly' : 'Monthly'})`];
      if (!timeSeries) {
        throw new Error('No historical data available');
      }

      return Object.entries(timeSeries).map(([date, values]: [string, any]) => ({
        date,
        open: parseFloat(values['1. open']),
        high: parseFloat(values['2. high']),
        low: parseFloat(values['3. low']),
        close: parseFloat(values['4. close']),
        volume: parseInt(values['5. volume'])
      })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    } catch (error) {
      console.error(`Failed to get historical data for ${symbol}:`, error);
      return this.getMockHistoricalData(symbol);
    }
  }

  // Get market news from NewsAPI
  public async getMarketNews(topics: string[] = ['finance', 'stocks', 'market']): Promise<MarketNews[]> {
    try {
      const query = topics.join(' OR ');
      const url = `${this.newsBaseUrl}/everything?q=${encodeURIComponent(query)}&apiKey=${this.newsApiKey}&sortBy=publishedAt&pageSize=20&language=en`;
      
      const response = await fetch(url);
      const data = await response.json();

      if (data.status !== 'ok') {
        throw new Error(data.message || 'Failed to fetch news');
      }

      const articles = data.articles || [];
      return articles.map((article: any, index: number) => ({
        id: `news-${index}-${Date.now()}`,
        title: article.title,
        summary: article.description || article.content?.substring(0, 200) + '...',
        source: article.source.name,
        publishedAt: article.publishedAt,
        url: article.url,
        sentiment: this.analyzeSentiment(article.title + ' ' + (article.description || '')),
        relatedSymbols: this.extractStockSymbols(article.title + ' ' + (article.description || ''))
      }));
    } catch (error) {
      console.error('Failed to get market news:', error);
      return this.getMockNews();
    }
  }

  // Get news for specific stock symbol
  public async getStockNews(symbol: string): Promise<MarketNews[]> {
    try {
      const url = `${this.newsBaseUrl}/everything?q=${encodeURIComponent(symbol)}&apiKey=${this.newsApiKey}&sortBy=publishedAt&pageSize=10&language=en`;
      
      const response = await fetch(url);
      const data = await response.json();

      if (data.status !== 'ok') {
        throw new Error(data.message || 'Failed to fetch stock news');
      }

      const articles = data.articles || [];
      return articles.map((article: any, index: number) => ({
        id: `stock-${symbol}-${index}-${Date.now()}`,
        title: article.title,
        summary: article.description || article.content?.substring(0, 200) + '...',
        source: article.source.name,
        publishedAt: article.publishedAt,
        url: article.url,
        sentiment: this.analyzeSentiment(article.title + ' ' + (article.description || '')),
        relatedSymbols: [symbol]
      }));
    } catch (error) {
      console.error(`Failed to get news for ${symbol}:`, error);
      return [];
    }
  }

  // Get market status
  public getMarketStatus(): 'open' | 'closed' | 'pre-market' | 'after-hours' {
    const now = new Date();
    const day = now.getDay();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const timeInMinutes = hour * 60 + minute;

    // Market is closed on weekends
    if (day === 0 || day === 6) {
      return 'closed';
    }

    // Market hours: 9:30 AM - 4:00 PM ET
    const marketOpen = 9 * 60 + 30; // 9:30 AM
    const marketClose = 16 * 60; // 4:00 PM
    const preMarketStart = 4 * 60; // 4:00 AM
    const afterHoursEnd = 20 * 60; // 8:00 PM

    if (timeInMinutes >= marketOpen && timeInMinutes < marketClose) {
      return 'open';
    } else if (timeInMinutes >= preMarketStart && timeInMinutes < marketOpen) {
      return 'pre-market';
    } else if (timeInMinutes >= marketClose && timeInMinutes < afterHoursEnd) {
      return 'after-hours';
    } else {
      return 'closed';
    }
  }

  // Get next market open/close times
  public getNextMarketTimes(): MarketStatus {
    const now = new Date();
    const day = now.getDay();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const timeInMinutes = hour * 60 + minute;

    const marketOpen = 9 * 60 + 30; // 9:30 AM
    const marketClose = 16 * 60; // 4:00 PM

    let nextOpen: Date;
    let nextClose: Date;

    if (day >= 1 && day <= 5) { // Weekday
      if (timeInMinutes < marketOpen) {
        // Market opens today
        nextOpen = new Date(now);
        nextOpen.setHours(9, 30, 0, 0);
        nextClose = new Date(now);
        nextClose.setHours(16, 0, 0, 0);
      } else if (timeInMinutes < marketClose) {
        // Market is open, next close is today
        nextOpen = new Date(now);
        nextOpen.setDate(nextOpen.getDate() + 1);
        nextOpen.setHours(9, 30, 0, 0);
        nextClose = new Date(now);
        nextClose.setHours(16, 0, 0, 0);
      } else {
        // Market closed, next open is tomorrow
        nextOpen = new Date(now);
        nextOpen.setDate(nextOpen.getDate() + 1);
        nextOpen.setHours(9, 30, 0, 0);
        nextClose = new Date(nextOpen);
        nextClose.setHours(16, 0, 0, 0);
      }
    } else {
      // Weekend, next open is Monday
      const daysUntilMonday = day === 0 ? 1 : 8 - day; // Sunday = 0, Saturday = 6
      nextOpen = new Date(now);
      nextOpen.setDate(nextOpen.getDate() + daysUntilMonday);
      nextOpen.setHours(9, 30, 0, 0);
      nextClose = new Date(nextOpen);
      nextClose.setHours(16, 0, 0, 0);
    }

    return {
      isOpen: this.getMarketStatus() === 'open',
      nextOpen: nextOpen.toISOString(),
      nextClose: nextClose.toISOString(),
      timezone: 'America/New_York'
    };
  }

  // Search for stocks
  public async searchStocks(query: string): Promise<any[]> {
    try {
      const data = await this.makeApiCall({
        function: 'SYMBOL_SEARCH',
        keywords: query
      });

      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }

      const matches = data.bestMatches || [];
      return matches.map((match: any) => ({
        symbol: match['1. symbol'],
        name: match['2. name'],
        type: match['3. type'],
        region: match['4. region'],
        marketOpen: match['5. marketOpen'],
        marketClose: match['6. marketClose'],
        timezone: match['7. timezone'],
        currency: match['8. currency'],
        matchScore: match['9. matchScore']
      }));
    } catch (error) {
      console.error('Failed to search stocks:', error);
      return [];
    }
  }

  // Helper methods for fallback data
  private getMockQuote(symbol: string): StockQuote {
    const basePrice = 100 + Math.random() * 200;
    const change = (Math.random() - 0.5) * 10;
    const changePercent = (change / basePrice) * 100;

    return {
      symbol,
      price: basePrice,
      change,
      changePercent,
      volume: Math.floor(Math.random() * 1000000),
      high: basePrice + Math.random() * 5,
      low: basePrice - Math.random() * 5,
      open: basePrice + (Math.random() - 0.5) * 2,
      previousClose: basePrice - change,
      timestamp: new Date().toISOString().split('T')[0],
      marketStatus: this.getMarketStatus()
    };
  }

  private getMockHistoricalData(symbol: string): HistoricalData[] {
    const data: HistoricalData[] = [];
    const basePrice = 100;
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const price = basePrice + (Math.random() - 0.5) * 20;
      
      data.push({
        date: date.toISOString().split('T')[0],
        open: price + (Math.random() - 0.5) * 2,
        high: price + Math.random() * 3,
        low: price - Math.random() * 3,
        close: price,
        volume: Math.floor(Math.random() * 1000000)
      });
    }
    
    return data;
  }

  private getMockNews(): MarketNews[] {
    return [
      {
        id: '1',
        title: 'Market Update: Tech Stocks Rally on Strong Earnings',
        summary: 'Technology stocks showed strong performance today as major companies reported better-than-expected quarterly earnings.',
        source: 'Financial News',
        publishedAt: new Date().toISOString(),
        url: 'https://example.com/news/1',
        sentiment: 'positive',
        relatedSymbols: ['AAPL', 'MSFT', 'GOOGL']
      },
      {
        id: '2',
        title: 'Federal Reserve Signals Potential Rate Changes',
        summary: 'The Federal Reserve indicated possible adjustments to interest rates in response to current economic conditions.',
        source: 'Market Watch',
        publishedAt: new Date(Date.now() - 3600000).toISOString(),
        url: 'https://example.com/news/2',
        sentiment: 'neutral',
        relatedSymbols: []
      }
    ];
  }

  private mapSentiment(score: number): 'positive' | 'negative' | 'neutral' {
    if (score > 0.1) return 'positive';
    if (score < -0.1) return 'negative';
    return 'neutral';
  }

  // Simple sentiment analysis based on keywords
  private analyzeSentiment(text: string): 'positive' | 'negative' | 'neutral' {
    const positiveWords = ['up', 'rise', 'gain', 'surge', 'rally', 'bullish', 'positive', 'growth', 'profit', 'success', 'strong', 'beat', 'exceed', 'outperform'];
    const negativeWords = ['down', 'fall', 'drop', 'decline', 'crash', 'bearish', 'negative', 'loss', 'weak', 'miss', 'disappoint', 'underperform', 'concern', 'risk'];
    
    const lowerText = text.toLowerCase();
    let positiveScore = 0;
    let negativeScore = 0;
    
    positiveWords.forEach(word => {
      if (lowerText.includes(word)) positiveScore++;
    });
    
    negativeWords.forEach(word => {
      if (lowerText.includes(word)) negativeScore++;
    });
    
    if (positiveScore > negativeScore) return 'positive';
    if (negativeScore > positiveScore) return 'negative';
    return 'neutral';
  }

  // Extract stock symbols from text
  private extractStockSymbols(text: string): string[] {
    const symbols: string[] = [];
    const commonSymbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT'];
    
    commonSymbols.forEach(symbol => {
      if (text.toUpperCase().includes(symbol)) {
        symbols.push(symbol);
      }
    });
    
    return symbols;
  }

  // Clear cache
  public clearCache() {
    this.cache.clear();
  }
}

export default new MarketDataService();
