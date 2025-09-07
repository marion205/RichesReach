// Mock User Service for testing social features
export interface MockUser {
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
  portfolios: MockPortfolio[];
  stats: {
    totalLearningTime: number;
    modulesCompleted: number;
    achievements: string[];
    streakDays: number;
  };
}

export interface MockPortfolio {
  id: string;
  name: string;
  description: string;
  isPublic: boolean;
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  positions: MockPosition[];
}

export interface MockPosition {
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

class MockUserService {
  private static instance: MockUserService;
  private currentUserId = 'current-user-123';
  private users: MockUser[] = [];

  private constructor() {
    this.initializeMockUsers();
  }

  public static getInstance(): MockUserService {
    if (!MockUserService.instance) {
      MockUserService.instance = new MockUserService();
    }
    return MockUserService.instance;
  }

  private initializeMockUsers() {
    // Create the test user you requested
    const testUser: MockUser = {
      id: 'test-user-456',
      name: 'Test Investor',
      email: 'test@example.com',
      profilePic: null,
      followersCount: 89,
      followingCount: 156,
      isFollowingUser: false,
      isFollowedByUser: true, // Current user follows this test user
      createdAt: '2023-03-15T00:00:00Z',
      experienceLevel: 'intermediate',
      riskTolerance: 'moderate',
      investmentGoals: ['retirement', 'wealth', 'passive'],
      monthlyInvestment: 2500,
      portfolios: [
        {
          id: 'portfolio-test-1',
          name: 'Balanced Growth',
          description: 'A well-diversified portfolio focused on steady growth',
          isPublic: true,
          totalValue: 67500,
          totalReturn: 12500,
          totalReturnPercent: 22.7,
          positions: [
            {
              id: 'pos-test-1',
              stock: { symbol: 'AAPL', companyName: 'Apple Inc.' },
              shares: 100,
              currentPrice: 175.50,
              totalValue: 17550,
              returnPercent: 18.5
            },
            {
              id: 'pos-test-2',
              stock: { symbol: 'MSFT', companyName: 'Microsoft Corporation' },
              shares: 80,
              currentPrice: 380.25,
              totalValue: 30420,
              returnPercent: 25.2
            },
            {
              id: 'pos-test-3',
              stock: { symbol: 'VTI', companyName: 'Vanguard Total Stock Market ETF' },
              shares: 120,
              currentPrice: 220.45,
              totalValue: 26454,
              returnPercent: 12.8
            }
          ]
        },
        {
          id: 'portfolio-test-2',
          name: 'Tech Focus',
          description: 'High-growth technology investments',
          isPublic: true,
          totalValue: 32000,
          totalReturn: 8500,
          totalReturnPercent: 36.1,
          positions: [
            {
              id: 'pos-test-4',
              stock: { symbol: 'TSLA', companyName: 'Tesla Inc.' },
              shares: 50,
              currentPrice: 245.30,
              totalValue: 12265,
              returnPercent: 42.3
            },
            {
              id: 'pos-test-5',
              stock: { symbol: 'NVDA', companyName: 'NVIDIA Corporation' },
              shares: 30,
              currentPrice: 485.20,
              totalValue: 14556,
              returnPercent: 38.7
            }
          ]
        }
      ],
      stats: {
        totalLearningTime: 320,
        modulesCompleted: 12,
        achievements: ['diversification-master', 'tech-investor', 'consistent-saver'],
        streakDays: 18
      }
    };

    // Create current user profile
    const currentUser: MockUser = {
      id: this.currentUserId,
      name: 'You',
      email: 'you@example.com',
      profilePic: null,
      followersCount: 45,
      followingCount: 23,
      isFollowingUser: true, // This user follows the test user
      isFollowedByUser: false,
      createdAt: '2023-01-10T00:00:00Z',
      experienceLevel: 'beginner',
      riskTolerance: 'conservative',
      investmentGoals: ['retirement', 'emergency'],
      monthlyInvestment: 1000,
      portfolios: [
        {
          id: 'portfolio-current-1',
          name: 'My First Portfolio',
          description: 'Learning the basics of investing',
          isPublic: true,
          totalValue: 14303.52,
          totalReturn: 2145.53,
          totalReturnPercent: 17.65,
          positions: [
            {
              id: 'pos-current-1',
              stock: { symbol: 'VTI', companyName: 'Vanguard Total Stock Market ETF' },
              shares: 50,
              currentPrice: 220.45,
              totalValue: 11022.50,
              returnPercent: 15.2
            }
          ]
        }
      ],
      stats: {
        totalLearningTime: 95,
        modulesCompleted: 4,
        achievements: ['first-investment'],
        streakDays: 7
      }
    };

    // Add some additional mock users for variety
    const additionalUsers: MockUser[] = [
      {
        id: 'user-sarah-789',
        name: 'Sarah Johnson',
        email: 'sarah@example.com',
        profilePic: null,
        followersCount: 1247,
        followingCount: 89,
        isFollowingUser: false,
        isFollowedByUser: false,
        createdAt: '2023-01-15T00:00:00Z',
        experienceLevel: 'intermediate',
        riskTolerance: 'moderate',
        investmentGoals: ['retirement', 'house', 'wealth'],
        monthlyInvestment: 2000,
        portfolios: [
          {
            id: 'portfolio-sarah-1',
            name: 'Growth Portfolio',
            description: 'Focused on long-term growth stocks',
            isPublic: true,
            totalValue: 45000,
            totalReturn: 8500,
            totalReturnPercent: 23.3,
            positions: [
              {
                id: 'pos-sarah-1',
                stock: { symbol: 'AAPL', companyName: 'Apple Inc.' },
                shares: 50,
                currentPrice: 175.50,
                totalValue: 8775,
                returnPercent: 15.2
              }
            ]
          }
        ],
        stats: {
          totalLearningTime: 180,
          modulesCompleted: 8,
          achievements: ['first-investment', 'diversification-master'],
          streakDays: 12
        }
      },
      {
        id: 'user-mike-101',
        name: 'Mike Chen',
        email: 'mike@example.com',
        profilePic: null,
        followersCount: 892,
        followingCount: 156,
        isFollowingUser: true,
        isFollowedByUser: false,
        createdAt: '2022-08-20T00:00:00Z',
        experienceLevel: 'advanced',
        riskTolerance: 'aggressive',
        investmentGoals: ['wealth', 'passive'],
        monthlyInvestment: 5000,
        portfolios: [
          {
            id: 'portfolio-mike-1',
            name: 'Tech Growth',
            description: 'High-growth technology investments',
            isPublic: true,
            totalValue: 125000,
            totalReturn: 35000,
            totalReturnPercent: 38.9,
            positions: [
              {
                id: 'pos-mike-1',
                stock: { symbol: 'TSLA', companyName: 'Tesla Inc.' },
                shares: 100,
                currentPrice: 245.30,
                totalValue: 24530,
                returnPercent: 45.7
              }
            ]
          }
        ],
        stats: {
          totalLearningTime: 420,
          modulesCompleted: 15,
          achievements: ['advanced-trader', 'portfolio-optimizer'],
          streakDays: 28
        }
      },
      {
        id: 'user-alex-202',
        name: 'Alex Rodriguez',
        email: 'alex.rodriguez@example.com',
        profilePic: null,
        followersCount: 567,
        followingCount: 234,
        isFollowingUser: false,
        isFollowedByUser: false,
        createdAt: '2023-05-10T00:00:00Z',
        experienceLevel: 'beginner',
        riskTolerance: 'conservative',
        investmentGoals: ['retirement', 'emergency'],
        monthlyInvestment: 1200,
        portfolios: [
          {
            id: 'portfolio-alex-1',
            name: 'Conservative Growth',
            description: 'Low-risk, steady growth investments',
            isPublic: true,
            totalValue: 18500,
            totalReturn: 2100,
            totalReturnPercent: 12.8,
            positions: [
              {
                id: 'pos-alex-1',
                stock: { symbol: 'VTI', companyName: 'Vanguard Total Stock Market ETF' },
                shares: 80,
                currentPrice: 220.45,
                totalValue: 17636,
                returnPercent: 10.5
              }
            ]
          }
        ],
        stats: {
          totalLearningTime: 95,
          modulesCompleted: 4,
          achievements: ['first-steps'],
          streakDays: 7
        }
      },
      {
        id: 'user-jessica-303',
        name: 'Jessica Wang',
        email: 'jessica.wang@example.com',
        profilePic: null,
        followersCount: 2103,
        followingCount: 89,
        isFollowingUser: false,
        isFollowedByUser: false,
        createdAt: '2022-12-01T00:00:00Z',
        experienceLevel: 'advanced',
        riskTolerance: 'aggressive',
        investmentGoals: ['wealth', 'passive', 'retirement'],
        monthlyInvestment: 8000,
        portfolios: [
          {
            id: 'portfolio-jessica-1',
            name: 'Aggressive Growth',
            description: 'High-risk, high-reward investments',
            isPublic: true,
            totalValue: 185000,
            totalReturn: 45000,
            totalReturnPercent: 32.1,
            positions: [
              {
                id: 'pos-jessica-1',
                stock: { symbol: 'NVDA', companyName: 'NVIDIA Corporation' },
                shares: 200,
                currentPrice: 485.20,
                totalValue: 97040,
                returnPercent: 45.2
              }
            ]
          }
        ],
        stats: {
          totalLearningTime: 650,
          modulesCompleted: 18,
          achievements: ['advanced-trader', 'portfolio-optimizer', 'market-expert'],
          streakDays: 45
        }
      }
    ];

    this.users = [testUser, currentUser, ...additionalUsers];
  }

