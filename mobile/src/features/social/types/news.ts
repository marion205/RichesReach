export interface NewsItem {
  id: string;
  title: string;
  source: string;
  timestamp: string;
  category: 'market' | 'earnings' | 'tech' | 'crypto' | 'politics';
  stockSymbol?: string;
  stockChange?: number;
  hasVideo: boolean;
  videoUrl?: string;
  thumbnailUrl?: string;
  content: string;
  readTime: string;
  isBreaking?: boolean;
}

export interface NewsCategory {
  key: string;
  label: string;
  icon: string;
}

export interface NewsApiResponse {
  articles: NewsApiArticle[];
  totalResults: number;
  status: string;
}

export interface NewsApiArticle {
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
