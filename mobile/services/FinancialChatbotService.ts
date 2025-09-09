import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

// GraphQL query for getting stock recommendations
const GET_STOCK_RECOMMENDATIONS = gql`
  query GetStockRecommendations($riskTolerance: String, $investmentAmount: Float, $timeHorizon: String) {
    stockRecommendations(riskTolerance: $riskTolerance, investmentAmount: $investmentAmount, timeHorizon: $timeHorizon) {
      symbol
      companyName
      currentPrice
      targetPrice
      recommendation
      riskLevel
      expectedReturn
      sector
      reason
    }
  }
`;

interface StockRecommendation {
  symbol: string;
  companyName: string;
  currentPrice: number;
  targetPrice: number;
  recommendation: string;
  riskLevel: string;
  expectedReturn: number;
  sector: string;
  reason: string;
}

interface InvestmentContext {
  amount: number;
  timeHorizon: string;
  goal: string;
  riskTolerance: 'low' | 'medium' | 'high';
}

class FinancialChatbotService {
  private static instance: FinancialChatbotService;

  public static getInstance(): FinancialChatbotService {
    if (!FinancialChatbotService.instance) {
      FinancialChatbotService.instance = new FinancialChatbotService();
    }
    return FinancialChatbotService.instance;
  }

  /**
   * Check if the user's question is financial-related
   */
  public isFinancialQuestion(userInput: string): boolean {
    const input = userInput.toLowerCase();
    
    // Financial keywords
    const financialKeywords = [
      'invest', 'investment', 'stock', 'stocks', 'etf', 'mutual fund', 'bond', 'bonds',
      'portfolio', 'diversify', 'diversification', 'risk', 'return', 'profit', 'loss',
      'market', 'trading', 'buy', 'sell', 'hold', 'dividend', 'yield', 'volatility',
      'retirement', 'ira', '401k', 'roth', 'traditional', 'pension', 'annuity',
      'budget', 'budgeting', 'save', 'saving', 'debt', 'credit', 'loan', 'mortgage',
      'insurance', 'tax', 'taxes', 'financial', 'finance', 'money', 'wealth',
      'asset', 'assets', 'liability', 'liabilities', 'net worth', 'income', 'expense',
      'compound', 'interest', 'inflation', 'recession', 'bull', 'bear', 'market cap',
      'pe ratio', 'earnings', 'revenue', 'profit margin', 'balance sheet', 'cash flow',
      'options', 'futures', 'forex', 'crypto', 'bitcoin', 'cryptocurrency', 'blockchain',
      'robinhood', 'fidelity', 'vanguard', 'schwab', 'etrade', 'ameritrade',
      'dollar cost averaging', 'dca', 'rebalancing', 'allocation', 'sector',
      'growth', 'value', 'dividend', 'income', 'capital gains', 'tax loss harvesting'
    ];

    // Non-financial keywords that should be rejected
    const nonFinancialKeywords = [
      'weather', 'cooking', 'recipe', 'travel', 'vacation', 'hotel', 'restaurant',
      'movie', 'music', 'sports', 'game', 'gaming', 'fashion', 'clothing', 'shopping',
      'relationship', 'dating', 'marriage', 'family', 'children', 'pets', 'animals',
      'health', 'medical', 'doctor', 'hospital', 'medicine', 'drug', 'exercise',
      'fitness', 'gym', 'workout', 'diet', 'food', 'nutrition', 'weight loss',
      'politics', 'election', 'government', 'law', 'legal', 'court', 'crime',
      'education', 'school', 'university', 'college', 'degree', 'course', 'study',
      'technology', 'programming', 'coding', 'software', 'hardware', 'computer',
      'car', 'vehicle', 'automobile', 'house', 'home', 'real estate', 'property',
      'job', 'career', 'work', 'employment', 'salary', 'interview', 'resume'
    ];

    // Check for non-financial keywords first
    const hasNonFinancialKeywords = nonFinancialKeywords.some(keyword => 
      input.includes(keyword)
    );

    if (hasNonFinancialKeywords) {
      return false;
    }

    // Check for financial keywords
    const hasFinancialKeywords = financialKeywords.some(keyword => 
      input.includes(keyword)
    );

    return hasFinancialKeywords;
  }

