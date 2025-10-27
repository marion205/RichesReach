from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

app = FastAPI(title="RichesReach Fresh Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for Apollo Client."""
    # Parse the request body
    body = await request.json()
    query_str = body.get("query", "")
    
    print(f"DEBUG: GraphQL query received: {query_str[:100]}...")
    
    # Handle StartLesson mutation - MINIMAL VERSION
    if "startLesson" in query_str:
        print("DEBUG: Processing StartLesson mutation")
        variables = body.get("variables", {})
        
        # Simple topic extraction
        topic = variables.get("topic", "stock basics")
        topic = topic.strip().lower().replace('_', ' ')
        
        print(f"DEBUG: Topic detected: '{topic}'")
        
        # Comprehensive lesson lookup with detailed educational content
        lessons = {
            "stock basics": {
                "title": "📈 Stock Trading Fundamentals",
                "text": """🎯 **What Are Stocks?**

Stocks represent ownership shares in a company. When you buy a stock, you own a small piece of that company!

**Key Concepts:**
• **Share Price**: What you pay for one share
• **Market Cap**: Total value of all shares (Price × Shares Outstanding)
• **Dividends**: Company profits paid to shareholders
• **Bull Market**: Prices going up 📈
• **Bear Market**: Prices going down 📉

**How to Get Started:**
1. **Open a Brokerage Account** (Robinhood, Fidelity, TD Ameritrade)
2. **Start Small** - Begin with $100-500
3. **Research Companies** - Understand what you're buying
4. **Diversify** - Don't put all money in one stock

**Real Example:**
AAPL stock at $150:
- Buy 10 shares = $1,500 investment
- If AAPL goes to $160: You make $100 profit
- If AAPL drops to $140: You lose $100

**Pro Tips:**
✅ Start with index funds (SPY, QQQ) for safety
✅ Never invest money you can't afford to lose
✅ Learn about P/E ratios and company fundamentals""",
                "voiceNarration": "Welcome to stock trading! Learn the fundamentals of buying and selling company shares.",
                "quiz": {
                    "id": "quiz_stock_basics",
                    "question": "What happens when you buy a stock?",
                    "options": ["You lend money to the company", "You own a small piece of the company", "You become the company's employee", "You get guaranteed profits"],
                    "correct": 1,
                    "explanation": "Correct! Buying a stock means you own shares and become a partial owner of the company.",
                    "voiceHint": "Think about what ownership means when you buy something."
                },
                "xpEarned": 40,
                "difficulty": 1,
                "estimatedTimeMinutes": 6,
                "skillsTargeted": ["stock_trading", "fundamentals"]
            },
            
            "crypto basics": {
                "title": "₿ Cryptocurrency Trading",
                "text": """🎯 **What is Cryptocurrency?**

Cryptocurrency is digital money that uses blockchain technology. It's decentralized, meaning no bank controls it!

**Popular Cryptocurrencies:**
• **Bitcoin (BTC)**: Digital gold, store of value
• **Ethereum (ETH)**: Smart contracts platform
• **Cardano (ADA)**: Academic approach to blockchain
• **Solana (SOL)**: Fast, low-cost transactions

**How Crypto Trading Works:**
1. **Buy on Exchanges** (Coinbase, Binance, Kraken)
2. **Store in Wallets** (Hardware wallets for security)
3. **Trade Pairs** (BTC/USD, ETH/BTC)
4. **HODL or Trade** - Long-term hold vs active trading

**Crypto vs Stocks:**
📊 **Stocks**: Regulated, company ownership, dividends
₿ **Crypto**: 24/7 trading, high volatility, decentralized

**Real Example:**
Bitcoin at $30,000:
- Buy 0.1 BTC = $3,000 investment
- If BTC goes to $40,000: You make $1,000 profit
- If BTC drops to $20,000: You lose $1,000

**Safety Tips:**
✅ Never invest more than you can afford to lose
✅ Use hardware wallets for large amounts
✅ Beware of scams and fake exchanges
✅ Understand the technology before investing""",
                "voiceNarration": "Welcome to cryptocurrency! Learn about digital money and blockchain technology.",
                "quiz": {
                    "id": "quiz_crypto_basics",
                    "question": "What makes cryptocurrency different from regular money?",
                    "options": ["It's controlled by banks", "It uses blockchain technology", "It's only available online", "It has no value"],
                    "correct": 1,
                    "explanation": "Correct! Cryptocurrency uses blockchain technology, making it decentralized and secure.",
                    "voiceHint": "Think about the technology that powers digital currencies."
                },
                "xpEarned": 60,
                "difficulty": 2,
                "estimatedTimeMinutes": 10,
                "skillsTargeted": ["crypto_trading", "blockchain"]
            },
            
            "options basics": {
                "title": "📊 Options Trading Fundamentals",
                "text": """🎯 **What Are Options?**

Options are financial contracts that give you the RIGHT (not obligation) to buy or sell a stock at a specific price by a certain date.

**Key Terms:**
• **Call Option**: Right to BUY at strike price
• **Put Option**: Right to SELL at strike price  
• **Strike Price**: The price you can buy/sell at
• **Expiration Date**: When the option expires
• **Premium**: Cost to buy the option

**Real Example:**
AAPL is at $150. You buy a $155 call option for $3.
- If AAPL goes to $160: You profit $2 ($160-$155-$3)
- If AAPL stays at $150: You lose $3 (the premium)

**Why Trade Options?**
✅ Leverage - Control more shares with less money
✅ Hedging - Protect your portfolio
✅ Income - Sell options for premium""",
                "voiceNarration": "Welcome to options trading! Options give you the right to buy or sell stocks at specific prices.",
                "quiz": {
                    "id": "quiz_options_basics",
                    "question": "What happens if you buy a call option and the stock price goes below the strike price?",
                    "options": ["You make unlimited profit", "You lose only the premium paid", "You must buy the stock", "You get your money back"],
                    "correct": 1,
                    "explanation": "Correct! With options, your maximum loss is limited to the premium you paid.",
                    "voiceHint": "Remember: options limit your downside risk to the premium paid."
                },
                "xpEarned": 50,
                "difficulty": 2,
                "estimatedTimeMinutes": 8,
                "skillsTargeted": ["options_trading", "risk_management"]
            },
            
            "volatility trading": {
                "title": "📈 Volatility Trading Strategies", 
                "text": """🎯 **Understanding Volatility**

Volatility measures how much a stock's price moves up and down. High volatility = big price swings, Low volatility = small price swings.

**Volatility Indicators:**
• **VIX**: "Fear Index" - measures market volatility
• **Beta**: How much a stock moves vs market
• **Standard Deviation**: Statistical measure of price swings

**Volatility Trading Strategies:**

**1. Straddle Strategy** 📊
- Buy both call AND put at same strike price
- Profit when stock moves significantly either way
- Best in high volatility environments

**2. Iron Condor** 🦅
- Sell call spread + sell put spread
- Profit when stock stays in range
- Best in low volatility environments

**Real Example:**
TSLA earnings coming up (high volatility expected):
- Buy $200 straddle for $15
- If TSLA moves to $220 or $180: Profit!
- If TSLA stays at $200: Lose $15""",
                "voiceNarration": "Volatility is your friend in options trading! Learn proven strategies.",
                "quiz": {
                    "id": "quiz_volatility_trading",
                    "question": "Which strategy works best when you expect high volatility?",
                    "options": ["Iron Condor", "Straddle", "Calendar Spread", "Covered Call"],
                    "correct": 1,
                    "explanation": "Perfect! Straddles profit from big moves in either direction.",
                    "voiceHint": "Think about strategies that benefit from big price movements."
                },
                "xpEarned": 75,
                "difficulty": 3,
                "estimatedTimeMinutes": 12,
                "skillsTargeted": ["volatility_trading", "options_strategies"]
            },
            
            "risk management": {
                "title": "🛡️ Risk Management Mastery",
                "text": """🎯 **The Golden Rules of Risk Management**

**Rule #1: Never Risk More Than You Can Afford to Lose**
- Only trade with money you don't need for essentials
- Set maximum loss per trade (usually 1-2% of account)
- Never add money to losing positions

**Rule #2: Position Sizing** 📏
- Risk = Entry Price - Stop Loss
- Position Size = Risk Amount ÷ Risk Per Share
- Example: $1000 account, 1% risk = $10 max loss
- If risk is $2 per share, buy only 5 shares

**Rule #3: Diversification** 🌈
- Don't put all eggs in one basket
- Spread risk across different sectors
- Use different strategies simultaneously

**Real Example:**
Account: $10,000
Max risk per trade: 1% = $100
Stock price: $50, Stop loss: $48
Risk per share: $2
Position size: $100 ÷ $2 = 50 shares""",
                "voiceNarration": "Risk management is the foundation of successful trading. Learn to protect your capital.",
                "quiz": {
                    "id": "quiz_risk_management",
                    "question": "If you have a $10,000 account and want to risk 1% per trade, what's your maximum loss per trade?",
                    "options": ["$100", "$1,000", "$500", "$50"],
                    "correct": 0,
                    "explanation": "Exactly! 1% of $10,000 is $100. This conservative approach helps preserve capital.",
                    "voiceHint": "Calculate 1% of your account size."
                },
                "xpEarned": 80,
                "difficulty": 3,
                "estimatedTimeMinutes": 10,
                "skillsTargeted": ["risk_management", "position_sizing"]
            },
            
            "crypto strategies": {
                "title": "₿ Advanced Crypto Strategies",
                "text": """🎯 **Crypto Trading Strategies**

**1. Dollar-Cost Averaging (DCA)** 💰
- Buy fixed amounts regularly (weekly/monthly)
- Reduces impact of price volatility
- Great for long-term accumulation

**2. HODLing** 🚀
- Buy and hold for years
- Based on belief in long-term crypto adoption
- Requires strong conviction

**3. Swing Trading** 📊
- Hold positions for days/weeks
- Use technical analysis
- Requires more active management

**4. DeFi Yield Farming** 🌾
- Provide liquidity to earn rewards
- Higher risk, higher potential returns
- Understand impermanent loss

**Real Examples:**
- **DCA**: Buy $100 of BTC every week
- **HODL**: Buy BTC and hold for 4+ years
- **Swing**: Buy BTC at support, sell at resistance
- **DeFi**: Provide ETH/USDC liquidity for 15% APY

**Risk Management for Crypto:**
⚠️ Never invest more than 5-10% of portfolio
⚠️ Use stop losses for active trading
⚠️ Keep most crypto in cold storage
⚠️ Diversify across different cryptocurrencies""",
                "voiceNarration": "Master advanced cryptocurrency strategies from DCA to DeFi yield farming.",
                "quiz": {
                    "id": "quiz_crypto_strategies",
                    "question": "What is Dollar-Cost Averaging (DCA)?",
                    "options": ["Buying all at once", "Buying fixed amounts regularly", "Selling everything at once", "Only buying on weekends"],
                    "correct": 1,
                    "explanation": "Correct! DCA involves buying fixed amounts regularly to reduce volatility impact.",
                    "voiceHint": "Think about spreading your purchases over time."
                },
                "xpEarned": 90,
                "difficulty": 3,
                "estimatedTimeMinutes": 12,
                "skillsTargeted": ["crypto_strategies", "defi"]
            },
            
            "technical analysis": {
                "title": "📊 Technical Analysis Fundamentals",
                "text": """🎯 **What is Technical Analysis?**

Technical analysis studies price charts and trading volume to predict future price movements. It's based on the idea that market psychology repeats itself.

**Key Concepts:**
• **Support**: Price level where buying interest is strong
• **Resistance**: Price level where selling pressure is strong
• **Trend**: Overall direction of price movement
• **Volume**: Number of shares traded

**Essential Indicators:**

**1. Moving Averages** 📈
- **SMA (Simple Moving Average)**: Average price over time period
- **EMA (Exponential Moving Average)**: Gives more weight to recent prices
- **Golden Cross**: 50-day MA crosses above 200-day MA (bullish)
- **Death Cross**: 50-day MA crosses below 200-day MA (bearish)

**2. RSI (Relative Strength Index)** ⚖️
- Measures if stock is overbought (>70) or oversold (<30)
- Helps identify potential reversal points
- Values between 0-100

**3. MACD (Moving Average Convergence Divergence)** 🔄
- Shows relationship between two moving averages
- Signal line crossovers indicate buy/sell signals
- Histogram shows momentum changes

**Real Example:**
AAPL stock analysis:
- Price breaks above $150 resistance = Bullish signal
- RSI at 75 = Overbought, expect pullback
- MACD line crosses above signal = Buy signal
- Volume increases on breakout = Confirms strength

**Chart Patterns:**
📈 **Head and Shoulders**: Reversal pattern
📊 **Double Top/Bottom**: Reversal signals
🔺 **Triangles**: Continuation patterns
📋 **Flags and Pennants**: Short-term continuations

**Pro Tips:**
✅ Always use multiple indicators for confirmation
✅ Consider market context and news events
✅ Practice on paper before using real money
✅ Remember: Past performance doesn't guarantee future results""",
                "voiceNarration": "Master the art of reading charts and predicting price movements with technical analysis.",
                "quiz": {
                    "id": "quiz_technical_analysis",
                    "question": "What does RSI above 70 typically indicate?",
                    "options": ["Stock is oversold", "Stock is overbought", "Strong uptrend", "Market crash coming"],
                    "correct": 1,
                    "explanation": "Correct! RSI above 70 indicates the stock is overbought and may be due for a pullback.",
                    "voiceHint": "Think about what 'overbought' means - too much buying pressure."
                },
                "xpEarned": 85,
                "difficulty": 3,
                "estimatedTimeMinutes": 15,
                "skillsTargeted": ["technical_analysis", "chart_patterns"]
            },
            
            "fundamental analysis": {
                "title": "📋 Fundamental Analysis Mastery",
                "text": """🎯 **What is Fundamental Analysis?**

Fundamental analysis evaluates a company's intrinsic value by examining financial statements, industry conditions, and economic factors.

**Key Financial Metrics:**

**1. Valuation Ratios** 💰
- **P/E Ratio**: Price-to-Earnings (Stock Price ÷ Earnings Per Share)
- **PEG Ratio**: P/E ÷ Growth Rate (better than P/E alone)
- **P/B Ratio**: Price-to-Book Value
- **P/S Ratio**: Price-to-Sales

**2. Profitability Metrics** 📊
- **ROE (Return on Equity)**: Net Income ÷ Shareholder Equity
- **ROA (Return on Assets)**: Net Income ÷ Total Assets
- **Gross Margin**: (Revenue - COGS) ÷ Revenue
- **Net Margin**: Net Income ÷ Revenue

**3. Growth Metrics** 📈
- **Revenue Growth**: Year-over-year sales increase
- **EPS Growth**: Earnings per share growth
- **Book Value Growth**: Shareholder equity growth

**Real Example:**
Analyzing AAPL (Apple Inc.):
- P/E Ratio: 25 (industry average: 20) = Slightly expensive
- ROE: 15% = Efficient use of shareholder capital
- Revenue Growth: 8% = Steady growth
- Debt-to-Equity: 0.3 = Low debt, financially stable

**Industry Analysis:**
🔍 **Market Size**: How big is the total addressable market?
📊 **Competition**: Who are the main competitors?
🚀 **Growth Stage**: Is the industry growing, mature, or declining?
📋 **Regulation**: What government rules affect the industry?

**Economic Factors:**
🏦 **Interest Rates**: Affect borrowing costs and valuations
📈 **Inflation**: Impacts consumer spending and costs
🌍 **Currency**: Exchange rates affect international companies
📊 **GDP Growth**: Overall economic health

**Red Flags to Watch:**
⚠️ Declining revenue for multiple quarters
⚠️ Increasing debt without growth
⚠️ Management changes or scandals
⚠️ Industry disruption or new competitors

**Pro Tips:**
✅ Compare companies within the same industry
✅ Look at trends over multiple years, not just one quarter
✅ Consider qualitative factors: management quality, brand strength
✅ Use multiple valuation methods for confirmation""",
                "voiceNarration": "Learn to evaluate companies like a professional analyst using financial statements and industry analysis.",
                "quiz": {
                    "id": "quiz_fundamental_analysis",
                    "question": "What does a high P/E ratio typically indicate?",
                    "options": ["Stock is undervalued", "Stock is overvalued", "Company has no earnings", "Stock is very stable"],
                    "correct": 1,
                    "explanation": "Correct! A high P/E ratio suggests investors are paying more for each dollar of earnings, indicating potential overvaluation.",
                    "voiceHint": "Think about what P/E ratio measures - price relative to earnings."
                },
                "xpEarned": 95,
                "difficulty": 4,
                "estimatedTimeMinutes": 18,
                "skillsTargeted": ["fundamental_analysis", "valuation"]
            },
            
            "portfolio management": {
                "title": "💼 Portfolio Management Strategies",
                "text": """🎯 **Building a Winning Portfolio**

Portfolio management is the art of combining different investments to achieve your financial goals while managing risk.

**Core Portfolio Principles:**

**1. Asset Allocation** 🎯
- **Stocks**: Growth potential, higher risk
- **Bonds**: Income generation, lower risk
- **Cash**: Liquidity and safety
- **Alternative Assets**: Real estate, commodities, crypto

**2. Diversification Strategies** 🌈
- **Geographic**: US, International, Emerging Markets
- **Sector**: Technology, Healthcare, Finance, Energy
- **Market Cap**: Large-cap, Mid-cap, Small-cap
- **Style**: Growth vs Value stocks

**3. Risk Management** 🛡️
- **Correlation**: Don't put all eggs in correlated baskets
- **Rebalancing**: Adjust allocation quarterly/annually
- **Position Sizing**: Limit individual stock exposure
- **Stop Losses**: Protect against major losses

**Portfolio Models:**

**Conservative Portfolio** (Low Risk):
- 60% Bonds, 30% Large-cap stocks, 10% Cash
- Target: Capital preservation + modest growth
- Suitable for: Near retirement, risk-averse investors

**Balanced Portfolio** (Moderate Risk):
- 50% Stocks, 40% Bonds, 10% Alternatives
- Target: Steady growth with moderate volatility
- Suitable for: Middle-aged investors, 10+ year horizon

**Aggressive Portfolio** (High Risk):
- 80% Stocks, 15% Bonds, 5% Alternatives
- Target: Maximum growth potential
- Suitable for: Young investors, long-term horizon

**Real Example:**
$100,000 Portfolio Allocation:
- **Large-cap US stocks**: $40,000 (40%)
- **International stocks**: $20,000 (20%)
- **Bonds**: $25,000 (25%)
- **Small-cap stocks**: $10,000 (10%)
- **Cash/Alternatives**: $5,000 (5%)

**Rebalancing Strategy:**
📅 **Quarterly Review**: Check if allocation drifted >5%
🔄 **Rebalance**: Sell winners, buy underperformers
📊 **Tax Efficiency**: Use tax-advantaged accounts first
💰 **Dollar-Cost Averaging**: Regular contributions

**Performance Monitoring:**
📈 **Benchmark Comparison**: S&P 500, Total Stock Market
📊 **Risk-Adjusted Returns**: Sharpe ratio, Sortino ratio
🎯 **Goal Tracking**: Are you on track for retirement?
📋 **Annual Review**: Adjust strategy based on life changes

**Common Mistakes to Avoid:**
❌ **Over-diversification**: Too many small positions
❌ **Under-diversification**: Concentrated in few stocks
❌ **Chasing Performance**: Buying last year's winners
❌ **Ignoring Costs**: High fees eat into returns
❌ **Emotional Trading**: Making decisions based on fear/greed

**Pro Tips:**
✅ Start with index funds for broad market exposure
✅ Gradually add individual stocks as you learn
✅ Keep costs low with low-fee ETFs and funds
✅ Stay disciplined with your allocation strategy
✅ Review and rebalance regularly, but don't over-trade""",
                "voiceNarration": "Master the art of building and managing a diversified investment portfolio for long-term success.",
                "quiz": {
                    "id": "quiz_portfolio_management",
                    "question": "What is the main benefit of portfolio diversification?",
                    "options": ["Guaranteed profits", "Reduced risk", "Higher returns", "Lower taxes"],
                    "correct": 1,
                    "explanation": "Correct! Diversification reduces risk by spreading investments across different assets, sectors, and regions.",
                    "voiceHint": "Think about not putting all your eggs in one basket."
                },
                "xpEarned": 100,
                "difficulty": 4,
                "estimatedTimeMinutes": 20,
                "skillsTargeted": ["portfolio_management", "asset_allocation"]
            }
        }
        
        # Get lesson content with better fallback
        lesson = lessons.get(topic, lessons["stock basics"])
        
        return {
            "data": {
                "startLesson": {
                    "id": f"lesson_{topic.replace(' ', '_')}",
                    "title": lesson["title"],
                    "text": lesson["text"],
                    "voiceNarration": lesson["voiceNarration"],
                    "quiz": {
                        "id": lesson["quiz"]["id"],
                        "question": lesson["quiz"]["question"],
                        "options": lesson["quiz"]["options"],
                        "correct": lesson["quiz"]["correct"],
                        "explanation": lesson["quiz"]["explanation"],
                        "voiceHint": lesson["quiz"]["voiceHint"],
                        "__typename": "Quiz"
                    },
                    "xpEarned": lesson["xpEarned"],
                    "streak": 1,
                    "difficulty": lesson["difficulty"],
                    "estimatedTimeMinutes": lesson["estimatedTimeMinutes"],
                    "skillsTargeted": lesson["skillsTargeted"],
                    "__typename": "Lesson"
                }
            }
        }
    
    # Default response
    return {"data": {"message": "No matching GraphQL operation found"}}

if __name__ == "__main__":
    print("🚀 Starting Fresh RichesReach Test Server...")
    print("📡 Server will be available at: http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