  // Get all users for discovery
  public getDiscoverUsers(limit: number = 20, offset: number = 0, searchTerm?: string, experienceLevel?: string, sortBy: string = 'followers'): MockUser[] {
    let filteredUsers = this.users.filter(user => user.id !== this.currentUserId);

    // Apply search filter
    if (searchTerm && searchTerm.trim()) {
      const search = searchTerm.toLowerCase().trim();
      filteredUsers = filteredUsers.filter(user => {
        const nameMatch = user.name.toLowerCase().includes(search);
        const emailMatch = user.email.toLowerCase().includes(search);
        return nameMatch || emailMatch;
      });
    }

    // Apply experience level filter
    if (experienceLevel) {
      filteredUsers = filteredUsers.filter(user => user.experienceLevel === experienceLevel);
    }

    // Apply sorting
    switch (sortBy) {
      case 'followers':
        filteredUsers.sort((a, b) => b.followersCount - a.followersCount);
        break;
      case 'recent':
        filteredUsers.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case 'performance':
        filteredUsers.sort((a, b) => {
          const aAvgReturn = a.portfolios.reduce((sum, p) => sum + p.totalReturnPercent, 0) / a.portfolios.length;
          const bAvgReturn = b.portfolios.reduce((sum, p) => sum + p.totalReturnPercent, 0) / b.portfolios.length;
          return bAvgReturn - aAvgReturn;
        });
        break;
      case 'activity':
        filteredUsers.sort((a, b) => b.stats.modulesCompleted - a.stats.modulesCompleted);
        break;
    }

    return filteredUsers.slice(offset, offset + limit);
  }

