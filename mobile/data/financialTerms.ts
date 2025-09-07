// Financial Terms Dictionary for Educational Tooltips
export const FINANCIAL_TERMS = {
  // Portfolio Terms
  'Total Value': 'The current market value of all your investments combined. This is what your portfolio is worth right now.',
  
  'Total Return': 'The total amount of money you\'ve gained or lost on your investments. It\'s the difference between what you paid and what your investments are worth now.',
  
  'Return Percentage': 'Shows how much your investments have grown or shrunk as a percentage. A positive percentage means you\'re making money, negative means you\'re losing money.',
  
  'Portfolio': 'Your collection of investments (stocks, bonds, etc.). Think of it as your investment "basket" that holds all your different investments.',
  
  'Diversification': 'Spreading your money across different types of investments to reduce risk. Like not putting all your eggs in one basket!',
  
  'Asset Allocation': 'How you divide your money between different types of investments (stocks, bonds, cash, etc.).',
  
  'Rebalancing': 'Adjusting your portfolio to get back to your target mix of investments. Like reorganizing your closet to keep things neat.',
  
  // Stock Terms
  'Stock': 'A small piece of ownership in a company. When you buy a stock, you own a tiny part of that company.',
  
  'Share': 'A single unit of stock. If you own 10 shares of Apple, you own 10 tiny pieces of Apple.',
  
  'Current Price': 'The price you would pay to buy one share of this stock right now.',
  
  'Cost Basis': 'The original price you paid for your shares. This is used to calculate your gains or losses.',
  
  'Market Cap': 'The total value of all shares of a company. It\'s calculated by multiplying the stock price by the number of shares.',
  
  'Volume': 'How many shares of a stock were traded today. High volume means lots of people are buying and selling.',
  
  'Dividend': 'A payment some companies make to their shareholders, usually quarterly. It\'s like getting a small bonus for owning the stock.',
  
  // Risk Terms
  'Volatility': 'How much a stock\'s price goes up and down. High volatility means big price swings, low volatility means steadier prices.',
  
  'Beta': 'Measures how much a stock moves compared to the overall market. A beta of 1 means it moves with the market, 2 means it moves twice as much.',
  
  'Risk': 'The chance that you might lose money on an investment. Higher risk usually means higher potential returns, but also higher chance of loss.',
  
  'Sharpe Ratio': 'A measure of how much extra return you get for the risk you take. Higher is better - it means you\'re getting more reward for your risk.',
  
  // Market Terms
  'Bull Market': 'A period when stock prices are generally rising. Investors are optimistic and buying more.',
  
  'Bear Market': 'A period when stock prices are generally falling. Investors are pessimistic and selling more.',
  
  'Market Index': 'A measurement of the overall stock market performance. The S&P 500 is a popular index of 500 large companies.',
  
  'Sector': 'A group of companies in the same industry. For example, technology, healthcare, or energy sectors.',
  
  // Investment Strategy Terms
  'Buy and Hold': 'A strategy where you buy investments and keep them for a long time, regardless of short-term price changes.',
  
  'Dollar-Cost Averaging': 'Investing a fixed amount regularly, regardless of price. This helps reduce the impact of market volatility.',
  
  'Stop Loss': 'An order to sell a stock if it drops to a certain price, helping limit your losses.',
  
  'Take Profit': 'An order to sell a stock when it reaches a certain profit target.',
  
  // Analysis Terms
  'Fundamental Analysis': 'Evaluating a company based on its financial health, business model, and industry position.',
  
  'Technical Analysis': 'Using charts and patterns to predict future price movements based on past performance.',
  
  'P/E Ratio': 'Price-to-Earnings ratio. Compares a stock\'s price to its earnings. Lower might mean the stock is undervalued.',
  
  'EPS': 'Earnings Per Share. How much profit a company makes per share of stock.',
  
  // Economic Terms
  'Inflation': 'The rate at which prices for goods and services increase over time. It reduces the purchasing power of money.',
  
  'Interest Rate': 'The cost of borrowing money or the return on lending money. Set by central banks and affects the economy.',
  
  'GDP': 'Gross Domestic Product. The total value of all goods and services produced in a country.',
  
  'Recession': 'A period of economic decline, typically marked by falling GDP, rising unemployment, and reduced spending.',
  
  // Trading Terms
  'Market Order': 'An order to buy or sell immediately at the current market price.',
  
  'Limit Order': 'An order to buy or sell at a specific price or better.',
  
  'Bid': 'The highest price someone is willing to pay for a stock.',
  
  'Ask': 'The lowest price someone is willing to sell a stock for.',
  
  'Spread': 'The difference between the bid and ask prices.',
  
  // Tax Terms
  'Capital Gains': 'Profit from selling an investment for more than you paid for it.',
  
  'Capital Loss': 'Loss from selling an investment for less than you paid for it.',
  
  'Tax-Loss Harvesting': 'Selling losing investments to offset gains and reduce taxes.',
  
  'Long-term Capital Gains': 'Gains on investments held for more than a year, usually taxed at a lower rate.',
  
  'Short-term Capital Gains': 'Gains on investments held for a year or less, taxed at your regular income tax rate.',
};

// Helper function to get term explanation
export const getTermExplanation = (term: string): string => {
  return FINANCIAL_TERMS[term as keyof typeof FINANCIAL_TERMS] || 
    'This term doesn\'t have an explanation yet. We\'re working on adding more educational content!';
};

// Helper function to check if term exists
export const hasTermExplanation = (term: string): boolean => {
  return term in FINANCIAL_TERMS;
};
