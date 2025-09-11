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
    console.log('🔍 Checking if financial question for:', userInput);
    
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
      'growth', 'value', 'dividend', 'income', 'capital gains', 'tax loss harvesting',
      'aggressive', 'conservative', 'moderate', 'approach', 'strategy', 'strategies',
      // Add spending and purchase-related keywords
      'purchase', 'spend', 'spending', 'cost', 'price', 'expensive', 'cheap',
      'afford', 'affordable', 'worth', 'value', 'should i', 'worth it', 'buy',
      'get', 'item', 'product', 'thing', 'stuff',
      // Add savings and goal-related keywords
      'goal', 'goals', 'reach', 'achieve', 'target', 'dollars', 'dollar', 'earn', 'earning',
      'paycheck', 'biweekly', 'weekly', 'monthly', 'yearly', 'annual', 'salary', 'wage',
      'make', 'making', 'thousand', 'k', 'million', 'billion', 'amount', 'total',
      'save', 'saving', 'savings', 'accumulate', 'build', 'grow', 'increase',
      'versus', 'vs', 'compared to', 'better than', 'worse than', 'more than', 'less than',
      'worth more', 'worth less', 'valuable', 'value', 'prefer', 'choice', 'choose'
    ];

    // Non-financial keywords that should be rejected
    const nonFinancialKeywords = [
      'weather', 'cooking', 'recipe', 'movie', 'music', 'sports', 'game', 'gaming',
      'relationship', 'dating', 'marriage', 'family', 'children', 'pets', 'animals',
      'health', 'medical', 'doctor', 'hospital', 'medicine', 'drug', 'exercise',
      'fitness', 'gym', 'workout', 'diet', 'food', 'nutrition', 'weight loss',
      'politics', 'election', 'government', 'law', 'legal', 'court', 'crime',
      'education', 'school', 'university', 'college', 'degree', 'course', 'study',
      'technology', 'programming', 'coding', 'software', 'hardware', 'computer',
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

    // Additional check for savings/goal questions with numbers
    const hasNumbers = /\d+/.test(input);
    const hasSavingsContext = input.includes('save') || input.includes('reach') || input.includes('goal') || 
                             input.includes('dollars') || input.includes('saving') || input.includes('savings') ||
                             input.includes('accumulate') || input.includes('build') || input.includes('grow');
    const hasIncomeContext = input.includes('make') || input.includes('earn') || input.includes('paycheck') || 
                            input.includes('biweekly') || input.includes('weekly') || input.includes('monthly') ||
                            input.includes('salary') || input.includes('wage');
    
    const isSavingsQuestion = hasNumbers && hasSavingsContext && hasIncomeContext;

    console.log('Financial question result:', hasFinancialKeywords);
    console.log('Savings question check:', { hasNumbers, hasSavingsContext, hasIncomeContext, isSavingsQuestion });
    
    return hasFinancialKeywords || isSavingsQuestion;
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
    
    // Check for travel-related spending (any combination of travel words + spending/money words)
    const travelWords = ['trip', 'travel', 'vacation', 'miami', 'holiday', 'getaway', 'journey'];
    const spendingWords = ['spending', 'spend', 'cost', 'money', 'budget', 'cash', 'dollars'];
    const hasTravelWord = travelWords.some(word => input.includes(word));
    const hasSpendingWord = spendingWords.some(word => input.includes(word));
    
    if (hasTravelWord && hasSpendingWord) {
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
    const input = userInput.toLowerCase();
    const travelWords = ['trip', 'travel', 'vacation', 'miami', 'holiday', 'getaway', 'journey'];
    const spendingWords = ['spending', 'spend', 'cost', 'money', 'budget', 'cash', 'dollars'];
    const hasTravelWord = travelWords.some(word => input.includes(word));
    const hasSpendingWord = spendingWords.some(word => input.includes(word));
    
    if (amount > 0 && amount < 2000 && (goal === 'travel fund' || (hasTravelWord && hasSpendingWord))) {
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
    console.log('=== CHATBOT DEBUG ===');
    console.log('User input:', userInput);
    
    // Check if it's a financial question
    if (!this.isFinancialQuestion(userInput)) {
      console.log('Not a financial question');
      return this.generateNonFinancialResponse(userInput);
    }
    
    console.log('Is a financial question');

    // Check for savings calculation questions FIRST (before investment context)
    const input = userInput.toLowerCase();
    const hasSavingsKeywords = input.includes('save') || input.includes('reach') || input.includes('goal') ||
                              input.includes('saving') || input.includes('savings') || input.includes('accumulate') ||
                              input.includes('build') || input.includes('grow') || input.includes('achieve');
    const hasIncomeKeywords = input.includes('paycheck') || input.includes('biweekly') || input.includes('every two weeks') || 
                             input.includes('make') || input.includes('earn') || input.includes('weekly') || 
                             input.includes('monthly') || input.includes('salary') || input.includes('wage');
    
    console.log('Savings detection check:');
    console.log('- Input:', input);
    console.log('- Has savings keywords (save/reach/goal):', hasSavingsKeywords);
    console.log('- Has income keywords (paycheck/biweekly/make/earn):', hasIncomeKeywords);
    console.log('- Should trigger savings:', hasSavingsKeywords && hasIncomeKeywords);
    
    if (hasSavingsKeywords && hasIncomeKeywords) {
      console.log('🎯 DETECTED SAVINGS QUESTION - Triggering savings calculation');
      return this.generateSavingsCalculationResponse(userInput);
    }

    // Extract investment context
    console.log('Checking for investment context...');
    const context = this.extractInvestmentContext(userInput);
    console.log('Investment context:', context);
    
    // Only trigger investment advice for clear investment questions, not comparative questions
    const isInvestmentQuestion = context && context.amount > 0 && 
      (input.includes('invest') || input.includes('investment') || input.includes('portfolio') || 
       input.includes('stock') || input.includes('etf') || input.includes('mutual fund') ||
       input.includes('retirement') || input.includes('401k') || input.includes('ira'));
    
    if (isInvestmentQuestion) {
      console.log('💰 DETECTED INVESTMENT QUESTION - Triggering investment advice');
      return await this.generateInvestmentAdvice(userInput, context);
    }

    // Otherwise, provide general financial guidance
    console.log('📚 Using general financial response');
    return this.generateGeneralFinancialResponse(userInput);
  }

  /**
   * Generate savings calculation response
   */
  private generateSavingsCalculationResponse(userInput: string): string {
    const input = userInput.toLowerCase();
    
    console.log('Savings calculation triggered for:', userInput);
    console.log('Input after lowercasing:', input);
    
    // Extract numbers from the input (including k for thousands)
    const numberMatches = input.match(/(\d+)(?:k|thousand)?/gi);
    console.log('Number matches found:', numberMatches);
    if (!numberMatches || numberMatches.length < 2) {
      return `I'd be happy to help you calculate how much to save from each paycheck! 

To give you an accurate calculation, please provide:
• Your biweekly income amount
• Your savings goal amount
• Your target date

For example: "I make $600 every two weeks and want to save $5000 by December"`;
    }
    
    // Extract and convert the key numbers
    const income = parseInt(numberMatches[0].replace(/k|thousand/gi, ''));
    let goal = parseInt(numberMatches[1].replace(/k|thousand/gi, ''));
    
    // If the goal number was followed by 'k' or 'thousand', multiply by 1000
    if (numberMatches[1].toLowerCase().includes('k') || numberMatches[1].toLowerCase().includes('thousand')) {
      goal = goal * 1000;
    }
    
    // Calculate time until December
    const now = new Date();
    const currentMonth = now.getMonth(); // 0-11
    const december = 11; // December is month 11
    
    let monthsUntilDecember;
    if (currentMonth <= december) {
      monthsUntilDecember = december - currentMonth;
    } else {
      // If we're past December, calculate until next December
      monthsUntilDecember = (12 - currentMonth) + december;
    }
    
    // Calculate biweekly periods until December
    const biweeklyPeriods = Math.ceil((monthsUntilDecember * 30) / 14); // Approximate
    
    // Calculate how much to save per paycheck
    const savePerPaycheck = Math.ceil(goal / biweeklyPeriods);
    const percentageOfIncome = ((savePerPaycheck / income) * 100).toFixed(1);
    
    // Calculate total savings if they save this amount
    const totalSavings = savePerPaycheck * biweeklyPeriods;
    const extraAmount = totalSavings - goal;
    
    let response = `**Savings Calculation for $${goal.toLocaleString()} by December**\n\n`;
    response += `**Your Situation:**\n`;
    response += `• Biweekly income: $${income.toLocaleString()}\n`;
    response += `• Savings goal: $${goal.toLocaleString()}\n`;
    response += `• Time until December: ~${monthsUntilDecember} months\n`;
    response += `• Biweekly periods remaining: ~${biweeklyPeriods}\n\n`;
    
    response += `**Recommended Action:**\n`;
    response += `• Save **$${savePerPaycheck.toLocaleString()}** from each paycheck\n`;
    response += `• This is **${percentageOfIncome}%** of your biweekly income\n`;
    response += `• You'll have **$${totalSavings.toLocaleString()}** by December\n`;
    
    if (extraAmount > 0) {
      response += `• You'll have **$${extraAmount.toLocaleString()}** extra! 🎉\n\n`;
    } else {
      response += `\n`;
    }
    
    response += `**Savings Strategy:**\n`;
    response += `• Set up automatic transfer to savings account\n`;
    response += `• Treat savings like a bill - pay it first\n`;
    response += `• Consider a high-yield savings account (4-5% APY)\n`;
    response += `• Track your progress monthly\n\n`;
    
    response += `**Budget Impact:**\n`;
    response += `• Remaining income per paycheck: $${(income - savePerPaycheck).toLocaleString()}\n`;
    response += `• Monthly remaining income: $${((income - savePerPaycheck) * 2).toLocaleString()}\n`;
    response += `• Make sure this fits your monthly expenses\n\n`;
    
    if (percentageOfIncome > 20) {
      response += `⚠️ **Warning**: Saving ${percentageOfIncome}% of your income is quite aggressive. Make sure you can cover your essential expenses first!\n\n`;
    }
    
    response += `*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    
    return response;
  }

  /**
   * Generate general financial response for non-investment questions
   */
  private generateGeneralFinancialResponse(userInput: string): string {
    const input = userInput.toLowerCase();
    
    console.log('General financial response called with:', userInput);
    console.log('Input after lowercasing:', input);
    
    // Check for savings calculation questions
    const hasSavingsKeywords = input.includes('save') || input.includes('reach') || input.includes('goal') ||
                              input.includes('saving') || input.includes('savings') || input.includes('accumulate') ||
                              input.includes('build') || input.includes('grow') || input.includes('achieve');
    const hasIncomeKeywords = input.includes('paycheck') || input.includes('biweekly') || input.includes('every two weeks') || 
                             input.includes('make') || input.includes('earn') || input.includes('weekly') || 
                             input.includes('monthly') || input.includes('salary') || input.includes('wage');
    
    console.log('Has savings keywords:', hasSavingsKeywords);
    console.log('Has income keywords:', hasIncomeKeywords);
    console.log('Should trigger savings calculation:', hasSavingsKeywords && hasIncomeKeywords);
    
    if (hasSavingsKeywords && hasIncomeKeywords) {
      console.log('Triggering savings calculation response');
      return this.generateSavingsCalculationResponse(userInput);
    }
    
    // Check for "would you rather" or comparative financial questions
    if (input.includes('would you rather') || input.includes('better to have') || input.includes('more valuable') ||
        input.includes('versus') || input.includes('vs') || input.includes('compared to') || 
        input.includes('better than') || input.includes('worse than') || input.includes('worth more') ||
        input.includes('worth less') || input.includes('prefer') || input.includes('choice between')) {
      return `**$100,000 Cash vs 800 Credit Score - A Financial Analysis**

This is a fascinating financial question that depends on your current situation and goals:

**$100,000 Cash Advantages:**
• **Immediate liquidity** - Can invest, pay off debt, or handle emergencies
• **Investment potential** - Could grow to $1M+ over 20-30 years with 7-8% returns
• **Debt elimination** - Could pay off high-interest debt immediately
• **Opportunity cost** - Can take advantage of investment opportunities
• **Peace of mind** - Emergency fund and financial security

**800 Credit Score Advantages:**
• **Access to credit** - Can borrow money when needed at low rates
• **Lower costs** - Better rates on mortgages, car loans, credit cards
• **Financial flexibility** - Can leverage credit for investments or opportunities
• **Long-term benefit** - Credit score affects many financial decisions
• **No immediate cash** - But opens doors to borrowing power

**The Verdict:**
**$100,000 cash is generally more valuable** because:
1. **Time value of money** - $100K invested today could be worth $700K+ in 30 years
2. **Immediate utility** - Can solve problems, invest, or eliminate debt now
3. **Credit can be built** - You can improve credit score over time with good habits
4. **Cash is king** - Provides immediate options and opportunities

**However, 800 credit score is valuable if:**
• You need to borrow money for major purchases (house, business)
• You have high-interest debt that needs refinancing
• You're planning major financial moves requiring credit

**Bottom Line:** Take the $100,000, invest it wisely, and build your credit score through responsible financial habits. You'll have both the money AND the credit score over time!

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    // Check for investment strategy questions
    if (input.includes('aggressive approach') || input.includes('conservative approach') || 
        input.includes('moderate approach') || input.includes('investment strategy') ||
        input.includes('investment approach') || input.includes('portfolio strategy')) {
      return `**Investment Strategy Approaches**

Here's a comprehensive breakdown of different investment approaches:

**Aggressive Approach (High Risk/High Reward):**
• **Allocation**: 70-80% stocks, 10-20% bonds, 10% alternatives
• **Focus**: Growth stocks, small-cap companies, emerging markets
• **Examples**: ARKK, QQQ, individual tech stocks, crypto
• **Time Horizon**: 10+ years
• **Risk Level**: High volatility, potential for 15-20% annual returns
• **Best For**: Young investors, long time horizon, high risk tolerance

**Conservative Approach (Low Risk/Stable Returns):**
• **Allocation**: 60-70% bonds, 20-30% stocks, 10% cash
• **Focus**: Blue-chip stocks, government bonds, dividend stocks
• **Examples**: BND, VTI, utility stocks, REITs
• **Time Horizon**: 3-5 years
• **Risk Level**: Low volatility, 4-7% annual returns
• **Best For**: Near retirement, short time horizon, low risk tolerance

**Moderate/Balanced Approach (Medium Risk/Moderate Returns):**
• **Allocation**: 50-60% stocks, 30-40% bonds, 10% alternatives
• **Focus**: Large-cap stocks, index funds, corporate bonds
• **Examples**: SPY, VTI, BND, target-date funds
• **Time Horizon**: 5-10 years
• **Risk Level**: Moderate volatility, 7-10% annual returns
• **Best For**: Most investors, balanced risk tolerance

**Key Factors to Consider:**
• **Age**: Younger = more aggressive, older = more conservative
• **Time Horizon**: Longer = more aggressive, shorter = more conservative
• **Risk Tolerance**: How much volatility can you handle?
• **Financial Goals**: Retirement, house, education, etc.
• **Income Stability**: Stable job = more aggressive, variable = more conservative

**Remember**: You can always adjust your approach as your situation changes!

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

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

    if (input.includes('market cap') || input.includes('market capitalization')) {
      return `**Market Capitalization (Market Cap)**

Market cap is the total value of a company's outstanding shares of stock.

**How It's Calculated:**
• Market Cap = Current Stock Price × Total Outstanding Shares
• Example: $100 stock price × 1 billion shares = $100 billion market cap

**Market Cap Categories:**
• **Large Cap**: $10+ billion (Apple, Microsoft, Amazon)
• **Mid Cap**: $2-10 billion (established companies with growth potential)
• **Small Cap**: $300 million - $2 billion (smaller, potentially faster-growing companies)
• **Micro Cap**: Under $300 million (very small companies, higher risk)

**Why Market Cap Matters:**
• Indicates company size and stability
• Affects stock volatility and liquidity
• Determines index inclusion (S&P 500 requires large cap)
• Influences investment strategy and risk level

**Investment Considerations:**
• Large cap: More stable, lower growth potential
• Small cap: Higher risk, potentially higher returns
• Diversify across different market caps for balanced portfolio

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('pe ratio') || input.includes('price to earnings') || input.includes('p/e')) {
      return `**Price-to-Earnings (P/E) Ratio**

The P/E ratio compares a company's stock price to its earnings per share.

**How It's Calculated:**
• P/E Ratio = Stock Price ÷ Earnings Per Share (EPS)
• Example: $100 stock price ÷ $5 EPS = 20 P/E ratio

**What P/E Tells You:**
• **High P/E (20+)**: Investors expect high growth, stock may be overvalued
• **Low P/E (under 15)**: Stock may be undervalued or company has issues
• **Average P/E**: Varies by industry and market conditions

**P/E Categories:**
• **Trailing P/E**: Based on past 12 months earnings
• **Forward P/E**: Based on projected future earnings
• **Industry P/E**: Compare to similar companies

**Limitations:**
• Doesn't account for growth rates
• Can be misleading for companies with no earnings
• Varies significantly by industry

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('dividend') || input.includes('dividends')) {
      return `**Dividends Explained**

Dividends are payments made by companies to shareholders from their profits.

**Types of Dividends:**
• **Cash Dividends**: Direct cash payments to shareholders
• **Stock Dividends**: Additional shares instead of cash
• **Special Dividends**: One-time extra payments

**Key Dividend Metrics:**
• **Dividend Yield**: Annual dividend ÷ stock price (e.g., $2 dividend ÷ $100 stock = 2% yield)
• **Dividend Payout Ratio**: Dividends paid ÷ net income
• **Dividend Growth Rate**: How much dividends increase annually

**Dividend Aristocrats:**
• Companies that have increased dividends for 25+ consecutive years
• Examples: Coca-Cola, Johnson & Johnson, Procter & Gamble

**Benefits:**
• Regular income stream
• Reinvestment for compound growth
• Often indicates stable, profitable companies

**Considerations:**
• Dividends are not guaranteed
• High yields can indicate problems
• Tax implications on dividend income

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('volatility') || input.includes('volatile')) {
      return `**Volatility in Investing**

Volatility measures how much a stock's price fluctuates over time.

**Types of Volatility:**
• **Historical Volatility**: Based on past price movements
• **Implied Volatility**: Market's expectation of future price swings
• **Realized Volatility**: Actual price movements that occurred

**Measuring Volatility:**
• **Standard Deviation**: Statistical measure of price dispersion
• **Beta**: Compares stock volatility to market (S&P 500)
• **VIX**: "Fear index" measuring market volatility expectations

**Volatility Levels:**
• **Low Volatility (Beta < 1)**: Less volatile than market (utilities, consumer staples)
• **High Volatility (Beta > 1)**: More volatile than market (tech stocks, small caps)

**Investment Implications:**
• Higher volatility = higher risk and potential returns
• Lower volatility = more stable, predictable returns
• Diversification helps reduce portfolio volatility

**Managing Volatility:**
• Dollar-cost averaging
• Diversification across sectors
• Appropriate asset allocation
• Long-term perspective

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('beta') || input.includes('stock beta')) {
      return `**Beta in Stock Analysis**

Beta measures a stock's volatility relative to the overall market.

**How Beta Works:**
• **Beta = 1.0**: Moves exactly with the market
• **Beta > 1.0**: More volatile than market (amplifies market movements)
• **Beta < 1.0**: Less volatile than market (dampens market movements)
• **Beta = 0**: No correlation with market (rare)

**Examples:**
• **High Beta (1.5+)**: Tech stocks, small caps, growth stocks
• **Low Beta (0.5-0.8)**: Utilities, consumer staples, bonds
• **Negative Beta**: Some defensive stocks, inverse ETFs

**Using Beta:**
• **Risk Assessment**: Higher beta = higher risk
• **Portfolio Construction**: Mix high and low beta stocks
• **Market Timing**: High beta stocks amplify market trends

**Limitations:**
• Based on historical data
• Doesn't predict future volatility
• Can change over time
• Doesn't account for company-specific risks

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('expense ratio') || input.includes('expense ratios')) {
      return `**Expense Ratios in Funds**

An expense ratio is the annual fee charged by mutual funds and ETFs.

**How It Works:**
• Expressed as a percentage of assets under management
• Automatically deducted from fund returns
• Example: 0.5% expense ratio on $10,000 investment = $50 annual fee

**Typical Expense Ratios:**
• **Index Funds/ETFs**: 0.03% - 0.15% (very low)
• **Actively Managed Funds**: 0.5% - 2.0% (higher)
• **Target Date Funds**: 0.1% - 0.8%

**Impact on Returns:**
• Lower expense ratios = higher net returns
• Over 30 years, 0.5% difference can cost thousands
• Example: $10,000 at 7% return over 30 years:
  - 0.1% expense ratio: $76,123
  - 0.6% expense ratio: $66,439
  - Difference: $9,684

**What's Included:**
• Management fees
• Administrative costs
• Marketing expenses (12b-1 fees)
• Operating expenses

**Choosing Funds:**
• Compare expense ratios within same category
• Lower is generally better
• Consider total return, not just fees

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('401k') || input.includes('401(k)')) {
      return `**401(k) Retirement Plans**

A 401(k) is an employer-sponsored retirement savings plan with tax advantages.

**How 401(k)s Work:**
• Employee contributions deducted from paycheck
• Employer may match contributions (free money!)
• Investments grow tax-deferred
• Withdrawals taxed as income in retirement

**Contribution Limits (2024):**
• Employee: $23,000 (under 50), $30,500 (50+)
• Total (employee + employer): $69,000
• Catch-up contributions: $7,500 for 50+

**Types of 401(k)s:**
• **Traditional 401(k)**: Pre-tax contributions, tax-deferred growth
• **Roth 401(k)**: After-tax contributions, tax-free withdrawals
• **Some plans offer both options**

**Employer Matching:**
• Common: 50% match up to 6% of salary
• Example: Earn $50,000, contribute 6% ($3,000), get $1,500 match
• Always contribute enough to get full match!

**Investment Options:**
• Usually 10-20 mutual funds/ETFs
• Target-date funds (set and forget)
• Index funds (low cost)
• Company stock (limit exposure)

**Withdrawal Rules:**
• Penalty-free at age 59½
• Required minimum distributions at 73
• Early withdrawal penalty: 10% + taxes

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('emergency fund') || input.includes('emergency funds')) {
      return `**Emergency Fund Essentials**

An emergency fund is money set aside for unexpected expenses.

**How Much to Save:**
• **Minimum**: 1 month of expenses
• **Recommended**: 3-6 months of expenses
• **Conservative**: 6-12 months of expenses
• **Variable income**: 6-12 months (more uncertainty)

**What Counts as Emergency:**
• Job loss or reduced income
• Medical emergencies
• Major car repairs
• Home repairs (roof, HVAC)
• Unexpected travel (family emergency)

**Where to Keep It:**
• **High-yield savings account**: 4-5% APY, FDIC insured
• **Money market account**: Slightly higher rates
• **CDs**: Higher rates, but less accessible
• **NOT in stocks**: Too volatile for emergencies

**Building Your Fund:**
• Start small: $500-1,000 first
• Automate transfers from checking
• Use windfalls: tax refunds, bonuses
• Cut expenses temporarily
• Sell unused items

**Emergency Fund vs. Other Savings:**
• Separate from vacation fund
• Different from house down payment
• Not for planned expenses
• Focus on accessibility and safety

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('budget') || input.includes('budgeting')) {
      return `**Budgeting Strategies**

A budget is a plan for how to spend and save your money.

**Popular Budgeting Methods:**

**50/30/20 Rule:**
• 50%: Needs (housing, food, utilities, minimum debt payments)
• 30%: Wants (entertainment, dining out, hobbies)
• 20%: Savings and debt repayment

**Zero-Based Budgeting:**
• Every dollar assigned a purpose
• Income minus expenses = $0
• More detailed tracking required

**Envelope Method:**
• Cash in envelopes for different categories
• When envelope is empty, stop spending
• Great for controlling discretionary spending

**Steps to Create a Budget:**
1. **Track income**: All sources of monthly income
2. **List expenses**: Fixed and variable costs
3. **Categorize**: Needs vs. wants
4. **Set limits**: Realistic spending targets
5. **Track spending**: Use apps or spreadsheets
6. **Review monthly**: Adjust as needed

**Budgeting Apps:**
• Mint: Automatic categorization
• YNAB: Zero-based budgeting
• Personal Capital: Investment tracking
• Goodbudget: Envelope method

**Common Budgeting Mistakes:**
• Not tracking small purchases
• Being too restrictive
• Not accounting for irregular expenses
• Not reviewing and adjusting

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('debt') || input.includes('debt management')) {
      return `**Debt Management Strategies**

Effective debt management is crucial for financial health.

**Types of Debt:**
• **Good Debt**: Low interest, builds wealth (mortgage, student loans)
• **Bad Debt**: High interest, depreciating assets (credit cards, payday loans)
• **Neutral Debt**: Moderate interest, necessary (car loans)

**Debt Payoff Strategies:**

**Debt Snowball Method:**
• Pay minimums on all debts
• Extra payments on smallest debt first
• Builds momentum and motivation
• Psychological benefits

**Debt Avalanche Method:**
• Pay minimums on all debts
• Extra payments on highest interest rate debt
• Saves more money in interest
• Mathematically optimal

**Debt Consolidation:**
• Combine multiple debts into one payment
• Lower interest rate or payment
• Balance transfer credit cards
• Personal loans
• Home equity loans

**Debt Settlement:**
• Negotiate with creditors for lower payoff
• Damages credit score
• Tax implications on forgiven debt
• Last resort option

**Preventing New Debt:**
• Build emergency fund
• Use cash for purchases
• Avoid lifestyle inflation
• Track spending carefully

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('credit score') || input.includes('credit scores')) {
      return `**Credit Score Importance**

Your credit score is a three-digit number that represents your creditworthiness to lenders.

**Credit Score Ranges:**
• **Excellent (750-850)**: Best interest rates and terms
• **Good (700-749)**: Good rates, some premium options
• **Fair (650-699)**: Higher rates, limited options
• **Poor (600-649)**: High rates, few options
• **Very Poor (300-599)**: Very high rates, limited approval

**What Affects Your Credit Score:**
• **Payment History (35%)**: On-time payments are crucial
• **Credit Utilization (30%)**: Keep balances under 30% of limits
• **Credit History Length (15%)**: Longer history is better
• **Credit Mix (10%)**: Different types of credit (cards, loans)
• **New Credit (10%)**: Recent applications and accounts

**Why Credit Scores Matter:**
• **Interest Rates**: Better scores = lower rates
• **Loan Approval**: Higher scores = easier approval
• **Insurance Premiums**: Some insurers use credit scores
• **Rental Applications**: Landlords often check credit
• **Employment**: Some employers check credit

**Improving Your Credit Score:**
• Pay bills on time, every time
• Keep credit card balances low
• Don't close old accounts unnecessarily
• Limit new credit applications
• Check your credit report regularly

**Credit Monitoring:**
• Free annual credit reports from AnnualCreditReport.com
• Credit monitoring services
• Dispute errors immediately
• Set up payment reminders

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('dollar cost averaging') || input.includes('dca')) {
      return `**Dollar-Cost Averaging (DCA)**

DCA is an investment strategy where you invest a fixed amount regularly, regardless of market conditions.

**How DCA Works:**
• Invest the same amount at regular intervals
• Buy more shares when prices are low
• Buy fewer shares when prices are high
• Reduces impact of market volatility
• Example: $500 every month into an index fund

**Benefits:**
• **Reduces Timing Risk**: Don't need to predict market movements
• **Emotional Discipline**: Removes emotion from investing decisions
• **Lower Average Cost**: Often results in better average purchase price
• **Habit Formation**: Builds consistent investing habits
• **Reduces Volatility Impact**: Smooths out market ups and downs

**DCA Example:**
Month 1: $500 ÷ $100/share = 5 shares
Month 2: $500 ÷ $80/share = 6.25 shares
Month 3: $500 ÷ $120/share = 4.17 shares
Average cost: $1,500 ÷ 15.42 shares = $97.28/share

**When to Use DCA:**
• Regular income (salary, wages)
• Long-term investment goals
• Volatile markets
• Building wealth over time
• Retirement savings

**DCA vs Lump Sum:**
• **DCA**: Lower risk, potentially lower returns
• **Lump Sum**: Higher risk, potentially higher returns
• **Historical Data**: Lump sum often outperforms DCA
• **Psychological**: DCA feels safer and more manageable

**Implementation Tips:**
• Automate your investments
• Choose low-cost index funds
• Stay consistent regardless of market conditions
• Increase amounts when possible
• Don't stop during market downturns

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('analyze stocks') || input.includes('stock analysis') || input.includes('how to analyze')) {
      return `**How to Analyze Stocks**

Stock analysis helps you make informed investment decisions by evaluating a company's financial health and growth potential.

**Fundamental Analysis:**

**Financial Statements:**
• **Income Statement**: Revenue, expenses, profit margins
• **Balance Sheet**: Assets, liabilities, shareholder equity
• **Cash Flow Statement**: Operating, investing, financing cash flows

**Key Financial Ratios:**
• **P/E Ratio**: Price-to-earnings (valuation)
• **PEG Ratio**: P/E divided by growth rate
• **Debt-to-Equity**: Financial leverage
• **ROE**: Return on equity (profitability)
• **Current Ratio**: Liquidity measure

**Company Metrics:**
• **Revenue Growth**: Year-over-year growth rates
• **Profit Margins**: Gross, operating, net margins
• **Market Share**: Industry position
• **Management Quality**: Leadership track record
• **Competitive Advantage**: Moat analysis

**Technical Analysis:**
• **Price Charts**: Support and resistance levels
• **Moving Averages**: Trend identification
• **Volume Analysis**: Trading activity
• **Momentum Indicators**: RSI, MACD
• **Chart Patterns**: Head and shoulders, triangles

**Qualitative Factors:**
• **Industry Trends**: Growth prospects
• **Competitive Position**: Market leadership
• **Management Team**: Experience and vision
• **Business Model**: Sustainability
• **Regulatory Environment**: Legal risks

**Analysis Process:**
1. **Research the Company**: Business model, products, services
2. **Review Financials**: Last 3-5 years of statements
3. **Calculate Ratios**: Compare to industry averages
4. **Assess Growth**: Revenue and earnings trends
5. **Evaluate Risks**: Industry, company-specific risks
6. **Determine Valuation**: Fair value estimate
7. **Make Decision**: Buy, hold, or sell

**Red Flags to Avoid:**
• Declining revenue or earnings
• High debt levels
• Poor management
• Industry in decline
• Accounting irregularities

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    if (input.includes('trading fundamentals') || input.includes('trading basics')) {
      return `**Trading Fundamentals**

Trading involves buying and selling securities to profit from price movements.

**Types of Trading:**
• **Day Trading**: Buy and sell within the same day
• **Swing Trading**: Hold positions for days to weeks
• **Position Trading**: Hold for months to years
• **Scalping**: Very short-term trades (minutes)
• **Momentum Trading**: Follow price trends

**Essential Trading Concepts:**

**Market Orders:**
• **Market Order**: Execute immediately at current price
• **Limit Order**: Execute only at specified price or better
• **Stop Order**: Trigger when price reaches certain level
• **Stop-Limit Order**: Combination of stop and limit

**Risk Management:**
• **Position Sizing**: Don't risk more than 1-2% per trade
• **Stop Losses**: Set predetermined exit points
• **Diversification**: Don't put all money in one trade
• **Risk-Reward Ratio**: Aim for at least 1:2 ratio
• **Maximum Drawdown**: Limit total portfolio losses

**Trading Psychology:**
• **Emotional Control**: Don't let fear or greed drive decisions
• **Discipline**: Stick to your trading plan
• **Patience**: Wait for good setups
• **Accept Losses**: Part of trading, learn from them
• **Avoid Revenge Trading**: Don't try to recover losses quickly

**Technical Analysis Basics:**
• **Support/Resistance**: Price levels that tend to hold
• **Trend Lines**: Direction of price movement
• **Volume**: Confirms price movements
• **Moving Averages**: Smooth price data
• **Chart Patterns**: Predict future movements

**Fundamental Analysis:**
• **Earnings Reports**: Company financial performance
• **Economic Indicators**: GDP, inflation, employment
• **Industry News**: Sector-specific developments
• **Company News**: Product launches, management changes
• **Market Sentiment**: Overall market mood

**Trading Platforms:**
• **Brokerage Accounts**: Choose based on fees and features
• **Charting Software**: Technical analysis tools
• **News Sources**: Stay informed about market events
• **Educational Resources**: Learn continuously

**Common Trading Mistakes:**
• **Overtrading**: Too many trades, high fees
• **Lack of Plan**: No clear entry/exit strategy
• **Ignoring Risk**: Not using stop losses
• **Emotional Trading**: Fear and greed decisions
• **Chasing Performance**: Following hot tips

**Getting Started:**
1. **Learn the Basics**: Understand markets and instruments
2. **Paper Trade**: Practice without real money
3. **Start Small**: Use small amounts initially
4. **Keep Records**: Track all trades and performance
5. **Continuous Learning**: Markets evolve constantly

*This is educational information only. For personalized financial advice, consult a qualified financial advisor.*`;
    }

    // Smart purchase decision framework - works for any item
    if (input.includes('should i') && (input.includes('buy') || input.includes('purchase') || input.includes('get'))) {
      return `**Smart Purchase Decision Framework**

When considering any purchase, here's a comprehensive financial evaluation:

**Before You Buy - Ask These Questions:**

**1. Financial Health Check:**
• Do you have an emergency fund (6+ months expenses)?
• Are you debt-free or actively paying down debt?
• Are you contributing to retirement accounts?
• Does this purchase fit your budget?

**2. Value Assessment:**
• **Need vs. Want**: Is this essential or discretionary?
• **Cost per Use**: How often will you actually use this?
• **Quality vs. Price**: Will a cheaper alternative work?
• **Opportunity Cost**: What else could this money do?

**3. Purchase Timing:**
• **Wait 24-48 Hours**: Avoid impulse purchases
• **Research Prices**: Compare options and look for deals
• **Consider Used/Refurbished**: Often 30-70% cheaper
• **Seasonal Sales**: Wait for better timing if possible

**4. Smart Spending Rules:**
• **Cash Only**: Never finance non-essential purchases
• **Budget Allocation**: Limit discretionary spending to 10-20% of income
• **Quality Over Quantity**: Buy fewer, better items
• **One In, One Out**: Replace rather than accumulate

**5. Alternative Approaches:**
• **Borrow/Rent**: For items you'll rarely use
• **Save Up**: Set aside money monthly until you can afford it
• **Buy Used**: Check online marketplaces and thrift stores
• **DIY/Repair**: Fix what you have instead of replacing

**6. Long-term Thinking:**
• Will this bring lasting value or temporary satisfaction?
• Could this money grow if invested instead?
• What would your future self think of this purchase?
• Does this align with your financial goals?

**Remember**: Every purchase is a choice between spending now vs. investing for the future. Choose wisely!

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
