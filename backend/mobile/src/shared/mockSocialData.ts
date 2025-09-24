// Mock data for social features demonstration
export const mockUsers = [
{
id: 'user-1',
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
id: 'portfolio-1',
name: 'Growth Portfolio',
description: 'Focused on long-term growth stocks',
isPublic: true,
totalValue: 45000,
totalReturn: 8500,
totalReturnPercent: 23.3,
positions: [
{
id: 'pos-1',
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
id: 'user-2',
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
id: 'portfolio-2',
name: 'Tech Growth',
description: 'High-growth technology investments',
isPublic: true,
totalValue: 125000,
totalReturn: 35000,
totalReturnPercent: 38.9,
positions: [
{
id: 'pos-2',
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
id: 'user-3',
name: 'Emily Rodriguez',
email: 'emily@example.com',
profilePic: null,
followersCount: 456,
followingCount: 78,
isFollowingUser: false,
isFollowedByUser: false,
createdAt: '2023-06-10T00:00:00Z',
experienceLevel: 'beginner',
riskTolerance: 'conservative',
investmentGoals: ['retirement', 'emergency'],
monthlyInvestment: 800,
portfolios: [
{
id: 'portfolio-3',
name: 'Safe & Steady',
description: 'Conservative investment approach',
isPublic: true,
totalValue: 12000,
totalReturn: 1200,
totalReturnPercent: 11.1,
positions: [
{
id: 'pos-3',
stock: { symbol: 'VTI', companyName: 'Vanguard Total Stock Market ETF' },
shares: 60,
currentPrice: 220.45,
totalValue: 13227,
returnPercent: 8.9
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
}
];
export const mockSocialPosts = [
{
id: 'post-1',
type: 'portfolio_update',
createdAt: '2024-01-15T10:30:00Z',
user: mockUsers[0],
content: 'Just rebalanced my portfolio after the recent market movements. Feeling confident about the tech sector recovery!',
portfolio: mockUsers[0].portfolios[0],
likesCount: 23,
commentsCount: 5,
isLiked: false,
comments: [
{
id: 'comment-1',
content: 'Great move! I\'ve been thinking about doing the same.',
createdAt: '2024-01-15T11:00:00Z',
user: mockUsers[1]
}
]
},
{
id: 'post-2',
type: 'stock_purchase',
createdAt: '2024-01-14T14:20:00Z',
user: mockUsers[1],
content: 'Added more TSLA to my portfolio. The recent dip was too good to pass up!',
stock: {
symbol: 'TSLA',
companyName: 'Tesla Inc.',
currentPrice: 245.30,
changePercent: 5.2
},
likesCount: 45,
commentsCount: 12,
isLiked: true,
comments: [
{
id: 'comment-2',
content: 'Bold move! What\'s your price target?',
createdAt: '2024-01-14T15:00:00Z',
user: mockUsers[0]
}
]
},
{
id: 'post-3',
type: 'learning_complete',
createdAt: '2024-01-13T16:45:00Z',
user: mockUsers[2],
content: 'Completed the "Understanding Risk" module! Feeling much more confident about my investment strategy.',
likesCount: 18,
commentsCount: 3,
isLiked: false,
comments: []
}
];
export const mockDiscoverUsers = mockUsers.map(user => ({
...user,
// Add some additional discover-specific data
lastActive: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
publicPortfolioCount: user.portfolios.filter(p => p.isPublic).length,
averageReturn: user.portfolios.reduce((acc, p) => acc + p.totalReturnPercent, 0) / user.portfolios.length
}));
