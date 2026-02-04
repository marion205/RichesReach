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
    this.apiKey = process.env.EXPO_PUBLIC_NEWS_API_KEY || '';
    if (!this.apiKey) {
      logger.warn('News API key missing. Set EXPO_PUBLIC_NEWS_API_KEY to enable live news.');
    }
  }

  async getFinancialNews(category: string = 'business', pageSize: number = 20): Promise<NewsItem[]> {
    try {
      if (!this.apiKey) {
        return [];
      }
      const query = `${category} OR finance OR stocks OR investing OR market OR earnings OR trading`;
      const response = await fetch(
        `${this.baseUrl}/everything?q=${encodeURIComponent(query)}&language=en&sortBy=publishedAt&pageSize=${pageSize}&apiKey=${this.apiKey}`,
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
      if (!this.apiKey) {
        return [];
      }
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
      return this.transformNewsData(data?.articles ?? []);
    } catch (error) {
      logger.error('Error fetching market news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  async getCryptoNews(): Promise<NewsItem[]> {
    try {
      if (!this.apiKey) {
        return [];
      }
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
      return this.transformNewsData(data?.articles ?? []);
    } catch (error) {
      logger.error('Error fetching crypto news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  async getEarningsNews(): Promise<NewsItem[]> {
    try {
      if (!this.apiKey) {
        return [];
      }
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
      return this.transformNewsData(data?.articles ?? []);
    } catch (error) {
      logger.error('Error fetching earnings news:', error);
      // Return empty array instead of mock data
      return [];
    }
  }

  private transformNewsData(articles: NewsApiArticle[]): NewsItem[] {
    if (!articles || !Array.isArray(articles)) return [];
    return articles.map((article, index) => ({
      id: `news-${index}`,
      title: article?.title ?? '',
      source: article?.source?.name ?? 'Unknown',
      timestamp: this.formatTimestamp(article?.publishedAt ?? new Date().toISOString()),
      category: this.categorizeNews(article?.title ?? '', article?.description ?? ''),
      stockSymbol: this.extractStockSymbol(article?.title ?? ''),
      stockChange: this.generateMockStockChange(),
      hasVideo: Math.random() > 0.7, // 30% chance of having video
      videoUrl: Math.random() > 0.7 ? this.getMockVideoUrl() : undefined,
      thumbnailUrl: article?.urlToImage || this.getDefaultThumbnail(),
      content: (article?.description || article?.content) ?? '',
      readTime: this.calculateReadTime(article?.content ?? article?.description ?? ''),
      isBreaking: this.isBreakingNews(article?.publishedAt ?? new Date().toISOString()),
    }));
  }

  private formatTimestamp(publishedAt: string | null | undefined): string {
    const now = new Date();
    const published = new Date(publishedAt ?? now);
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
    const text = ((title ?? '') + ' ' + (description ?? '')).toLowerCase();
    
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

  private extractStockSymbol(title: string | null | undefined): string | undefined {
    const text = title ?? '';
    const symbols = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BTC', 'ETH',
      'NFLX', 'ADBE', 'CRM', 'PYPL', 'UBER', 'LYFT', 'AMD', 'INTC', 'IBM',
      'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA', 'DIS', 'NKE', 'WMT', 'PG'
    ];
    const foundSymbol = symbols.find(symbol => text.toUpperCase().includes(symbol));
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

  private calculateReadTime(content: string | null | undefined): string {
    const wordsPerMinute = 200;
    const text = content ?? '';
    const wordCount = text.trim() ? text.split(/\s+/).length : 0;
    const minutes = Math.max(1, Math.ceil(wordCount / wordsPerMinute));
    return `${minutes} min read`;
  }

  private isBreakingNews(publishedAt: string | null | undefined): boolean {
    const published = new Date(publishedAt ?? 0);
    const now = new Date();
    const diffInMinutes = (now.getTime() - published.getTime()) / (1000 * 60);
    return diffInMinutes < 30; // Breaking if published within last 30 minutes
  }
}

export default NewsService;