  /**
   * Extract investment context from user input
   */
  public extractInvestmentContext(userInput: string): InvestmentContext | null {
    const input = userInput.toLowerCase();
    
    // Extract amount
    const amountMatch = input.match(/\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)\s*(?:thousand|k|million|m|billion|b)?/);
    let amount = 0;
    if (amountMatch) {
      let numStr = amountMatch[1].replace(/,/g, '');
      // Check for multiplier words in the full match, not just the input
      const fullMatch = amountMatch[0].toLowerCase();
      const multiplier = fullMatch.includes('thousand') || fullMatch.includes('k') ? 1000 :
                        fullMatch.includes('million') || fullMatch.includes('m') ? 1000000 :
                        fullMatch.includes('billion') || fullMatch.includes('b') ? 1000000000 : 1;
      amount = parseFloat(numStr) * multiplier;
      
      // Debug logging
      console.log('Amount extraction debug:', {
        input: userInput,
        amountMatch: amountMatch[0],
        numStr,
        fullMatch,
        multiplier,
        finalAmount: amount
      });
    }

    // Extract time horizon
    let timeHorizon = 'medium';
    if (input.includes('year') || input.includes('annual')) {
      timeHorizon = 'long';
    } else if (input.includes('month') || input.includes('short')) {
      timeHorizon = 'short';
    }

    // Extract goal
    let goal = 'general investment';
    if (input.includes('trip') || input.includes('travel') || input.includes('vacation') || input.includes('miami') || input.includes('spending money')) {
      goal = 'travel fund';
    } else if (input.includes('retirement')) {
      goal = 'retirement';
    } else if (input.includes('house') || input.includes('home') || input.includes('property')) {
      goal = 'home purchase';
    } else if (input.includes('education') || input.includes('college') || input.includes('school')) {
      goal = 'education';
    }

    // Extract risk tolerance
    let riskTolerance: 'low' | 'medium' | 'high' = 'medium';
    if (input.includes('conservative') || input.includes('safe') || input.includes('low risk')) {
      riskTolerance = 'low';
    } else if (input.includes('aggressive') || input.includes('high risk') || input.includes('risky')) {
      riskTolerance = 'high';
    }

