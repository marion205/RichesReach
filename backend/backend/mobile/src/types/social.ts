// Social feature types for production
export interface User {
  id: string;
  name: string;
  email: string;
  profilePic?: string | null;
  followersCount: number;
  followingCount: number;
  isFollowingUser: boolean;
  isFollowedByUser: boolean;
  createdAt: string;
  experienceLevel: 'beginner' | 'intermediate' | 'advanced';
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  investmentGoals: string[];
  monthlyInvestment: number;
  portfolios: Portfolio[];
  stats: {
    totalLearningTime: number;
    modulesCompleted: number;
    achievements: string[];
    streakDays: number;
  };
}

export interface Portfolio {
  id: string;
  name: string;
  description: string;
  isPublic: boolean;
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  positions: Position[];
}

export interface Position {
  id: string;
  stock: {
    symbol: string;
    companyName: string;
  };
  shares: number;
  currentPrice: number;
  totalValue: number;
  returnPercent: number;
}

export interface SocialPost {
  id: string;
  type: 'portfolio_update' | 'stock_purchase' | 'learning_complete';
  createdAt: string;
  user: User;
  content: string;
  portfolio?: Portfolio;
  stock?: {
    symbol: string;
    companyName: string;
    currentPrice: number;
    changePercent: number;
  };
  likesCount: number;
  commentsCount: number;
  isLiked: boolean;
  comments: Comment[];
}

export interface Comment {
  id: string;
  content: string;
  createdAt: string;
  user: User;
}
