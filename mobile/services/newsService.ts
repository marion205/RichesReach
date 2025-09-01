import AsyncStorage from '@react-native-async-storage/async-storage';

// News API Configuration
const NEWS_API_KEY = '94a335c7316145f79840edd62f77e11e';
const NEWS_API_BASE_URL = 'https://newsapi.org/v2';

// News Categories
export const NEWS_CATEGORIES = {
  ALL: 'all',
  MARKETS: 'markets',
  TECHNOLOGY: 'technology',
  CRYPTO: 'crypto',
  ECONOMY: 'economy',
  PERSONAL_FINANCE: 'personal-finance',
  INVESTING: 'investing',
  REAL_ESTATE: 'real-estate',
} as const;

export type NewsCategory = typeof NEWS_CATEGORIES[keyof typeof NEWS_CATEGORIES];

// News Article Interface
export interface NewsArticle {
  id: string;
  title: string;
  description: string;
  url: string;
  publishedAt: string;
  source: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  imageUrl?: string;
  category: NewsCategory;
  readTime?: number;
  isSaved?: boolean;
}

// News Service Class
class NewsService {
  private savedArticles: NewsArticle[] = [];
  private userPreferences: {
    categories: NewsCategory[];
    sources: string[];
    keywords: string[];
  } = {
    categories: [NEWS_CATEGORIES.ALL],
    sources: [],
    keywords: [],
  };

  constructor() {
    this.loadSavedArticles();
    this.loadUserPreferences();
  }