    return {
      amount,
      timeHorizon,
      goal,
      riskTolerance
    };
  }

  /**
   * Generate personalized investment advice
   */
  public async generateInvestmentAdvice(
    userInput: string,
    context: InvestmentContext
  ): Promise<string> {
    const { amount, timeHorizon, goal, riskTolerance } = context;

    // Handle small amounts for travel/spending money
    if (amount > 0 && amount < 2000 && (goal === 'travel fund' || userInput.toLowerCase().includes('spending money'))) {
      return `For $${amount.toLocaleString()} in spending money for your trip, here are some practical suggestions:

**Short-term Savings Strategy:**
• Keep the money in a high-yield savings account (4-5% APY)
• Consider a money market account for easy access
• Use a travel rewards credit card for purchases (pay off immediately)

**Budgeting Tips:**
• Set a daily spending limit ($${Math.round(amount / 7).toLocaleString()} per day for a week)
• Use cash for small purchases to control spending
• Track expenses with a budgeting app

**Travel Money Tips:**
• Notify your bank about travel plans
• Carry some cash for emergencies
• Use ATMs at banks (avoid hotel/airport ATMs with high fees)
• Consider travel insurance for larger trips

This amount is better suited for immediate spending rather than investment, as the short timeframe doesn't allow for meaningful growth.

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    // Generate stock recommendations based on context
    const recommendations = await this.getStockRecommendations(context);
    
    let response = `Based on your investment goal of ${goal} with $${amount.toLocaleString()} over a ${timeHorizon}-term period, here are my recommendations:\n\n`;

    // Add risk-appropriate advice
    if (riskTolerance === 'low') {
      response += `**Conservative Approach (Low Risk):**\n`;
      response += `• 60% Bonds/ETFs (BND, AGG)\n`;
      response += `• 30% Large-cap stocks (SPY, VTI)\n`;
      response += `• 10% Cash reserves\n\n`;
    } else if (riskTolerance === 'high') {
      response += `**Aggressive Approach (High Risk):**\n`;
      response += `• 70% Growth stocks (QQQ, ARKK)\n`;
      response += `• 20% Individual stocks (AAPL, MSFT, GOOGL)\n`;
      response += `• 10% International exposure (VXUS)\n\n`;
    } else {
      response += `**Balanced Approach (Medium Risk):**\n`;
      response += `• 50% Broad market ETFs (VTI, SPY)\n`;
      response += `• 30% Individual stocks\n`;
      response += `• 20% Bonds/REITs (BND, VNQ)\n\n`;
    }

    // Add specific stock recommendations
    if (recommendations.length > 0) {
      response += `**Specific Stock Recommendations:**\n`;
      recommendations.slice(0, 5).forEach((rec, index) => {
        response += `${index + 1}. **${rec.symbol}** (${rec.companyName})\n`;
        response += `   • Current Price: $${rec.currentPrice}\n`;
        response += `   • Target Price: $${rec.targetPrice}\n`;
        response += `   • Expected Return: ${rec.expectedReturn}%\n`;
        response += `   • Risk Level: ${rec.riskLevel}\n`;
        response += `   • Reason: ${rec.reason}\n\n`;
      });
    }

    // Add time-specific advice
    if (timeHorizon === 'short') {
      response += `**Short-term Strategy (1-2 years):**\n`;
      response += `• Focus on stable, dividend-paying stocks\n`;
      response += `• Consider high-yield savings accounts for safety\n`;
      response += `• Avoid highly volatile investments\n\n`;
    } else if (timeHorizon === 'long') {
      response += `**Long-term Strategy (5+ years):**\n`;
      response += `• Emphasize growth stocks and ETFs\n`;
      response += `• Consider dollar-cost averaging\n`;
      response += `• Rebalance quarterly\n\n`;
    }

    // Add goal-specific advice
    if (goal === 'travel fund') {
      response += `**Travel Fund Strategy:**\n`;
      response += `• Consider target-date funds for your trip timeline\n`;
      response += `• Keep 20% in liquid assets for last-minute opportunities\n`;
      response += `• Monitor currency exchange rates if traveling internationally\n\n`;
    }

    response += `**Important Disclaimers:**\n`;
    response += `• Past performance doesn't guarantee future results\n`;
    response += `• Diversify your investments to manage risk\n`;
    response += `• Consider consulting a financial advisor for personalized advice\n`;
    response += `• This is educational information, not financial advice\n`;

    return response;
  }

  /**
   * Get stock recommendations based on context
   */
  private async getStockRecommendations(context: InvestmentContext): Promise<StockRecommendation[]> {
    // This would typically call a GraphQL query or API
    // For now, return mock recommendations based on risk tolerance
    
    const mockRecommendations: StockRecommendation[] = [
      {
        symbol: 'AAPL',
        companyName: 'Apple Inc.',
        currentPrice: 175.50,
        targetPrice: 200.00,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 14.0,
        sector: 'Technology',
        reason: 'Strong fundamentals, consistent growth, and robust ecosystem'
      },
      {
        symbol: 'MSFT',
        companyName: 'Microsoft Corporation',
        currentPrice: 380.25,
        targetPrice: 420.00,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 10.5,
        sector: 'Technology',
        reason: 'Cloud computing leadership and AI integration'
      },
      {
        symbol: 'GOOGL',
        companyName: 'Alphabet Inc.',
        currentPrice: 140.80,
        targetPrice: 160.00,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 13.6,
        sector: 'Technology',
        reason: 'Dominant search and advertising business with AI potential'
      },
      {
        symbol: 'SPY',
        companyName: 'SPDR S&P 500 ETF',
        currentPrice: 445.20,
        targetPrice: 480.00,
        recommendation: 'BUY',
        riskLevel: 'Low',
        expectedReturn: 7.8,
        sector: 'Diversified',
        reason: 'Broad market exposure with low expense ratio'
      },
      {
        symbol: 'QQQ',
        companyName: 'Invesco QQQ Trust',
        currentPrice: 375.40,
        targetPrice: 410.00,
        recommendation: 'BUY',
        riskLevel: 'Medium',
        expectedReturn: 9.2,
        sector: 'Technology',
        reason: 'Nasdaq-100 exposure with growth focus'
      }
    ];

    // Filter based on risk tolerance
    if (context.riskTolerance === 'low') {
      return mockRecommendations.filter(rec => rec.riskLevel === 'Low');
    } else if (context.riskTolerance === 'high') {
      return mockRecommendations.filter(rec => rec.riskLevel === 'High' || rec.riskLevel === 'Medium');
    } else {
      return mockRecommendations.filter(rec => rec.riskLevel === 'Medium' || rec.riskLevel === 'Low');
    }
  }

  /**
   * Generate response for non-financial questions
   */
  public generateNonFinancialResponse(userInput: string): string {
    return `I'm a financial AI assistant focused on helping with investment, budgeting, and personal finance questions. 

I can help you with:
• Investment strategies and stock recommendations
• Retirement planning (IRAs, 401(k)s)
• Budgeting and saving strategies
• Risk management and diversification
• Financial terminology and concepts

Please ask me about personal finance, investing, or money management topics!`;
  }

  /**
   * Main method to process user input and generate appropriate response
   */
  public async processUserInput(userInput: string): Promise<string> {
    // Check if it's a financial question
    if (!this.isFinancialQuestion(userInput)) {
      return this.generateNonFinancialResponse(userInput);
    }

    // Extract investment context
    const context = this.extractInvestmentContext(userInput);
    
    // If we have investment context, generate personalized advice
    if (context && context.amount > 0) {
      return await this.generateInvestmentAdvice(userInput, context);
    }

    // Otherwise, provide general financial guidance
    return this.generateGeneralFinancialResponse(userInput);
  }

  /**
   * Generate general financial response for non-investment questions
   */
  private generateGeneralFinancialResponse(userInput: string): string {
    const input = userInput.toLowerCase();
    
    // Check for specific financial topics
    if (input.includes('budget') || input.includes('budgeting')) {
      return `**Budgeting Strategies:**\n\n**50/30/20 Rule:**\n• 50% for needs (housing, food, utilities)\n• 30% for wants (entertainment, dining)\n• 20% for savings and debt repayment\n\n**Zero-Based Budgeting:**\n• Assign every dollar a purpose\n• Track all expenses\n• Adjust monthly based on goals\n\n**Envelope Method:**\n• Use cash for variable expenses\n• Helps control spending\n• Visual representation of budget\n\nStart with the 50/30/20 rule and adjust based on your situation!`;
    }
    
    if (input.includes('debt') || input.includes('pay off')) {
      return `**Debt Payoff Strategies:**\n\n**Debt Snowball Method:**\n• Pay minimums on all debts\n• Extra payments to smallest balance\n• Build momentum with quick wins\n\n**Debt Avalanche Method:**\n• Pay minimums on all debts\n• Extra payments to highest interest rate\n• Saves more money long-term\n\n**Debt Consolidation:**\n• Combine multiple debts into one\n• Lower interest rate if possible\n• Simplify payments\n\nChoose the method that motivates you to stay consistent!`;
    }
    
    if (input.includes('emergency') || input.includes('rainy day')) {
      return `**Emergency Fund Strategy:**\n\n**How Much to Save:**\n• 3-6 months of expenses\n• Start with $1,000 if in debt\n• Increase as income grows\n\n**Where to Keep It:**\n• High-yield savings account\n• Money market account\n• Easy access, no penalties\n\n**Building Your Fund:**\n• Set up automatic transfers\n• Use windfalls (tax refunds, bonuses)\n• Cut unnecessary expenses\n\nAn emergency fund provides financial security and peace of mind!`;
    }
    
    // Check for specific financial education topics
    if (input.includes('etf') || input.includes('exchange traded fund')) {
      return `**Exchange-Traded Fund (ETF)**

An ETF is a type of investment fund that trades on stock exchanges, similar to stocks. ETFs hold assets such as stocks, commodities, or bonds and generally operate with an arbitrage mechanism designed to keep it trading close to its net asset value.

**Key Benefits:**
• Diversification across many assets
• Lower expense ratios than mutual funds
• Tax efficiency
• Intraday trading like stocks
• Transparency of holdings

**Popular ETF Examples:**
• SPY (S&P 500 ETF)
• QQQ (Nasdaq-100 ETF)
• VTI (Total Stock Market ETF)

ETFs are excellent for both beginners and experienced investors looking for cost-effective diversification.

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('index fund') || input.includes('index funds')) {
      return `**Index Funds Explained**

An index fund is a type of mutual fund or ETF designed to track the performance of a specific market index.

**How They Work:**
• Automatically track a market index (e.g., S&P 500)
• Buy all stocks in the index proportionally
• Rebalance automatically when index changes
• Low management fees (passive management)

**Popular Indexes:**
• S&P 500: 500 largest US companies
• Russell 2000: 2000 small-cap companies
• MSCI World: Global developed markets

**Benefits:**
• Low costs (expense ratios typically 0.03-0.15%)
• Broad diversification
• Consistent with market performance
• Tax efficient
• Easy to understand

Index funds are perfect for beginners and experienced investors who want market returns with minimal effort.

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('ira') || input.includes('roth') || input.includes('traditional')) {
      return `**Roth IRA vs Traditional IRA**

Both IRAs offer tax advantages, but they work differently:

**Traditional IRA:**
• Tax-deductible contributions (reduce current year taxes)
• Tax-deferred growth
• Required minimum distributions (RMDs) starting at age 72
• Early withdrawal penalties before age 59½

**Roth IRA:**
• After-tax contributions (no current year tax deduction)
• Tax-free growth and withdrawals
• No RMDs during your lifetime
• Contributions can be withdrawn penalty-free anytime

**Choose Traditional IRA if:**
• You expect to be in a lower tax bracket in retirement
• You want immediate tax savings

**Choose Roth IRA if:**
• You expect to be in a higher tax bracket in retirement
• You want tax-free income in retirement
• You want flexibility with withdrawals

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('compound interest') || input.includes('compounding')) {
      return `**Compound Interest Power**

Compound interest is earning interest on your interest, creating exponential growth.

**How It Works:**
• You earn interest on your principal
• You earn interest on previously earned interest
• Growth accelerates over time
• Time is your greatest ally

**The Rule of 72:**
• Divide 72 by your interest rate
• Result is years to double your money
• Example: 8% return = 9 years to double

**Examples:**
• $1,000 at 7% for 10 years = $1,967
• $1,000 at 7% for 20 years = $3,870
• $1,000 at 7% for 30 years = $7,612

**Maximizing Compound Interest:**
• Start investing early
• Invest regularly
• Reinvest dividends
• Avoid withdrawing early
• Choose growth investments

Albert Einstein called compound interest "the eighth wonder of the world" - start investing today!

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('diversification') || input.includes('diversify')) {
      return `**Diversification Strategy**

Diversification is spreading your investments across different assets to reduce risk.

**Types of Diversification:**
• Asset classes (stocks, bonds, real estate)
• Sectors (technology, healthcare, finance)
• Geographic regions (US, international, emerging markets)
• Company sizes (large-cap, mid-cap, small-cap)
• Investment styles (growth, value, blend)

**Benefits:**
• Reduces portfolio volatility
• Protects against single-asset losses
• Improves risk-adjusted returns
• Provides stability during market downturns

**How to Diversify:**
• Use index funds for broad exposure
• Invest in different sectors
• Include international investments
• Mix stocks and bonds
• Consider real estate (REITs)

Remember: Diversification doesn't guarantee profits or protect against all losses, but it's a fundamental risk management strategy.

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('options') || input.includes('option')) {
      return `**Options Trading Basics**

Options are contracts that give you the right to buy or sell stocks at specific prices.

**Types of Options:**
• Call Options: Right to BUY at strike price
• Put Options: Right to SELL at strike price

**Key Terms:**
• Strike Price: Price at which you can exercise the option
• Expiration Date: When the option expires
• Premium: Cost to buy the option
• In-the-Money: Option has intrinsic value
• Out-of-the-Money: Option has no intrinsic value

**Basic Strategies:**
• Covered Call: Sell calls against stock you own
• Protective Put: Buy puts to protect stock positions
• Long Call: Bet on stock price increase
• Long Put: Bet on stock price decrease

**Risk Considerations:**
• Options can expire worthless
• Time decay works against you
• Leverage amplifies both gains and losses
• Complex strategies require experience
• Start with paper trading

Remember: Options are advanced instruments. Master the basics before complex strategies.

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    // Default response
    return `I understand you're asking about "${userInput}". This is a great financial question!

Here are some topics I can help with:
• **Investment basics** - ETFs, index funds, stocks, options
• **Retirement planning** - IRAs, 401(k)s, pension plans
• **Budgeting** - 50/30/20 rule, zero-based budgeting
• **Debt management** - Payoff strategies, consolidation
• **Emergency funds** - How much to save, where to keep it
• **Risk management** - Diversification, asset allocation
• **Financial concepts** - Compound interest, market cap, expense ratios

Feel free to ask about any of these topics or try asking about a specific investment scenario!`;
  }
}

export default FinancialChatbotService;
