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
      const multiplier = input.includes('thousand') || input.includes('k') ? 1000 :
                        input.includes('million') || input.includes('m') ? 1000000 :
                        input.includes('billion') || input.includes('b') ? 1000000000 : 1;
      amount = parseFloat(numStr) * multiplier;
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
    if (input.includes('trip') || input.includes('travel') || input.includes('vacation')) {
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
    
    // Default response
    return `I understand you're asking about "${userInput}". This is a great financial question!

Here are some topics I can help with:
• **Investment strategies** - Stocks, ETFs, mutual funds
• **Retirement planning** - IRAs, 401(k)s, pension plans
• **Budgeting** - 50/30/20 rule, zero-based budgeting
• **Debt management** - Payoff strategies, consolidation
• **Emergency funds** - How much to save, where to keep it
• **Risk management** - Diversification, asset allocation

Feel free to ask about any of these topics or try asking about a specific investment scenario!`;
  }
}

export default FinancialChatbotService;
