import { NewsItem } from '../types/news';
import logger from '../../../utils/logger';

interface NewsApiResponse {
  articles: NewsApiArticle[];
  totalResults: number;
  status: string;
}

interface NewsApiArticle {
  source: {
    id: string;
    name: string;
  };
  author: string;
  title: string;
  description: string;
  url: string;
  urlToImage: string;
  publishedAt: string;
  content: string;
}

class NewsService {
  private apiKey: string;
  private baseUrl: string = 'https://newsapi.org/v2';

  constructor() {
    this.apiKey = process.env.EXPO_PUBLIC_NEWS_API_KEY || '94a335c7316145f79840edd62f77e11e';
  }

  async getFinancialNews(category: string = 'business', pageSize: number = 20): Promise<NewsItem[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/everything?q=finance OR stocks OR investing OR market OR earnings OR trading&language=en&sortBy=publishedAt&pageSize=${pageSize}&apiKey=${this.apiKey}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`News API error: ${response.status}`);
      }

      const data: NewsApiResponse = await response.json();
      return this.transformNewsData(data.articles);
    } catch (error) {
      logger.error('Error fetching financial news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  async getMarketNews(): Promise<NewsItem[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/top-headlines?category=business&country=us&pageSize=20&apiKey=${this.apiKey}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`News API error: ${response.status}`);
      }

      const data: NewsApiResponse = await response.json();
      return this.transformNewsData(data.articles);
    } catch (error) {
      logger.error('Error fetching market news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  async getCryptoNews(): Promise<NewsItem[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/everything?q=bitcoin OR ethereum OR cryptocurrency OR crypto OR blockchain OR defi&language=en&sortBy=publishedAt&pageSize=15&apiKey=${this.apiKey}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`News API error: ${response.status}`);
      }

      const data: NewsApiResponse = await response.json();
      return this.transformNewsData(data.articles);
    } catch (error) {
      logger.error('Error fetching crypto news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  async getEarningsNews(): Promise<NewsItem[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/everything?q=earnings OR quarterly OR revenue OR profit OR Q4 OR Q3 OR financial results&language=en&sortBy=publishedAt&pageSize=15&apiKey=${this.apiKey}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`News API error: ${response.status}`);
      }

      const data: NewsApiResponse = await response.json();
      return this.transformNewsData(data.articles);
    } catch (error) {
      logger.error('Error fetching earnings news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  private transformNewsData(articles: NewsApiArticle[]): NewsItem[] {
    return articles.map((article, index) => ({
      id: `news-${index}`,
      title: article.title,
      source: article.source.name,
      timestamp: this.formatTimestamp(article.publishedAt),
      category: this.categorizeNews(article.title, article.description),
      stockSymbol: this.extractStockSymbol(article.title),
      stockChange: this.generateMockStockChange(),
      hasVideo: Math.random() > 0.7, // 30% chance of having video
      videoUrl: Math.random() > 0.7 ? this.getMockVideoUrl() : undefined,
      thumbnailUrl: article.urlToImage || this.getDefaultThumbnail(),
      content: article.description || article.content,
      readTime: this.calculateReadTime(article.content),
      isBreaking: this.isBreakingNews(article.publishedAt),
    }));
  }

  private formatTimestamp(publishedAt: string): string {
    const now = new Date();
    const published = new Date(publishedAt);
    const diffInMinutes = Math.floor((now.getTime() - published.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}m`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h`;
    } else {
      return `${Math.floor(diffInMinutes / 1440)}d`;
    }
  }

  private categorizeNews(title: string, description: string): 'market' | 'earnings' | 'tech' | 'crypto' | 'politics' {
    const text = (title + ' ' + description).toLowerCase();
    
    if (text.includes('earnings') || text.includes('quarterly') || text.includes('revenue')) {
      return 'earnings';
    } else if (text.includes('bitcoin') || text.includes('crypto') || text.includes('ethereum')) {
      return 'crypto';
    } else if (text.includes('apple') || text.includes('microsoft') || text.includes('tesla') || text.includes('tech')) {
      return 'tech';
    } else if (text.includes('fed') || text.includes('rate') || text.includes('inflation') || text.includes('economy')) {
      return 'market';
    } else {
      return 'market';
    }
  }

  private extractStockSymbol(title: string): string | undefined {
    const symbols = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BTC', 'ETH',
      'NFLX', 'ADBE', 'CRM', 'PYPL', 'UBER', 'LYFT', 'AMD', 'INTC', 'IBM',
      'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA', 'DIS', 'NKE', 'WMT', 'PG'
    ];
    const foundSymbol = symbols.find(symbol => title.toUpperCase().includes(symbol));
    return foundSymbol;
  }

  private generateMockStockChange(): number {
    return Math.random() * 10 - 5; // Random change between -5% and +5%
  }

  private getMockVideoUrl(): string {
    const videos = [
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4',
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4',
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_10mb.mp4',
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_20mb.mp4',
      'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_30mb.mp4',
    ];
    return videos[Math.floor(Math.random() * videos.length)];
  }

  private getDefaultThumbnail(): string {
    const thumbnails = [
      'https://via.placeholder.com/300x200/4ECDC4/FFFFFF?text=Finance',
      'https://via.placeholder.com/300x200/FF6B6B/FFFFFF?text=Market',
      'https://via.placeholder.com/300x200/FFEAA7/FFFFFF?text=Earnings',
      'https://via.placeholder.com/300x200/FFD700/FFFFFF?text=Crypto',
      'https://via.placeholder.com/300x200/A8E6CF/FFFFFF?text=Trading',
    ];
    return thumbnails[Math.floor(Math.random() * thumbnails.length)];
  }

  private calculateReadTime(content: string): string {
    const wordsPerMinute = 200;
    const wordCount = content.split(' ').length;
    const minutes = Math.ceil(wordCount / wordsPerMinute);
    return `${minutes} min read`;
  }

  private isBreakingNews(publishedAt: string): boolean {
    const published = new Date(publishedAt);
    const now = new Date();
    const diffInMinutes = (now.getTime() - published.getTime()) / (1000 * 60);
    return diffInMinutes < 30; // Breaking if published within last 30 minutes
  }

  private getMockNewsData(): NewsItem[] {
    return [
      {
        id: 'news-1',
        title: 'Federal Reserve Signals Potential Rate Cut in Q2',
        source: 'Reuters',
        timestamp: '30m',
        category: 'market',
        hasVideo: false,
        content: 'The Federal Reserve indicated it may consider interest rate cuts in the second quarter if inflation continues to moderate.',
        readTime: '2 min read',
        isBreaking: true,
      },
      {
        id: 'news-2',
        title: 'Apple Reports Strong Q4 Earnings Despite Market Headwinds',
        source: 'Bloomberg',
        timestamp: '2h',
        category: 'earnings',
        stockSymbol: 'AAPL',
        stockChange: 2.3,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/FF6B6B/FFFFFF?text=Apple+Earnings',
        content: 'Apple reported better-than-expected quarterly earnings with strong iPhone sales driving revenue growth.',
        readTime: '4 min read',
      },
      {
        id: 'news-3',
        title: 'Tesla Stock Surges on Cybertruck Production Update',
        source: 'CNBC',
        timestamp: '1h',
        category: 'earnings',
        stockSymbol: 'TSLA',
        stockChange: 5.7,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/333333/FFFFFF?text=Tesla+Update',
        content: 'Tesla shares jumped after the company announced accelerated Cybertruck production timelines.',
        readTime: '3 min read',
      },
      {
        id: 'news-4',
        title: 'Bitcoin Reaches New All-Time High Above $100K',
        source: 'CoinDesk',
        timestamp: '45m',
        category: 'crypto',
        stockSymbol: 'BTC',
        stockChange: 8.2,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/FFD700/FFFFFF?text=BTC+100K',
        content: 'Bitcoin reached a new milestone as institutional adoption continues to drive price appreciation.',
        readTime: '4 min read',
        isBreaking: true,
      },
      {
        id: 'news-5',
        title: 'Microsoft Azure Cloud Revenue Exceeds Expectations',
        source: 'TechCrunch',
        timestamp: '3h',
        category: 'earnings',
        stockSymbol: 'MSFT',
        stockChange: 3.1,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_10mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/0078D4/FFFFFF?text=Azure+Growth',
        content: 'Microsoft reported strong cloud revenue growth driven by enterprise adoption of Azure services.',
        readTime: '5 min read',
      },
    ];
  }

  private getMockCryptoNewsData(): NewsItem[] {
    return [
      {
        id: 'crypto-1',
        title: 'Bitcoin Surges Past $100K as Institutional Adoption Accelerates',
        source: 'CoinDesk',
        timestamp: '1h',
        category: 'crypto',
        stockSymbol: 'BTC',
        stockChange: 8.5,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/FFD700/FFFFFF?text=BTC+100K',
        content: 'Bitcoin reached a new all-time high above $100,000 as major corporations announce Bitcoin treasury allocations.',
        readTime: '3 min read',
      },
    ];
  }

  private getMockEarningsNewsData(): NewsItem[] {
    return [
      {
        id: 'earnings-1',
        title: 'Tesla Cybertruck Production Ramps Up Despite Supply Chain Challenges',
        source: 'TechCrunch',
        timestamp: '4h',
        category: 'earnings',
        stockSymbol: 'TSLA',
        stockChange: 3.2,
        hasVideo: true,
        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4',
        thumbnailUrl: 'https://via.placeholder.com/300x200/333333/FFFFFF?text=Cybertruck',
        content: 'Tesla has successfully ramped up Cybertruck production despite ongoing supply chain disruptions affecting the automotive industry.',
        readTime: '5 min read',
      },
    ];
  }
}

export default NewsService;
