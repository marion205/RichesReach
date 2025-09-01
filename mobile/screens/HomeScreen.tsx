import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
  FlatList,
  TextInput,
  Alert,
} from 'react-native';
import { useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import NewsCard from '../components/NewsCard';
import NewsCategories from '../components/NewsCategories';
import NewsPreferences from '../components/NewsPreferences';
import NewsAlerts from '../components/NewsAlerts';
import SavedArticles from '../components/SavedArticles';
import newsService, { NewsCategory, NewsArticle, NEWS_CATEGORIES } from '../services/newsService';






// Types
interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function HomeScreen({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) {
  const client = useApolloClient();
  
  // State
  const [refreshing, setRefreshing] = useState(false);

  // News state
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>(NEWS_CATEGORIES.ALL);
  const [newsCategories, setNewsCategories] = useState<Array<{ category: NewsCategory; count: number; label: string }>>([]);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);
  const [showSavedArticles, setShowSavedArticles] = useState(false);
  const [isPersonalized, setIsPersonalized] = useState(false);

  // Chatbot state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // Load news on component mount
  useEffect(() => {
    loadNews();
    loadNewsCategories();
  }, [selectedCategory, isPersonalized]);

  const loadNews = async () => {
    try {
      let news;
      if (isPersonalized) {
        news = await newsService.getPersonalizedNews();
      } else {
        news = await newsService.getRealTimeNews(selectedCategory);
      }
      setNewsArticles(news);
    } catch (error) {
      console.error('Error loading news:', error);
    }
  };

  const loadNewsCategories = async () => {
    try {
      const categories = await newsService.getNewsCategories();
      setNewsCategories(categories);
    } catch (error) {
      console.error('Error loading news categories:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNews();
    setRefreshing(false);
  };

  // -------- Chatbot --------



  // -------- Chatbot --------
  const quickPrompts = [
    'What is an ETF?',
    'Roth vs Traditional IRA',
    'Explain 50/30/20 budgeting',
    'How do index funds work?',
    'What is an expense ratio?',
    'Diversification basics',
    'Dollar-cost averaging',
    'How to analyze stocks?',
    'What is market cap?',
    'Emergency fund basics',
    'Credit score importance',
    'Compound interest explained',
    'Options trading basics',
    'How to trade options',
    'Trading fundamentals',
  ];

  // AI Response Generator with Real Financial Data
  const generateAIResponse = async (userInput: string): Promise<string> => {
    const input = userInput.toLowerCase();
    
    // Financial Education Database
    const financialKnowledge: { [key: string]: { title: string; content: string } } = {
      'etf': {
        title: 'Exchange-Traded Fund (ETF)',
        content: `An ETF is a type of investment fund that trades on stock exchanges, similar to stocks. ETFs hold assets such as stocks, commodities, or bonds and generally operate with an arbitrage mechanism designed to keep it trading close to its net asset value.

Key Benefits:
• Diversification across many assets
• Lower expense ratios than mutual funds
• Tax efficiency
• Intraday trading like stocks
• Transparency of holdings

Popular ETF Examples:
• SPY (S&P 500 ETF)
• QQQ (Nasdaq-100 ETF)
• VTI (Total Stock Market ETF)

ETFs are excellent for both beginners and experienced investors looking for cost-effective diversification.`
      },
      'roth vs traditional ira': {
        title: 'Roth IRA vs Traditional IRA',
        content: `Both IRAs offer tax advantages, but they work differently:

Traditional IRA:
• Tax-deductible contributions (reduce current year taxes)
• Tax-deferred growth
• Required minimum distributions (RMDs) starting at age 72
• Early withdrawal penalties before age 59½

Roth IRA:
• After-tax contributions (no current year tax deduction)
• Tax-free growth and withdrawals
• No RMDs during your lifetime
• Contributions can be withdrawn penalty-free anytime

Choose Traditional IRA if:
• You expect to be in a lower tax bracket in retirement
• You want immediate tax savings

Choose Roth IRA if:
• You expect to be in a higher tax bracket in retirement
• You want tax-free income in retirement
• You want flexibility with withdrawals`
      },
      'budgeting': {
        title: '50/30/20 Budgeting Rule',
        content: `The 50/30/20 rule is a simple budgeting framework:

50% - Needs (Essential Expenses):
• Housing (rent/mortgage)
• Utilities
• Food
• Transportation
• Insurance
• Minimum debt payments

30% - Wants (Discretionary Spending):
• Entertainment
• Dining out
• Shopping
• Hobbies
• Travel
• Subscriptions

20% - Savings & Debt:
• Emergency fund
• Retirement savings
• Investment contributions
• Extra debt payments
• Financial goals

Benefits:
• Simple to follow
• Ensures savings
• Balances needs vs wants
• Flexible framework

Remember: Adjust percentages based on your specific situation and goals.`
      },
      'index fund': {
        title: 'Index Funds Explained',
        content: `An index fund is a type of mutual fund or ETF designed to track the performance of a specific market index.

How They Work:
• Automatically track a market index (e.g., S&P 500)
• Buy all stocks in the index proportionally
• Rebalance automatically when index changes
• Low management fees (passive management)

Popular Indexes:
• S&P 500: 500 largest US companies
• Russell 2000: 2000 small-cap companies
• MSCI World: Global developed markets
• Bloomberg Barclays US Aggregate Bond Index

Advantages:
• Diversification
• Low costs
• Consistent performance
• Tax efficiency
• No manager risk

Index funds are excellent for long-term investing and are often recommended for retirement accounts.`
      },
      'expense ratio': {
        title: 'Expense Ratio Explained',
        content: `An expense ratio is the annual fee charged by investment funds to cover operating costs.

What It Covers:
• Management fees
• Administrative costs
• Marketing expenses
• Legal and accounting fees
• Custodian fees

How It's Calculated:
• Expressed as a percentage of assets
• Example: 0.50% = $5 per $1,000 invested annually
• Deducted automatically from fund returns

Typical Expense Ratios:
• Index funds: 0.03% - 0.20%
• Actively managed funds: 0.50% - 1.50%
• ETFs: 0.03% - 0.50%

Impact on Returns:
• Higher fees reduce long-term returns
• 1% fee over 30 years can reduce returns by 25%
• Always compare expense ratios when choosing funds

Lower is generally better, especially for long-term investments.`
      },
      'diversification': {
        title: 'Diversification Basics',
        content: `Diversification is spreading investments across different asset classes to reduce risk.

Asset Classes:
• Stocks (domestic, international, emerging markets)
• Bonds (government, corporate, municipal)
• Real estate (REITs, direct ownership)
• Commodities (gold, oil, agricultural)
• Cash and cash equivalents

Diversification Benefits:
• Reduces portfolio volatility
• Protects against single-asset risk
• Improves risk-adjusted returns
• Provides stability during market downturns

How to Diversify:
• Across asset classes
• Within asset classes (different sectors)
• Geographically (domestic vs international)
• By company size (large, mid, small cap)

Remember: "Don't put all your eggs in one basket." Diversification is key to long-term investment success.`
      },
      'dollar cost averaging': {
        title: 'Dollar-Cost Averaging (DCA)',
        content: `Dollar-cost averaging is investing a fixed amount regularly regardless of market conditions.

How It Works:
• Invest the same amount monthly/quarterly
• Buy more shares when prices are low
• Buy fewer shares when prices are high
• Automatically reduces average cost per share

Example:
• Month 1: $100 buys 10 shares at $10
• Month 2: $100 buys 8 shares at $12.50
• Month 3: $100 buys 20 shares at $5
• Average cost: $8.33 per share

Benefits:
• Reduces timing risk
• Emotional discipline
• Automates investing
• Smooths out market volatility

DCA is excellent for beginners and helps build wealth consistently over time.`
      },
      'stock analysis': {
        title: 'How to Analyze Stocks',
        content: `Stock analysis involves evaluating a company's fundamentals and market position.

Fundamental Analysis:
• Revenue and earnings growth
• Profit margins and profitability
• Debt levels and financial health
• Competitive advantages
• Management quality

Key Metrics:
• P/E Ratio (Price-to-Earnings)
• P/B Ratio (Price-to-Book)
• Debt-to-Equity Ratio
• Return on Equity (ROE)
• Free Cash Flow

Technical Analysis:
• Price trends and patterns
• Volume analysis
• Moving averages
• Support and resistance levels
• Momentum indicators

Remember: Combine both approaches and always do your own research before investing.`
      },
             'market cap': {
         title: 'Market Capitalization',
         content: `Market cap is the total value of a company's outstanding shares.

Calculation:
• Market Cap = Share Price × Number of Outstanding Shares

Market Cap Categories:
• Large Cap: $10+ billion (Apple, Microsoft, Amazon)
• Mid Cap: $2-10 billion (established growth companies)
• Small Cap: $300 million - $2 billion (growth potential)
• Micro Cap: $50-300 million (higher risk/reward)

Why It Matters:
• Indicates company size and stability
• Helps with portfolio diversification
• Influences investment strategy
• Risk assessment

Large caps are generally more stable, while small caps offer higher growth potential but with increased risk.`
       },
       'emergency fund': {
         title: 'Emergency Fund Basics',
         content: `An emergency fund is money set aside for unexpected expenses or financial emergencies.

How Much to Save:
• 3-6 months of essential expenses
• Consider job stability and family situation
• High-risk jobs: 6-12 months
• Dual-income households: 3-6 months

What It Covers:
• Job loss
• Medical emergencies
• Car repairs
• Home repairs
• Unexpected travel

Where to Keep It:
• High-yield savings account
• Money market account
• Easily accessible
• Separate from regular spending

Benefits:
• Financial security
• Prevents debt
• Reduces stress
• Provides options during crises

Start small and build gradually - even $1,000 can make a big difference!`
       },
       'credit score': {
         title: 'Credit Score Importance',
         content: `Your credit score is a three-digit number that lenders use to assess your creditworthiness.

Score Ranges:
• Excellent: 800-850
• Very Good: 740-799
• Good: 670-739
• Fair: 580-669
• Poor: 300-579

What Affects Your Score:
• Payment history (35%)
• Credit utilization (30%)
• Length of credit history (15%)
• Credit mix (10%)
• New credit inquiries (10%)

Why It Matters:
• Loan approval and interest rates
• Credit card applications
• Insurance premiums
• Rental applications
• Job opportunities (some employers check)

How to Improve:
• Pay bills on time
• Keep credit utilization below 30%
• Don't close old accounts
• Limit new credit applications
• Monitor your credit report

A good credit score can save you thousands in interest over your lifetime.`
       },
       'compound interest': {
         title: 'Compound Interest Explained',
         content: `Compound interest is when you earn interest on both your principal and accumulated interest.

How It Works:
• Year 1: $1,000 × 10% = $100 interest
• Year 2: $1,100 × 10% = $110 interest
• Year 3: $1,210 × 10% = $121 interest

The Power of Compounding:
• Time is your greatest ally
• Small amounts grow significantly over decades
• Early investing has massive advantages
• Consistent contributions amplify growth

Example: $100/month at 8% for 30 years
• Total invested: $36,000
• Final value: $150,000+
• Interest earned: $114,000+

Key Factors:
• Principal amount
• Interest rate
• Time period
• Frequency of compounding
• Regular contributions

Start early, invest consistently, and let compound interest work its magic!`
       },
       'options': {
         title: 'Options Trading Basics',
         content: `Options are financial contracts that give you the right (but not obligation) to buy or sell an asset at a specific price.

Two Main Types:
• Call Options: Right to BUY at strike price
• Put Options: Right to SELL at strike price

Key Terms:
• Strike Price: Price at which you can exercise the option
• Expiration Date: When the option expires
• Premium: Cost to buy the option
• In-the-Money: Option has intrinsic value
• Out-of-the-Money: Option has no intrinsic value

Basic Strategies:
• Covered Call: Sell calls against stock you own
• Protective Put: Buy puts to protect stock positions
• Long Call: Bet on stock price increase
• Long Put: Bet on stock price decrease

Risk Considerations:
• Options can expire worthless
• Unlimited loss potential on some strategies
• Time decay works against you
• Requires understanding of Greeks (delta, gamma, theta, vega)

Important: Options are complex and risky. Start with paper trading and education before using real money.`
       },
       'trade options': {
         title: 'How to Trade Options',
         content: `Options trading requires education, practice, and risk management. Here's a step-by-step approach:

Step 1: Education
• Learn options terminology and mechanics
• Understand risk/reward profiles
• Study different strategies
• Practice with paper trading

Step 2: Account Setup
• Open a brokerage account that supports options
• Get options trading approval (Level 1-4)
• Start with Level 1 (buying calls/puts)

Step 3: Strategy Selection
• Covered Calls: Lower risk, income generation
• Protective Puts: Insurance for stock positions
• Long Calls/Puts: Directional bets
• Spreads: Limited risk, defined profit/loss

Step 4: Risk Management
• Never risk more than you can afford to lose
• Use stop-loss orders
• Diversify across different strategies
• Avoid complex strategies initially

Step 5: Execution
• Start with liquid options (high volume)
• Check bid/ask spreads
• Consider time decay impact
• Monitor positions regularly

Remember: Options are advanced instruments. Master the basics before complex strategies.`
       },
       'trading': {
         title: 'Trading Fundamentals',
         content: `Trading involves buying and selling financial instruments to profit from price movements.

Types of Trading:
• Day Trading: Buy/sell within same day
• Swing Trading: Hold positions for days/weeks
• Position Trading: Hold for weeks/months
• Scalping: Very short-term trades

Essential Skills:
• Technical Analysis: Charts, patterns, indicators
• Fundamental Analysis: Company financials, news
• Risk Management: Position sizing, stop-losses
• Psychology: Emotional control, discipline

Risk Management Rules:
• Never risk more than 1-2% per trade
• Use stop-loss orders
• Don't chase losses
• Keep position sizes reasonable

Trading vs Investing:
• Trading: Short-term, active management
• Investing: Long-term, buy-and-hold
• Trading requires more time and attention
• Both require education and practice

Start with paper trading to practice strategies without risking real money.`
       }
    };

    // Check for exact matches first
    for (const [key, data] of Object.entries(financialKnowledge)) {
      if (input.includes(key)) {
        return `${data.title}\n\n${data.content}\n\n💡 This is educational information only. For personalized financial advice, consult a qualified financial advisor.`;
      }
    }

    // Check for partial matches and synonyms
    const synonyms: { [key: string]: string[] } = {
      'options': ['option', 'trading options', 'trade options', 'options trading', 'how to trade options'],
      'etf': ['etfs', 'exchange traded fund', 'exchange traded funds'],
      'ira': ['individual retirement account', 'roth ira', 'traditional ira'],
      'budgeting': ['budget', '50/30/20', 'fifty thirty twenty'],
      'index fund': ['index funds', 'index investing'],
      'expense ratio': ['expense ratios', 'fund fees', 'management fees'],
      'diversification': ['diversify', 'diversified'],
      'dollar cost averaging': ['dca', 'dollar cost average'],
      'stock analysis': ['analyze stocks', 'stock research', 'how to analyze stocks'],
      'market cap': ['market capitalization', 'market value'],
      'emergency fund': ['emergency savings', 'rainy day fund'],
      'credit score': ['credit scores', 'credit rating'],
      'compound interest': ['compounding', 'compound growth'],
      'trading': ['trade', 'day trading', 'swing trading']
    };

    // Check for synonyms and related terms
    for (const [key, synonymList] of Object.entries(synonyms)) {
      if (synonymList.some(synonym => input.includes(synonym)) && financialKnowledge[key]) {
        const data = financialKnowledge[key];
        return `${data.title}\n\n${data.content}\n\n💡 This is educational information only. For personalized financial advice, consult a qualified financial advisor.`;
      }
    }

    // Check for partial matches
    for (const [key, data] of Object.entries(financialKnowledge)) {
      if (key.includes(input) || input.includes(key)) {
        return `${data.title}\n\n${data.content}\n\n💡 This is educational information only. For personalized financial advice, consult a qualified financial advisor.`;
      }
    }

    // General financial guidance for other questions
    return `I understand you're asking about "${userInput}". This is a great question about personal finance!

While I can provide general educational information, remember that this is not financial advice. For personalized guidance, consider consulting with a qualified financial advisor.

Some topics I can help with:
• Investment basics (ETFs, index funds, stocks)
• Retirement planning (IRAs, 401(k)s)
• Budgeting and saving strategies
• Risk management and diversification
• Financial terminology and concepts

Feel free to ask about any of these topics or try one of the quick prompts above!`;
  };

  const openChat = () => {
    setChatOpen(true);
    if (chatMessages.length === 0) {
      setChatMessages([
        {
          id: String(Date.now()),
          role: 'assistant',
          content:
            '👋 Welcome to your Financial AI Assistant!\n\nI can help you with:\n• Investment basics (ETFs, index funds, stocks)\n• Retirement planning (IRAs, 401(k)s)\n• Budgeting strategies (50/30/20 rule)\n• Risk management and diversification\n• Financial terminology and concepts\n\n💡 This is educational information only. For personalized financial advice, consult a qualified financial advisor.\n\nTry a quick prompt below or ask me anything about personal finance!',
        },
      ]);
    }
    setTimeout(() => listRef.current?.scrollToEnd?.({ animated: false }), 0);
  };

  const closeChat = () => {
    setChatOpen(false);
    setChatInput('');
    setChatSending(false);
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatInput('');
  };

  const handleQuickPrompt = async (prompt: string) => {
    const userMessage: ChatMsg = {
      id: String(Date.now()),
      role: 'user',
      content: prompt,
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatSending(true);

    try {
      const response = await generateAIResponse(prompt);
      const aiResponse: ChatMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response,
      };
      setChatMessages(prev => [...prev, aiResponse]);
      setChatSending(false);
      setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorResponse: ChatMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again or ask a different question.',
      };
      setChatMessages(prev => [...prev, errorResponse]);
      setChatSending(false);
    }
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || chatSending) return;

    const userMessage: ChatMsg = {
      id: String(Date.now()),
      role: 'user',
      content: chatInput.trim(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatSending(true);

    try {
      const response = await generateAIResponse(userMessage.content);
      const aiResponse: ChatMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response,
      };
      setChatMessages(prev => [...prev, aiResponse]);
      setChatSending(false);
      setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorResponse: ChatMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again or ask a different question.',
      };
      setChatMessages(prev => [...prev, errorResponse]);
      setChatSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="home" size={24} color="#34C759" />
        <Text style={styles.headerTitle}>Financial News</Text>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Welcome Message */}
        <View style={styles.welcomeContainer}>
          <Icon name="home" size={48} color="#34C759" />
          <Text style={styles.welcomeTitle}>Welcome to RichesReach! 📰</Text>
          <Text style={styles.welcomeSubtitle}>
            Stay informed with the latest financial news and get personalized financial education.
          </Text>
        </View>

        {/* News Section */}
        <View style={styles.newsSection}>
          <View style={styles.newsHeader}>
            <View style={styles.newsHeaderLeft}>
              <Icon name="rss" size={20} color="#34C759" />
              <Text style={styles.newsTitle}>Financial News</Text>
            </View>
            <View style={styles.newsHeaderRight}>
              <TouchableOpacity 
                style={styles.savedButton}
                onPress={() => setShowSavedArticles(true)}
              >
                <Icon name="bookmark" size={16} color="#5856D6" />
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.alertsButton}
                onPress={() => setShowAlerts(true)}
              >
                <Icon name="bell" size={16} color="#FF9500" />
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.personalizeButton}
                onPress={() => setIsPersonalized(!isPersonalized)}
              >
                <Icon 
                  name={isPersonalized ? "user-check" : "user"} 
                  size={16} 
                  color={isPersonalized ? "#34C759" : "#8E8E93"} 
                />
                <Text style={[
                  styles.personalizeText,
                  isPersonalized && styles.personalizeTextActive
                ]}>
                  {isPersonalized ? 'Personal' : 'All'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.preferencesButton}
                onPress={() => setShowPreferences(true)}
              >
                <Icon name="settings" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          {/* News Categories */}
          {newsCategories.length > 0 && (
            <NewsCategories
              selectedCategory={selectedCategory}
              onCategorySelect={setSelectedCategory}
              categories={newsCategories}
            />
          )}

          <FlatList
            data={newsArticles}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <NewsCard 
                news={item} 
                onSave={newsService.saveArticle}
                onUnsave={newsService.unsaveArticle}
                showSaveButton={true}
              />
            )}
            horizontal={false}
            showsVerticalScrollIndicator={false}
            scrollEnabled={false}
          />
        </View>

        {/* News Preferences Modal */}
        <NewsPreferences
          visible={showPreferences}
          onClose={() => setShowPreferences(false)}
          onPreferencesUpdated={() => {
            loadNews();
            loadNewsCategories();
          }}
        />

        {/* News Alerts Modal */}
        <NewsAlerts
          visible={showAlerts}
          onClose={() => setShowAlerts(false)}
        />

        {/* Saved Articles Modal */}
        <SavedArticles
          visible={showSavedArticles}
          onClose={() => setShowSavedArticles(false)}
        />
      </ScrollView>

      {/* Chatbot Floating Button */}
      <TouchableOpacity style={styles.chatButton} onPress={openChat}>
        <Icon name="message-circle" size={24} color="#fff" />
      </TouchableOpacity>

      {/* Chatbot Modal */}
      {chatOpen && (
        <View style={styles.chatModal}>
          <View style={styles.chatHeader}>
            <View style={styles.chatTitleContainer}>
              <Icon name="zap" size={20} color="#00cc99" style={styles.chatTitleIcon} />
              <Text style={styles.chatTitle}>Financial Education Assistant</Text>
            </View>
            <View style={styles.chatHeaderActions}>
              <TouchableOpacity onPress={clearChat} style={styles.chatActionButton}>
                <Icon name="trash-2" size={16} color="#666" />
              </TouchableOpacity>
              <TouchableOpacity onPress={closeChat} style={styles.chatCloseButton}>
                <Icon name="x" size={20} color="#666" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Quick Prompts */}
          <View style={styles.quickPromptsContainer}>
            <FlatList
              data={quickPrompts}
              keyExtractor={(item, index) => `prompt-${index}`}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.quickPromptButton}
                  onPress={() => handleQuickPrompt(item)}
                >
                  <Text style={styles.quickPromptText}>{item}</Text>
                </TouchableOpacity>
              )}
              horizontal={true}
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.quickPromptsContent}
            />
          </View>

          {/* Chat Messages */}
          <FlatList
            ref={listRef}
            data={chatMessages}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={[
                styles.chatMessage,
                item.role === 'user' ? styles.userMessage : styles.assistantMessage
              ]}>
                <Text style={[
                  styles.chatMessageText,
                  item.role === 'user' ? styles.userMessageText : styles.assistantMessageText
                ]}>
                  {item.content}
                </Text>
              </View>
            )}
            style={styles.chatMessages}
            showsVerticalScrollIndicator={false}
            showsHorizontalScrollIndicator={false}
            horizontal={false}
            nestedScrollEnabled={true}
          />

          {/* Chat Input */}
          <View style={styles.chatInputContainer}>
            <TextInput
              style={styles.chatInput}
              placeholder="Ask about personal finance..."
              value={chatInput}
              onChangeText={setChatInput}
              multiline
              maxLength={500}
            />
            <TouchableOpacity
              style={[styles.chatSendButton, !chatInput.trim() && styles.chatSendButtonDisabled]}
              onPress={sendMessage}
              disabled={!chatInput.trim() || chatSending}
            >
              <Icon 
                name={chatSending ? "refresh-cw" : "send"} 
                size={20} 
                color={chatInput.trim() ? "#fff" : "#ccc"} 
              />
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },

  // Welcome Section
  welcomeContainer: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
  },

  // Summary Stats
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#fff',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },

  // Content
  content: {
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 30,
  },
  emptyButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  emptyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 15,
    marginBottom: 30,
  },
  emptySecondaryButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#00cc99',
  },
  emptySecondaryButtonText: {
    color: '#00cc99',
    fontSize: 14,
    fontWeight: '500',
  },
  emptyTips: {
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    width: '100%',
  },
  emptyTipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  emptyTipsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
    lineHeight: 20,
  },

  // News Section
  newsSection: {
    marginTop: 24,
    marginBottom: 16,
  },
  newsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  newsHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  newsHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  newsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  personalizeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  personalizeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  personalizeTextActive: {
    color: '#34C759',
  },
  savedButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  alertsButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  preferencesButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
  },

  // Watchlist Section
  watchlistSection: {
    backgroundColor: '#fff',
    marginHorizontal: 15,
    marginVertical: 10,
    borderRadius: 12,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  watchlistHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  watchlistTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  stockCount: {
    fontSize: 14,
    color: '#666',
  },
  watchlistDescription: {
    fontSize: 14,
    color: '#555',
    marginBottom: 15,
  },

  // Stock Card
  stockCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  stockInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  companyName: {
    fontSize: 14,
    color: '#333',
    marginTop: 2,
  },
  sector: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  stockMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
    marginBottom: 10,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  notesContainer: {
    marginTop: 10,
    marginBottom: 10,
  },
  notesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 13,
    color: '#555',
    lineHeight: 18,
  },
  targetContainer: {
    marginTop: 10,
    marginBottom: 10,
  },
  targetLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00cc99',
  },



  // Error
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#f8f9fa',
  },
  errorText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Chatbot Styles
  chatButton: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: '#00cc99',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  chatModal: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    padding: 20,
    paddingTop: 60, // Account for status bar
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 10,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  chatTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chatTitleIcon: {
    marginRight: 8,
  },
  chatTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  chatHeaderActions: {
    flexDirection: 'row',
  },
  chatActionButton: {
    marginLeft: 10,
  },
  chatCloseButton: {
    marginLeft: 10,
  },
  quickPromptsContainer: {
    marginBottom: 10,
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  quickPromptsContent: {
    paddingHorizontal: 4,
    gap: 8,
  },
  quickPromptButton: {
    backgroundColor: '#F0F8FF',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 18,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    minWidth: 120,
  },
  quickPromptText: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  chatMessages: {
    flex: 1,
    marginBottom: 8,
    paddingHorizontal: 0,
  },
  chatMessage: {
    minWidth: '90%',
    maxWidth: '120%',
    padding: 10,
    borderRadius: 10,
    marginBottom: 8,
    marginHorizontal: 4,
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#00cc99',
    borderBottomRightRadius: 0,
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f8f9fa',
    borderBottomLeftRadius: 0,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  chatMessageText: {
    fontSize: 15,
    lineHeight: 20,
    color: '#fff',
  },
  userMessageText: {
    color: '#fff',
    fontSize: 15,
    lineHeight: 20,
  },
  assistantMessageText: {
    color: '#333',
    fontSize: 15,
    lineHeight: 20,
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    paddingTop: 8,
    backgroundColor: '#fff',
  },
  chatInput: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: '#F8F9FA',
    fontSize: 14,
    color: '#333',
    marginRight: 8,
    minHeight: 36,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  chatSendButton: {
    backgroundColor: '#00cc99',
    padding: 8,
    borderRadius: 18,
  },
  chatSendButtonDisabled: {
    backgroundColor: '#ccc',
  },
});