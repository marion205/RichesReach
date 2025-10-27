#!/usr/bin/env python3
"""
Simple test server for crypto basics lesson
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import time
from datetime import datetime, timedelta

app = FastAPI(title="Crypto Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Crypto Test Server is running!"}

@app.get("/api/wealth-circles/")
async def get_wealth_circles():
    """Mock wealth circles endpoint."""
    return [
        {
            "id": "1",
            "name": "BIPOC Wealth Builders",
            "description": "Building generational wealth through smart investing and community support",
            "members": 1247,
            "category": "investment",
            "activity": [
                {"user": "Alex Johnson", "action": "shared portfolio"},
                {"user": "Maria Garcia", "action": "posted trade"},
                {"user": "David Chen", "action": "commented"}
            ]
        },
        {
            "id": "2", 
            "name": "Crypto Innovators",
            "description": "Exploring blockchain technology and cryptocurrency investments",
            "members": 892,
            "category": "crypto",
            "activity": [
                {"user": "Sarah Kim", "action": "shared analysis"},
                {"user": "Mike Torres", "action": "posted signal"},
                {"user": "Lisa Wang", "action": "commented"}
            ]
        },
        {
            "id": "3",
            "name": "Real Estate Moguls", 
            "description": "Building wealth through real estate investments and property management",
            "members": 654,
            "category": "real_estate",
            "activity": [
                {"user": "James Wilson", "action": "shared property"},
                {"user": "Emma Davis", "action": "posted deal"},
                {"user": "Ryan Brown", "action": "commented"}
            ]
        }
    ]


@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for crypto basics testing."""
    body = await request.json()
    query_str = body.get("query", "")
    variables = body.get("variables", {})
    
    print(f"DEBUG: GraphQL query received: {query_str[:100]}...")
    
    if "startLesson" in query_str:
        print("DEBUG: Processing StartLesson mutation")
        topic = variables.get("topic", "crypto basics")
        topic = topic.strip().lower().replace('_', ' ')
        
        print(f"DEBUG: Topic detected: '{topic}'")
        
        # Crypto basics lesson
        crypto_lesson = {
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

**Getting Started:**
1. **Choose an Exchange** - Start with Coinbase for beginners
2. **Buy Small Amounts** - Start with $50-100
3. **Learn About Wallets** - Hot wallets vs cold wallets
4. **Understand Volatility** - Crypto can swing 20%+ daily

**Real Example:**
Bitcoin at $30,000:
- Buy 0.01 BTC = $300 investment
- If BTC goes to $33,000: You make $30 profit
- If BTC drops to $27,000: You lose $30

**Pro Tips:**
✅ Never invest more than you can afford to lose
✅ Use dollar-cost averaging (buy small amounts regularly)
✅ Learn about blockchain technology
✅ Keep most crypto in cold storage""",
            "voiceNarration": "Welcome to cryptocurrency trading! Learn about digital money and blockchain technology.",
            "quiz": {
                "id": "quiz_crypto_basics",
                "question": "What makes cryptocurrency different from regular money?",
                "options": [
                    "It's controlled by banks",
                    "It's decentralized and uses blockchain",
                    "It's only used online",
                    "It's backed by gold"
                ],
                "correct": 1,
                "explanation": "Correct! Cryptocurrency is decentralized and uses blockchain technology, meaning no single authority controls it.",
                "voiceHint": "Think about what 'decentralized' means - no central authority."
            },
            "xpEarned": 60,
            "difficulty": 1,
            "estimatedTimeMinutes": 8,
            "skillsTargeted": ["crypto_trading", "blockchain"]
        }
        
        # Stock basics lesson
        stock_lesson = {
            "title": "📈 Stock Trading Fundamentals",
            "text": """🎯 **What is Stock Trading?**

Stock trading is buying and selling shares of publicly traded companies. When you buy a stock, you own a small piece of that company!

**How Stock Trading Works:**
1. **Choose a Broker** - Online platforms like Robinhood, E*TRADE, or TD Ameritrade
2. **Open an Account** - Link your bank account for deposits
3. **Research Stocks** - Look at company financials, news, and trends
4. **Place Orders** - Market orders (immediate) or limit orders (specific price)

**Types of Orders:**
• **Market Order**: Buy/sell immediately at current price
• **Limit Order**: Buy/sell only at your target price
• **Stop Loss**: Automatically sell if price drops below threshold

**Key Concepts:**
• **Shares**: Units of ownership in a company
• **Dividends**: Regular payments some companies make to shareholders
• **Market Cap**: Total value of all company shares
• **P/E Ratio**: Price-to-earnings ratio (valuation metric)

**Real Example:**
Apple (AAPL) at $150 per share:
- Buy 10 shares = $1,500 investment
- If AAPL goes to $165: You make $150 profit (10% gain)
- If AAPL drops to $135: You lose $150 (10% loss)

**Getting Started:**
1. **Start Small** - Begin with $100-500
2. **Diversify** - Don't put all money in one stock
3. **Research First** - Understand what you're buying
4. **Think Long-term** - Don't panic sell on daily fluctuations

**Pro Tips:**
✅ Never invest more than you can afford to lose
✅ Use dollar-cost averaging (buy small amounts regularly)
✅ Focus on companies you understand
✅ Keep emotions out of trading decisions""",
            "voiceNarration": "Welcome to stock trading! Learn how to buy and sell shares of companies.",
            "quiz": {
                "id": "quiz_stock_basics",
                "question": "What happens when you buy a stock?",
                "options": ["You lend money to the company", "You own a small piece of the company", "You become the company's employee", "You get guaranteed profits"],
                "correct": 1,
                "explanation": "Correct! Buying a stock means you own shares and become a partial owner of the company.",
                "voiceHint": "Think about what ownership means when you buy something."
            },
            "xpEarned": 50,
            "difficulty": 1,
            "estimatedTimeMinutes": 7,
            "skillsTargeted": ["stock_trading", "fundamentals"]
        }
        
        # Return appropriate lesson based on topic
        if topic == "crypto basics":
            lesson = crypto_lesson
        elif topic == "stock basics":
            lesson = stock_lesson
        else:
            # Default to crypto basics for unknown topics
            lesson = crypto_lesson
        
        return {
            "data": {
                "startLesson": {
                    "id": f"lesson_{topic.replace(' ', '_')}",
                    "title": lesson["title"],
                    "text": lesson["text"],
                    "voiceNarration": lesson["voiceNarration"],
                    "quiz": lesson["quiz"],
                    "xpEarned": lesson["xpEarned"],
                    "difficulty": lesson["difficulty"],
                    "estimatedTimeMinutes": lesson["estimatedTimeMinutes"],
                    "skillsTargeted": lesson["skillsTargeted"]
                }
            }
        }
    
        # Handle tutorProgress query
        if "tutorProgress" in query_str:
            print("DEBUG: Processing tutorProgress query")
            return {
                "data": {
                    "tutorProgress": {
                        "userId": "user_123",
                        "xp": 1250,
                        "level": 3,
                        "streakDays": 7,
                        "badges": ["first_lesson", "crypto_explorer"],
                        "hearts": 5,
                        "maxHearts": 5,
                        "abilityEstimate": 0.75,
                        "skillMastery": {
                            "crypto_trading": 0.6,
                            "stock_trading": 0.4,
                            "risk_management": 0.5
                        }
                    }
                }
            }
    
        # Handle dailyQuest query
        if "dailyQuest" in query_str:
            print("DEBUG: Processing dailyQuest query")
            return {
                "data": {
                    "dailyQuest": {
                        "id": "quest_daily_001",
                        "title": "Daily Learning Challenge",
                        "description": "Complete 3 lessons today to earn bonus XP!",
                        "questType": "learning",
                        "difficulty": "medium",
                        "rewards": [
                            {"type": "XP", "amount": 100},
                            {"type": "BADGE", "amount": 1}
                        ],
                        "progress": 0.0,
                        "target": 3,
                        "current": 0,
                        "expiresAt": "2025-01-28T23:59:59Z",
                        "xpReward": 100,
                        "timeLimitMinutes": 30,
                        "requiredSkills": ["crypto_trading", "stock_trading"],
                        "regimeContext": "BULL",
                        "voiceNarration": "Welcome to your daily quest! Complete 3 lessons to earn bonus XP!",
                        "completionCriteria": "Complete 3 lessons with 80% accuracy"
                    }
                }
            }
    
    # Handle StartQuest mutation
    if "startQuest" in query_str:
        print("DEBUG: Processing StartQuest mutation")
        difficulty = variables.get("difficulty", "MEDIUM")
        
        # Create a quest session
        quest_session = {
            "id": f"quest_{difficulty.lower()}_{int(time.time())}",
            "topic": "daily quest",
            "difficulty": difficulty,
            "rewards": [
                {"type": "XP", "amount": 100 if difficulty == "EASY" else 150 if difficulty == "MEDIUM" else 200},
                {"type": "BADGE", "amount": 1}
            ],
            "progress": 0.0,
            "narration": f"Welcome to your {difficulty.lower()} daily quest! Complete trading scenarios to earn bonus rewards.",
            "expiresAt": (datetime.now() + timedelta(hours=24)).isoformat(),
            "questType": "simulation",
            "scenarios": [
                {
                    "id": "scenario_1",
                    "title": "Crypto Trading Challenge",
                    "description": "Practice buying and selling cryptocurrency",
                    "difficulty": difficulty,
                    "xpReward": 25
                },
                {
                    "id": "scenario_2", 
                    "title": "Stock Trading Challenge",
                    "description": "Practice stock market trading",
                    "difficulty": difficulty,
                    "xpReward": 25
                }
            ],
            "timeLimitMinutes": 30
        }
        
        return {
            "data": {
                "startQuest": quest_session
            }
        }
    
    # Handle UpdateQuestProgress mutation
    if "updateQuestProgress" in query_str:
        print("DEBUG: Processing UpdateQuestProgress mutation")
        questId = variables.get("questId", "quest_medium_123")
        progress = variables.get("progress", 0.5)
        
        return {
            "data": {
                "updateQuestProgress": {
                    "questId": questId,
                    "progress": progress,
                    "completed": progress >= 1.0,
                    "xpEarned": int(progress * 100)
                }
            }
        }
    
    # Handle portfolioMetrics query (check first to avoid conflicts)
    if "portfolioMetrics" in query_str:
        print("DEBUG: Processing portfolioMetrics query")
        return {
            "data": {
                "portfolioMetrics": {
                    "totalValue": 125847.50,
                    "totalCost": 98000.00,
                    "totalReturn": 27847.50,
                    "totalReturnPercent": 28.42,
                    "holdings": [
                        {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "shares": 50,
                            "currentPrice": 185.25,
                            "totalValue": 9262.50,
                            "costBasis": 8500.00,
                            "returnAmount": 762.50,
                            "returnPercent": 8.97,
                            "sector": "Technology"
                        },
                        {
                            "symbol": "TSLA",
                            "companyName": "Tesla Inc.",
                            "shares": 25,
                            "currentPrice": 245.80,
                            "totalValue": 6145.00,
                            "costBasis": 5500.00,
                            "returnAmount": 645.00,
                            "returnPercent": 11.73,
                            "sector": "Automotive"
                        },
                        {
                            "symbol": "BTC",
                            "companyName": "Bitcoin",
                            "shares": 0.5,
                            "currentPrice": 45000.00,
                            "totalValue": 22500.00,
                            "costBasis": 20000.00,
                            "returnAmount": 2500.00,
                            "returnPercent": 12.50,
                            "sector": "Cryptocurrency"
                        }
                    ]
                }
            }
        }
    
    # Handle socialFeeds query (check before me to avoid conflicts)
    if "socialFeeds" in query_str:
        print("DEBUG: Processing socialFeeds query")
        limit = variables.get("limit", 10)
        offset = variables.get("offset", 0)
        return {
            "data": {
                "socialFeeds": [
                    {
                        "id": "feed_1",
                        "user": {
                            "id": "user_456",
                            "username": "crypto_trader",
                            "profilePic": "https://via.placeholder.com/50",
                            "verified": True
                        },
                        "content": "Just made a great trade on ETH! Up 15% this week 🚀",
                        "type": "TRADE_UPDATE",
                        "likes": 23,
                        "comments": 8,
                        "shares": 3,
                        "createdAt": "2025-01-28T14:30:00Z",
                        "tags": ["ETH", "crypto", "trading"]
                    },
                    {
                        "id": "feed_2",
                        "user": {
                            "id": "user_789",
                            "username": "stock_guru",
                            "profilePic": "https://via.placeholder.com/50",
                            "verified": False
                        },
                        "content": "Market analysis: Tech stocks looking strong for Q1. AAPL, MSFT, GOOGL all showing bullish patterns.",
                        "type": "MARKET_ANALYSIS",
                        "likes": 45,
                        "comments": 12,
                        "shares": 7,
                        "createdAt": "2025-01-28T13:15:00Z",
                        "tags": ["tech", "analysis", "stocks"]
                    }
                ]
            }
        }
    
    # Handle me query (check after other specific queries to avoid conflicts)
    if "me {" in query_str:
        print("DEBUG: Processing me query")
        return {
            "data": {
                "me": {
                    "id": "user_123",
                    "name": "Test User",
                    "email": "test@richesreach.com",
                    "username": "testuser",
                    "profilePic": "https://via.placeholder.com/150",
                    "hasPremiumAccess": True,
                    "subscriptionTier": "PREMIUM",
                    "followersCount": 42,
                    "followingCount": 38,
                    "totalTrades": 156,
                    "winRate": 0.68,
                    "totalPnL": 2847.50,
                    "riskTolerance": "MODERATE",
                    "tradingStyle": "SWING",
                    "experienceLevel": "INTERMEDIATE",
                    "preferredAssets": ["STOCKS", "CRYPTO"],
                    "notificationsEnabled": True,
                    "emailNotifications": True,
                    "pushNotifications": True,
                    "createdAt": "2024-01-15T10:30:00Z",
                    "lastLoginAt": "2025-01-28T15:00:00Z"
                }
            }
        }
    
    # Handle topTraders query
    if "topTraders" in query_str:
        print("DEBUG: Processing topTraders query")
        period = variables.get("period", "week")
        return {
            "data": {
                "topTraders": [
                    {
                        "id": "trader_1",
                        "username": "crypto_king",
                        "avatar": "https://via.placeholder.com/60",
                        "totalReturn": 45.2,
                        "totalTrades": 89,
                        "winRate": 0.78,
                        "followers": 1250,
                        "verified": True,
                        "rank": 1
                    },
                    {
                        "id": "trader_2", 
                        "username": "swing_master",
                        "avatar": "https://via.placeholder.com/60",
                        "totalReturn": 38.7,
                        "totalTrades": 67,
                        "winRate": 0.72,
                        "followers": 890,
                        "verified": True,
                        "rank": 2
                    },
                    {
                        "id": "trader_3",
                        "username": "day_trader_pro",
                        "avatar": "https://via.placeholder.com/60", 
                        "totalReturn": 32.1,
                        "totalTrades": 156,
                        "winRate": 0.68,
                        "followers": 567,
                        "verified": False,
                        "rank": 3
                    }
                ]
            }
        }
    
    # Handle swingSignals query
    if "swingSignals" in query_str:
        print("DEBUG: Processing swingSignals query")
        limit = variables.get("limit", 5)
        return {
            "data": {
                "swingSignals": [
                    {
                        "id": "signal_1",
                        "symbol": "AAPL",
                        "signalType": "BUY",
                        "confidence": 0.85,
                        "targetPrice": 195.00,
                        "stopLoss": 175.00,
                        "timeframe": "1-2 weeks",
                        "reasoning": "Strong earnings beat, bullish technical pattern",
                        "createdAt": "2025-01-28T10:00:00Z"
                    },
                    {
                        "id": "signal_2",
                        "symbol": "TSLA",
                        "signalType": "SELL",
                        "confidence": 0.72,
                        "targetPrice": 220.00,
                        "stopLoss": 260.00,
                        "timeframe": "3-5 days",
                        "reasoning": "Overbought conditions, resistance at $250",
                        "createdAt": "2025-01-28T09:30:00Z"
                    }
                ]
            }
        }
    
    # Handle availableBenchmarks query
    if "availableBenchmarks" in query_str:
        print("DEBUG: Processing availableBenchmarks query")
        return {
            "data": {
                "availableBenchmarks": ["SPY", "QQQ", "IWM", "VTI", "VEA", "VWO"]
            }
        }
    
    # Handle benchmarkSeries query
    if "benchmarkSeries" in query_str:
        print("DEBUG: Processing benchmarkSeries query")
        symbol = variables.get("symbol", "SPY")
        timeframe = variables.get("timeframe", "1D")
        return {
            "data": {
                "benchmarkSeries": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": [
                        {"timestamp": "2025-01-28T09:30:00Z", "price": 485.50},
                        {"timestamp": "2025-01-28T10:00:00Z", "price": 487.20},
                        {"timestamp": "2025-01-28T10:30:00Z", "price": 486.80},
                        {"timestamp": "2025-01-28T11:00:00Z", "price": 488.10},
                        {"timestamp": "2025-01-28T11:30:00Z", "price": 489.30},
                        {"timestamp": "2025-01-28T12:00:00Z", "price": 488.90},
                        {"timestamp": "2025-01-28T12:30:00Z", "price": 490.20},
                        {"timestamp": "2025-01-28T13:00:00Z", "price": 491.50},
                        {"timestamp": "2025-01-28T13:30:00Z", "price": 492.10},
                        {"timestamp": "2025-01-28T14:00:00Z", "price": 491.80}
                    ]
                }
            }
        }
    
    return {"data": {"message": "No matching GraphQL operation found"}}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Crypto Test Server...")
    print("📡 Server will be available at: http://127.0.0.1:8002")
    uvicorn.run(app, host="127.0.0.1", port=8002)
