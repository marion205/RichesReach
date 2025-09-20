// Learning Paths Data Structure for Beginner Education
export interface LearningModule {
id: string;
title: string;
description: string;
icon: string;
color: string;
duration: string; // e.g., "5 min read"
difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
completed: boolean;
locked: boolean;
content: {
sections: LearningSection[];
};
}
export interface LearningSection {
id: string;
title: string;
type: 'text' | 'interactive' | 'quiz' | 'video' | 'example';
content: string;
interactiveData?: any;
quizData?: QuizQuestion[];
exampleData?: ExampleData;
}
export interface QuizQuestion {
id: string;
question: string;
options: string[];
correctAnswer: number;
explanation: string;
}
export interface ExampleData {
title: string;
scenario: string;
calculation: string;
result: string;
explanation: string;
}
// Learning Paths
export const LEARNING_PATHS = {
GETTING_STARTED: {
id: 'getting-started',
title: 'Getting Started with Investing',
description: 'Learn the basics of investing and how to build your first portfolio',
icon: 'play-circle',
color: '#34C759',
totalModules: 6,
estimatedTime: '35 minutes',
modules: [
{
id: 'what-is-investing',
title: 'What is Investing?',
description: 'Understanding the basics of investing and why it matters',
icon: 'trending-up',
color: '#34C759',
duration: '5 min read',
difficulty: 'Beginner' as const,
completed: false,
locked: false,
content: {
sections: [
{
id: 'intro',
title: 'Introduction to Investing',
type: 'text' as const,
content: `Investing is the process of putting your money to work to generate returns over time. Think of it as planting seeds that grow into trees - your money grows and compounds over the years.
**Why Invest?**
- Beat inflation: Keep your money's purchasing power
- Build wealth: Grow your money over time
- Achieve goals: Save for retirement, house, education
- Financial freedom: Create passive income streams
**Key Concepts:**
- **Compound Interest**: Your money earns money on the money it already earned
- **Risk vs Return**: Higher potential returns usually come with higher risk
- **Diversification**: Don't put all your eggs in one basket
- **Time Horizon**: How long you plan to invest affects your strategy`
},
{
id: 'quiz-1',
title: 'Quick Check',
type: 'quiz' as const,
content: 'Test your understanding of investing basics',
quizData: [
{
id: 'q1',
question: 'What is the main benefit of compound interest?',
options: [
'It makes your money grow faster over time',
'It reduces your taxes',
'It protects against inflation',
'It guarantees returns'
],
correctAnswer: 0,
explanation: 'Compound interest means your money earns money on the money it already earned, creating exponential growth over time.'
},
{
id: 'q2',
question: 'What does diversification mean?',
options: [
'Putting all your money in one stock',
'Spreading your money across different investments',
'Only investing in safe options',
'Investing for a short time'
],
correctAnswer: 1,
explanation: 'Diversification means spreading your money across different types of investments to reduce risk.'
}
]
}
]
}
},
{
id: 'types-of-investments',
title: 'Types of Investments',
description: 'Learn about stocks, bonds, ETFs, and other investment options',
icon: 'layers',
color: '#007AFF',
duration: '6 min read',
difficulty: 'Beginner' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'stocks',
title: 'Stocks (Equities)',
type: 'text' as const,
content: `**What are Stocks?**
Stocks represent ownership in a company. When you buy a stock, you own a small piece of that company.
**How Stocks Work:**
- You buy shares at a certain price
- If the company does well, the stock price goes up
- You can sell for a profit or hold for dividends
- If the company struggles, the stock price may go down
**Types of Stocks:**
- **Growth Stocks**: Companies expected to grow quickly (higher risk, higher potential return)
- **Value Stocks**: Companies trading below their true worth (potential for good returns)
- **Dividend Stocks**: Companies that pay regular dividends (steady income)
- **Blue Chip Stocks**: Large, established companies (lower risk, steady growth)`
},
{
id: 'bonds',
title: 'Bonds',
type: 'text' as const,
content: `**What are Bonds?**
Bonds are loans you make to companies or governments. They pay you interest and return your principal.
**How Bonds Work:**
- You lend money to a borrower (company/government)
- They pay you interest regularly
- At maturity, you get your original money back
- Generally safer than stocks but lower returns
**Types of Bonds:**
- **Government Bonds**: Loans to the government (very safe)
- **Corporate Bonds**: Loans to companies (higher risk, higher return)
- **Municipal Bonds**: Loans to local governments (tax advantages)`
},
{
id: 'etfs',
title: 'ETFs (Exchange-Traded Funds)',
type: 'text' as const,
content: `**What are ETFs?**
ETFs are funds that track a group of stocks, bonds, or other assets. They trade like stocks but give you instant diversification.
**Benefits of ETFs:**
- **Diversification**: Own hundreds of stocks with one purchase
- **Low Cost**: Lower fees than mutual funds
- **Easy Trading**: Buy and sell like stocks
- **Transparency**: You know exactly what you own
**Popular ETF Types:**
- **S&P 500 ETFs**: Track the 500 largest US companies
- **Total Market ETFs**: Track the entire stock market
- **Sector ETFs**: Focus on specific industries
- **International ETFs**: Invest in foreign markets`
}
]
}
},
{
id: 'building-portfolio',
title: 'Building Your First Portfolio',
description: 'Learn how to create a balanced portfolio that matches your goals',
icon: 'pie-chart',
color: '#FF9500',
duration: '7 min read',
difficulty: 'Beginner' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'asset-allocation',
title: 'Asset Allocation Basics',
type: 'text' as const,
content: `**What is Asset Allocation?**
Asset allocation is how you divide your money between different types of investments.
**The 100-Age Rule:**
- Take your age and subtract it from 100
- That's the percentage you should have in stocks
- The rest goes in bonds and cash
- Example: If you're 25, put 75% in stocks, 25% in bonds
**Age-Based Guidelines:**
- **20s-30s**: 80-90% stocks, 10-20% bonds (aggressive growth)
- **40s-50s**: 60-70% stocks, 30-40% bonds (balanced)
- **60s+**: 40-50% stocks, 50-60% bonds (conservative)`
},
{
id: 'diversification',
title: 'Diversification Strategies',
type: 'text' as const,
content: `**Why Diversify?**
Diversification reduces risk by spreading your money across different investments.
**Diversification Methods:**
1. **By Asset Type**: Stocks, bonds, real estate, commodities
2. **By Geography**: US, international, emerging markets
3. **By Sector**: Technology, healthcare, finance, energy
4. **By Company Size**: Large-cap, mid-cap, small-cap
**Simple Diversification:**
- **Beginner**: 60% US stocks, 20% international stocks, 20% bonds
- **Conservative**: 40% US stocks, 20% international stocks, 40% bonds
- **Aggressive**: 70% US stocks, 20% international stocks, 10% bonds`
},
{
id: 'example',
title: 'Portfolio Example',
type: 'example' as const,
content: 'See how a real portfolio might look',
exampleData: {
title: 'Sarah\'s $10,000 Portfolio (Age 25)',
scenario: 'Sarah is 25 years old and wants to start investing with $10,000. She has a long time horizon and can handle some risk.',
calculation: 'Using the 100-age rule: 100 - 25 = 75% stocks, 25% bonds',
result: `
- **US Stocks (60%)**: $6,000 in S&P 500 ETF
- **International Stocks (15%)**: $1,500 in International ETF 
- **Bonds (25%)**: $2,500 in Bond ETF
**Expected Annual Return**: 7-9%
**Risk Level**: Moderate
**Time Horizon**: 30+ years`,
explanation: 'This portfolio gives Sarah good growth potential while maintaining some stability through bonds. As she gets older, she can gradually shift more money to bonds.'
}
}
]
}
},
{
id: 'risk-management',
title: 'Understanding Risk',
description: 'Learn about different types of risk and how to manage them',
icon: 'shield',
color: '#FF3B30',
duration: '4 min read',
difficulty: 'Beginner' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'types-of-risk',
title: 'Types of Investment Risk',
type: 'text' as const,
content: `**Market Risk**
The risk that the entire market will go down. This affects all stocks to some degree.
**Company Risk**
The risk that a specific company will fail or perform poorly. This is why diversification helps.
**Inflation Risk**
The risk that inflation will erode your purchasing power over time.
**Interest Rate Risk**
The risk that rising interest rates will hurt bond prices.
**Liquidity Risk**
The risk that you won't be able to sell your investment when you need to.`
},
{
id: 'risk-tolerance',
title: 'Assessing Your Risk Tolerance',
type: 'interactive' as const,
content: 'Take a quick assessment to understand your risk tolerance',
interactiveData: {
type: 'risk-assessment',
questions: [
{
question: 'If your portfolio dropped 20% in one month, what would you do?',
options: [
'Sell everything immediately',
'Sell some investments',
'Hold and wait',
'Buy more while prices are low'
],
scores: [1, 2, 3, 4]
},
{
question: 'What\'s your investment time horizon?',
options: [
'Less than 1 year',
'1-3 years',
'3-10 years',
'More than 10 years'
],
scores: [1, 2, 3, 4]
}
]
}
}
]
}
},
{
id: 'getting-started-action',
title: 'Your First Investment',
description: 'Step-by-step guide to making your first investment',
icon: 'target',
color: '#AF52DE',
duration: '3 min read',
difficulty: 'Beginner' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'steps',
title: 'Steps to Your First Investment',
type: 'text' as const,
content: `**Step 1: Set Your Goals**
- What are you investing for? (retirement, house, education)
- How much can you invest monthly?
- What's your time horizon?
**Step 2: Choose Your Platform**
- **Robo-advisors**: Automated investing (Betterment, Wealthfront)
- **Brokerage apps**: DIY investing (Robinhood, E*TRADE)
- **Employer 401(k)**: If available, start here first
**Step 3: Start Small**
- Begin with $100-500
- Use dollar-cost averaging (invest regularly)
- Don't try to time the market
**Step 4: Choose Your Investments**
- **Beginner**: Start with a total market ETF
- **Conservative**: 60% stocks, 40% bonds
- **Aggressive**: 80% stocks, 20% bonds
**Step 5: Monitor and Adjust**
- Check quarterly, not daily
- Rebalance annually
- Increase contributions over time`
}
]
}
}
]
},
PORTFOLIO_MANAGEMENT: {
id: 'portfolio-management',
title: 'Portfolio Management',
description: 'Learn how to manage and optimize your investment portfolio',
icon: 'bar-chart-2',
color: '#007AFF',
totalModules: 4,
estimatedTime: '20 minutes',
modules: [
{
id: 'rebalancing',
title: 'Portfolio Rebalancing',
description: 'Learn when and how to rebalance your portfolio',
icon: 'refresh-cw',
color: '#007AFF',
duration: '5 min read',
difficulty: 'Intermediate' as const,
completed: false,
locked: false,
content: {
sections: [
{
id: 'what-is-rebalancing',
title: 'What is Rebalancing?',
type: 'text' as const,
content: `**Rebalancing** is the process of adjusting your portfolio back to your target asset allocation.
**Why Rebalance?**
- Markets move, changing your allocation
- Maintains your risk level
- Forces you to "buy low, sell high"
- Keeps you on track with your goals
**When to Rebalance:**
- **Time-based**: Quarterly or annually
- **Threshold-based**: When allocation drifts 5-10%
- **Life changes**: New goals, risk tolerance changes
**How to Rebalance:**
1. Check your current allocation
2. Compare to your target allocation
3. Sell overweight assets
4. Buy underweight assets
5. Use new money to rebalance when possible`
}
]
}
},
{
id: 'options-trading',
title: 'Options Trading',
description: 'Master options strategies and advanced trading techniques',
icon: 'trending-up',
color: '#00cc99',
duration: '30 min read',
difficulty: 'Advanced' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'options-basics',
title: 'Options Basics',
type: 'text' as const,
content: `**Options** are financial derivatives that give you the right, but not the obligation, to buy or sell an asset at a specific price.

**Key Terms:**
- **Call Option**: Right to buy at strike price
- **Put Option**: Right to sell at strike price  
- **Strike Price**: Price at which you can exercise
- **Expiration Date**: When the option expires
- **Premium**: Cost to buy the option

**Why Trade Options?**
- Leverage: Control more shares with less money
- Hedging: Protect your portfolio from losses
- Income: Generate cash flow by selling options
- Flexibility: Profit in any market direction`
}
]
}
},
{
id: 'sbloc-guide',
title: 'SBLOC Guide',
description: 'Securities-based line of credit for advanced investors',
icon: 'credit-card',
color: '#8B5CF6',
duration: '25 min read',
difficulty: 'Advanced' as const,
completed: false,
locked: true,
content: {
sections: [
{
id: 'sbloc-basics',
title: 'SBLOC Basics',
type: 'text' as const,
content: `**SBLOC** (Securities-Based Line of Credit) lets you borrow against your investment portfolio.

**Key Benefits:**
- Access liquidity without selling investments
- Competitive interest rates
- No fixed repayment schedule
- Maintain portfolio control

**How It Works:**
1. Pledge eligible securities as collateral
2. Borrow up to 50-70% of portfolio value
3. Pay interest only on amount borrowed
4. Repay when convenient

**Important Considerations:**
- Margin calls if portfolio value drops
- Variable interest rates
- Not for purchasing more securities
- Risk of forced liquidation`
}
]
}
}
]
},
PORTFOLIO_MANAGEMENT: {
id: 'portfolio-management',
title: 'Portfolio Management',
description: 'Learn how to manage and optimize your investment portfolio',
icon: 'bar-chart-2',
color: '#007AFF',
totalModules: 4,
estimatedTime: '20 minutes',
modules: [
{
id: 'rebalancing',
title: 'Portfolio Rebalancing',
description: 'Learn when and how to rebalance your portfolio',
icon: 'refresh-cw',
color: '#007AFF',
duration: '5 min read',
difficulty: 'Intermediate' as const,
completed: false,
locked: false,
content: {
sections: [
{
id: 'what-is-rebalancing',
title: 'What is Rebalancing?',
type: 'text' as const,
content: `**Rebalancing** is the process of adjusting your portfolio back to your target asset allocation.
**Why Rebalance?**
- Markets move, changing your allocation
- Maintains your risk level
- Forces you to "buy low, sell high"
- Keeps you on track with your goals
**When to Rebalance:**
- **Time-based**: Quarterly or annually
- **Threshold-based**: When allocation drifts 5-10%
- **Life changes**: New goals, risk tolerance changes
**How to Rebalance:**
1. Check your current allocation
2. Compare to your target allocation
3. Sell overweight assets
4. Buy underweight assets
5. Use new money to rebalance when possible`
}
]
}
}
]
}
};
// Helper functions
export const getLearningPath = (pathId: string) => {
return Object.values(LEARNING_PATHS).find(path => path.id === pathId);
};
export const getModule = (pathId: string, moduleId: string) => {
const path = getLearningPath(pathId);
return path?.modules.find(module => module.id === moduleId);
};
export const getNextModule = (pathId: string, currentModuleId: string) => {
const path = getLearningPath(pathId);
if (!path) return null;
const currentIndex = path.modules.findIndex(module => module.id === currentModuleId);
if (currentIndex === -1 || currentIndex === path.modules.length - 1) return null;
return path.modules[currentIndex + 1];
};
export const unlockNextModule = (pathId: string, completedModuleId: string) => {
const path = getLearningPath(pathId);
if (!path) return;
const nextModule = getNextModule(pathId, completedModuleId);
if (nextModule) {
nextModule.locked = false;
}
};