  // Load saved articles from storage
  private async loadSavedArticles() {
    try {
      const saved = await AsyncStorage.getItem('savedArticles');
      if (saved) {
        this.savedArticles = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Error loading saved articles:', error);
    }
  }

  // Load user preferences from storage
  private async loadUserPreferences() {
    try {
      const prefs = await AsyncStorage.getItem('newsPreferences');
      if (prefs) {
        this.userPreferences = JSON.parse(prefs);
      }
    } catch (error) {
      console.error('Error loading news preferences:', error);
    }
  }

  // Save articles to storage
  private async saveArticlesToStorage() {
    try {
      await AsyncStorage.setItem('savedArticles', JSON.stringify(this.savedArticles));
    } catch (error) {
      console.error('Error saving articles:', error);
    }
  }

  // Save preferences to storage
  private async savePreferencesToStorage() {
    try {
      await AsyncStorage.setItem('newsPreferences', JSON.stringify(this.userPreferences));
    } catch (error) {
      console.error('Error saving preferences:', error);
    }
  }

  // Get real-time news from API
  async getRealTimeNews(category: NewsCategory = NEWS_CATEGORIES.ALL): Promise<NewsArticle[]> {
    try {
      // Build query parameters
      let query = 'finance OR investing OR stocks OR markets OR economy';
      let categoryParam = '';
      
      // Add category-specific keywords
      switch (category) {
        case NEWS_CATEGORIES.MARKETS:
          query += ' OR "stock market" OR "wall street" OR "S&P 500" OR "NASDAQ"';
          break;
        case NEWS_CATEGORIES.TECHNOLOGY:
          query += ' OR "tech stocks" OR "artificial intelligence" OR "AI" OR "technology sector"';
          break;
        case NEWS_CATEGORIES.CRYPTO:
          query += ' OR "bitcoin" OR "cryptocurrency" OR "blockchain" OR "crypto"';
          break;
        case NEWS_CATEGORIES.ECONOMY:
          query += ' OR "federal reserve" OR "inflation" OR "GDP" OR "economic growth"';
          break;
        case NEWS_CATEGORIES.PERSONAL_FINANCE:
          query += ' OR "personal finance" OR "budgeting" OR "saving" OR "retirement"';
          break;
        case NEWS_CATEGORIES.INVESTING:
          query += ' OR "investment" OR "portfolio" OR "mutual funds" OR "ETFs"';
          break;
        case NEWS_CATEGORIES.REAL_ESTATE:
          query += ' OR "real estate" OR "housing market" OR "mortgage rates"';
          break;
      }
      
      // Make real API call to NewsAPI
      const response = await fetch(
        `${NEWS_API_BASE_URL}/everything?q=${encodeURIComponent(query)}&language=en&sortBy=publishedAt&pageSize=20&apiKey=${NEWS_API_KEY}`
      );
      
      if (!response.ok) {
        throw new Error(`NewsAPI error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Transform API response to our format
      const articles: NewsArticle[] = data.articles.map((article: any, index: number) => ({
        id: `real-${index}`,
        title: article.title || 'No Title',
        description: article.description || 'No description available',
        url: article.url || '#',
        publishedAt: article.publishedAt || new Date().toISOString(),
        source: article.source?.name || 'Unknown Source',
        sentiment: this.analyzeSentiment(article.title + ' ' + article.description),
        imageUrl: article.urlToImage || this.getDefaultImage(category),
        category: category,
        readTime: this.calculateReadTime(article.title + ' ' + article.description),
        isSaved: false,
      }));
      
      return articles;
    } catch (error) {
      console.error('Error fetching real news:', error);
      // Fallback to mock data if API fails
      return this.generateMockNews(category);
    }
  }

  // Get personalized news based on user preferences
  async getPersonalizedNews(): Promise<NewsArticle[]> {
    try {
      const allNews = await this.getRealTimeNews();
      
      // Filter based on user preferences
      let personalized = allNews;
      
      if (this.userPreferences.categories.length > 0 && 
          !this.userPreferences.categories.includes(NEWS_CATEGORIES.ALL)) {
        personalized = personalized.filter(article => 
          this.userPreferences.categories.includes(article.category)
        );
      }
      
      if (this.userPreferences.keywords.length > 0) {
        personalized = personalized.filter(article => 
          this.userPreferences.keywords.some(keyword => 
            article.title.toLowerCase().includes(keyword.toLowerCase()) ||
            article.description.toLowerCase().includes(keyword.toLowerCase())
          )
        );
      }
      
      return personalized;
    } catch (error) {
      console.error('Error fetching personalized news:', error);
      return this.getFallbackNews();
    }
  }

  // Save article
  async saveArticle(article: NewsArticle): Promise<void> {
    const existingIndex = this.savedArticles.findIndex(a => a.id === article.id);
    
    if (existingIndex === -1) {
      this.savedArticles.push({ ...article, isSaved: true });
    } else {
      this.savedArticles[existingIndex].isSaved = true;
    }
    
    await this.saveArticlesToStorage();
  }

  // Unsave article
  async unsaveArticle(articleId: string): Promise<void> {
    this.savedArticles = this.savedArticles.filter(a => a.id !== articleId);
    await this.saveArticlesToStorage();
  }

  // Get saved articles
  async getSavedArticles(): Promise<NewsArticle[]> {
    return this.savedArticles;
  }

  // Update user preferences
  async updatePreferences(preferences: Partial<typeof this.userPreferences>): Promise<void> {
    this.userPreferences = { ...this.userPreferences, ...preferences };
    await this.savePreferencesToStorage();
  }

  // Get user preferences
  getPreferences() {
    return { ...this.userPreferences };
  }

  // Generate mock news for demo (replace with real API in production)
  private generateMockNews(category: NewsCategory): NewsArticle[] {
    const baseNews = [
      {
        id: '1',
        title: 'Federal Reserve Signals Potential Rate Cuts in 2024',
        description: 'The Federal Reserve indicated today that it may consider interest rate reductions in the coming year as inflation continues to moderate.',
        url: 'https://www.reuters.com/markets/us/federal-reserve-signals-potential-rate-cuts-2024-2024-01-15/',
        publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        source: 'Reuters',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.ECONOMY,
        readTime: 3,
      },
      {
        id: '2',
        title: 'Tech Stocks Rally on Strong Earnings Reports',
        description: 'Major technology companies exceeded quarterly expectations, driving a broad market rally and pushing indices to new highs.',
        url: 'https://www.bloomberg.com/news/articles/2024-01-15/tech-stocks-rally-on-strong-earnings-reports',
        publishedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        source: 'Bloomberg',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.TECHNOLOGY,
        readTime: 4,
      },
      {
        id: '3',
        title: 'Oil Prices Decline Amid Global Economic Concerns',
        description: 'Crude oil futures fell sharply as traders weighed concerns about global economic growth and demand prospects.',
        url: 'https://www.marketwatch.com/story/oil-prices-decline-amid-global-economic-concerns-2024-01-15',
        publishedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        source: 'MarketWatch',
        sentiment: 'negative' as const,
        imageUrl: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.MARKETS,
        readTime: 2,
      },
      {
        id: '4',
        title: 'Cryptocurrency Market Shows Signs of Recovery',
        description: 'Bitcoin and other major cryptocurrencies gained ground as institutional adoption continues to grow.',
        url: 'https://www.coindesk.com/markets/cryptocurrency-market-shows-signs-of-recovery-2024-01-15/',
        publishedAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        source: 'CoinDesk',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.CRYPTO,
        readTime: 3,
      },
      {
        id: '5',
        title: 'Housing Market Data Shows Mixed Signals',
        description: 'New home sales data revealed conflicting trends, with some regions showing strength while others face challenges.',
        url: 'https://www.wsj.com/articles/housing-market-data-shows-mixed-signals-2024-01-15',
        publishedAt: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(),
        source: 'Wall Street Journal',
        sentiment: 'neutral' as const,
        imageUrl: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.REAL_ESTATE,
        readTime: 4,
      },
      {
        id: '6',
        title: 'New Investment Strategies for 2024',
        description: 'Financial advisors recommend diversified portfolios with focus on emerging markets and sustainable investments.',
        url: 'https://www.investopedia.com/investment-strategies-2024-2024-01-15/',
        publishedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
        source: 'Investopedia',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.INVESTING,
        readTime: 5,
      },
      {
        id: '7',
        title: 'Personal Finance Apps Revolutionize Budgeting',
        description: 'Mobile applications are making it easier than ever for individuals to track spending and save money.',
        url: 'https://www.forbes.com/personal-finance-apps-2024-2024-01-15/',
        publishedAt: new Date(Date.now() - 14 * 60 * 60 * 1000).toISOString(),
        source: 'Forbes',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.PERSONAL_FINANCE,
        readTime: 3,
      },
      {
        id: '8',
        title: 'Global Markets React to Trade Agreement',
        description: 'International markets showed positive movement following the announcement of new trade agreements.',
        url: 'https://www.ft.com/markets/global-trade-agreement-2024-01-15/',
        publishedAt: new Date(Date.now() - 16 * 60 * 60 * 1000).toISOString(),
        source: 'Financial Times',
        sentiment: 'positive' as const,
        imageUrl: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop',
        category: NEWS_CATEGORIES.MARKETS,
        readTime: 4,
      }
    ];

    // Filter by category if not ALL
    if (category !== NEWS_CATEGORIES.ALL) {
      return baseNews.filter(article => article.category === category);
    }

    return baseNews;
  }

  // Fallback news if API fails
  private getFallbackNews(): NewsArticle[] {
    return [
      {
        id: 'fallback-1',
        title: 'Market Update: S&P 500 Shows Resilience',
        description: 'Despite market volatility, the S&P 500 continues to demonstrate strength in key sectors.',
        url: 'https://example.com/fallback-news-1',
        publishedAt: new Date().toISOString(),
        source: 'Market Update',
        sentiment: 'neutral' as const,
        category: NEWS_CATEGORIES.MARKETS,
        readTime: 2,
      }
    ];
  }

  // Get news categories with counts
  async getNewsCategories(): Promise<{ category: NewsCategory; count: number; label: string }[]> {
    const categories = [
      { category: NEWS_CATEGORIES.ALL, label: 'All News' },
      { category: NEWS_CATEGORIES.MARKETS, label: 'Markets' },
      { category: NEWS_CATEGORIES.TECHNOLOGY, label: 'Technology' },
      { category: NEWS_CATEGORIES.CRYPTO, label: 'Crypto' },
      { category: NEWS_CATEGORIES.ECONOMY, label: 'Economy' },
      { category: NEWS_CATEGORIES.PERSONAL_FINANCE, label: 'Personal Finance' },
      { category: NEWS_CATEGORIES.INVESTING, label: 'Investing' },
      { category: NEWS_CATEGORIES.REAL_ESTATE, label: 'Real Estate' },
    ];

    // Get counts for each category
    const categoriesWithCounts = await Promise.all(
      categories.map(async ({ category, label }) => {
        const news = await this.getRealTimeNews(category);
        return { category, count: news.length, label };
      })
    );

    return categoriesWithCounts;
  }

  // Analyze sentiment of text
  private analyzeSentiment(text: string): 'positive' | 'negative' | 'neutral' {
    const positiveWords = ['gain', 'rise', 'up', 'positive', 'growth', 'profit', 'bullish', 'surge', 'rally', 'increase', 'strong', 'recovery'];
    const negativeWords = ['fall', 'decline', 'down', 'negative', 'loss', 'bearish', 'crash', 'drop', 'decrease', 'weak', 'recession', 'crisis'];
    
    const lowerText = text.toLowerCase();
    let positiveCount = 0;
    let negativeCount = 0;
    
    positiveWords.forEach(word => {
      if (lowerText.includes(word)) positiveCount++;
    });
    
    negativeWords.forEach(word => {
      if (lowerText.includes(word)) negativeCount++;
    });
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }

  // Calculate read time based on text length
  private calculateReadTime(text: string): number {
    const wordsPerMinute = 200;
    const wordCount = text.split(' ').length;
    return Math.ceil(wordCount / wordsPerMinute);
  }

  // Get default image for category
  private getDefaultImage(category: NewsCategory): string {
    const defaultImages: Record<string, string> = {
      [NEWS_CATEGORIES.MARKETS]: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.TECHNOLOGY]: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.CRYPTO]: 'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.ECONOMY]: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.PERSONAL_FINANCE]: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.INVESTING]: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop',
      [NEWS_CATEGORIES.REAL_ESTATE]: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=200&fit=crop',
    };
    
    return defaultImages[category] || defaultImages[NEWS_CATEGORIES.MARKETS];
  }
}

export default new NewsService();