  // Get a specific user by ID
  public getUserById(userId: string): MockUser | null {
    return this.users.find(user => user.id === userId) || null;
  }

  // Get current user
  public getCurrentUser(): MockUser | null {
    return this.users.find(user => user.id === this.currentUserId) || null;
  }

  // Toggle follow status
  public toggleFollow(userId: string): { success: boolean; message: string } {
    const user = this.users.find(u => u.id === userId);
    const currentUser = this.getCurrentUser();

    if (!user || !currentUser) {
      return { success: false, message: 'User not found' };
    }

    if (user.isFollowingUser) {
      // Unfollow
      user.isFollowingUser = false;
      user.followersCount = Math.max(0, user.followersCount - 1);
      currentUser.followingCount = Math.max(0, currentUser.followingCount - 1);
      return { success: true, message: 'Unfollowed successfully' };
    } else {
      // Follow
      user.isFollowingUser = true;
      user.followersCount += 1;
      currentUser.followingCount += 1;
      return { success: true, message: 'Followed successfully' };
    }
  }

  // Get users that current user follows
  public getFollowingUsers(): MockUser[] {
    return this.users.filter(user => user.isFollowingUser && user.id !== this.currentUserId);
  }

  // Get users that follow current user
  public getFollowers(): MockUser[] {
    return this.users.filter(user => user.isFollowedByUser && user.id !== this.currentUserId);
  }

  // Get social feed posts
  public getSocialFeedPosts(): any[] {
    const followingUsers = this.getFollowingUsers();
    const posts: any[] = [];

    // Generate some mock posts from followed users
    followingUsers.forEach(user => {
      if (user.portfolios.length > 0) {
        posts.push({
          id: `post-${user.id}-1`,
          type: 'portfolio_update',
          createdAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
          user: user,
          content: `Just updated my ${user.portfolios[0].name}. Feeling confident about the market direction!`,
          portfolio: user.portfolios[0],
          likesCount: Math.floor(Math.random() * 50) + 5,
          commentsCount: Math.floor(Math.random() * 20) + 1,
          isLiked: Math.random() > 0.5,
          comments: []
        });
      }
    });

    return posts.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }
}

export default MockUserService;
