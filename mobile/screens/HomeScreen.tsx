import React, { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
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
Image,
Modal,
} from 'react-native';
import { useApolloClient, useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import PortfolioGraph from '../components/PortfolioGraph';
import PortfolioHoldings from '../components/PortfolioHoldings';
import BasicRiskMetrics from '../components/BasicRiskMetrics';
import PortfolioComparison from '../components/PortfolioComparison';
import RealTimePortfolioService, { PortfolioMetrics } from '../services/RealTimePortfolioService';
import webSocketService, { PortfolioUpdate } from '../services/WebSocketService';
import UserProfileService, { ExtendedUserProfile } from '../services/UserProfileService';
import FinancialChatbotService from '../services/FinancialChatbotService';
// GraphQL Query for Portfolio Data
const GET_PORTFOLIO_METRICS = gql`
query GetPortfolioMetrics {
portfolioMetrics {
totalValue
totalCost
totalReturn
totalReturnPercent
holdings {
symbol
companyName
shares
currentPrice
totalValue
costBasis
returnAmount
returnPercent
sector
}
}
}
`;
const GET_ME = gql`
query GetMe {
me {
id
name
email
hasPremiumAccess
subscriptionTier
}
}
`;
// Types
interface ChatMsg {
id: string;
role: 'user' | 'assistant';
content: string;
}
const HomeScreen = ({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) => {
const client = useApolloClient();
// Portfolio data query with subtle optimization
const { data: portfolioData, loading: portfolioLoading, error: portfolioError } = useQuery(GET_PORTFOLIO_METRICS, {
errorPolicy: 'ignore',
fetchPolicy: 'cache-first', // Use cache when available
notifyOnNetworkStatusChange: false, // Reduce unnecessary re-renders
});
// User data query for premium status with subtle optimization
const { data: userData, loading: userLoading } = useQuery(GET_ME, {
errorPolicy: 'ignore',
fetchPolicy: 'cache-first', // Use cache when available
notifyOnNetworkStatusChange: false, // Reduce unnecessary re-renders
});
// User profile state
const [userProfile, setUserProfile] = useState<ExtendedUserProfile | null>(null);
const [profileLoading, setProfileLoading] = useState(true);
// State
// Live portfolio data from WebSocket
const [liveHoldings, setLiveHoldings] = useState<any[]>([]);
const [isLiveData, setIsLiveData] = useState(false);
const [liveTotalValue, setLiveTotalValue] = useState<number | null>(null);
const [liveTotalReturn, setLiveTotalReturn] = useState<number | null>(null);
const [liveTotalReturnPercent, setLiveTotalReturnPercent] = useState<number | null>(null);
// Chatbot state
const [chatOpen, setChatOpen] = useState(false);
const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
const [chatInput, setChatInput] = useState('');
const [chatSending, setChatSending] = useState(false);
const listRef = useRef<FlatList<ChatMsg>>(null);
// Debounced chat input for better performance
const [debouncedChatInput, setDebouncedChatInput] = useState('');
useEffect(() => {
const timer = setTimeout(() => {
setDebouncedChatInput(chatInput);
}, 300);
return () => clearTimeout(timer);
}, [chatInput]);
// Real portfolio data
const [realPortfolioData, setRealPortfolioData] = useState<PortfolioMetrics | null>(null);
// Load real portfolio data
useEffect(() => {
const loadRealPortfolioData = async () => {
try {
const portfolioData = await RealTimePortfolioService.getPortfolioData();
if (portfolioData) {
setRealPortfolioData(portfolioData);
}
} catch (error) {
console.error('Failed to load real portfolio data:', error);
}
};
loadRealPortfolioData();
}, []);
// Load user profile
useEffect(() => {
const loadUserProfile = async () => {
try {
const userProfileService = UserProfileService.getInstance();
const profile = await userProfileService.getProfile();
setUserProfile(profile);
} catch (error) {
console.error('Error loading user profile:', error);
} finally {
setProfileLoading(false);
}
};
loadUserProfile();
}, []);
// WebSocket setup for live portfolio updates
useEffect(() => {
const setupWebSocket = async () => {
try {
// Set up portfolio update callback
webSocketService.setCallbacks({
onPortfolioUpdate: (portfolio: PortfolioUpdate) => {
// Update live holdings data
setLiveHoldings(portfolio.holdings);
setIsLiveData(true);
// Update live portfolio totals
setLiveTotalValue(portfolio.totalValue);
setLiveTotalReturn(portfolio.totalReturn);
setLiveTotalReturnPercent(portfolio.totalReturnPercent);
}
});
// Connect to WebSocket
webSocketService.connect();
// Subscribe to portfolio updates
setTimeout(() => {
webSocketService.subscribeToPortfolio();
}, 1000);
} catch (error) {
console.error('Error setting up portfolio WebSocket in HomeScreen:', error);
}
};
setupWebSocket();
// Cleanup on unmount
return () => {
// Don't disconnect the shared WebSocket service
// as other components might be using it
};
}, []);
// -------- Chatbot --------
// -------- Chatbot --------
const quickPrompts = useMemo(() => [
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
], []);
// AI Response Generator using Financial Chatbot Service
const generateAIResponse = async (userInput: string): Promise<string> => {
try {
const chatbotService = FinancialChatbotService.getInstance();
return await chatbotService.processUserInput(userInput);
} catch (error) {
console.error('Error generating AI response:', error);
return `I apologize, but I encountered an error while processing your request. Please try again or ask a different question.`;
}
};
const openChat = () => {
setChatOpen(true);
if (chatMessages.length === 0) {
setChatMessages([
{
id: String(Date.now()),
role: 'assistant',
content:
' Welcome to your Financial AI Assistant!\n\nI can help you with:\n• Investment basics (ETFs, index funds, stocks)\n• Retirement planning (IRAs, 401(k)s)\n• Budgeting strategies (50/30/20 rule)\n• Risk management and diversification\n• Financial terminology and concepts\n\n This is educational information only. For personalized financial advice, consult a qualified financial advisor.\n\nTry a quick prompt below or ask me anything about personal finance!',
},
]);
}
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
// Failed to send message
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
// Failed to send message
const errorResponse: ChatMsg = {
id: String(Date.now() + 1),
role: 'assistant',
content: 'I apologize, but I encountered an error while processing your request. Please try again or ask a different question.',
};
setChatMessages(prev => [...prev, errorResponse]);
setChatSending(false);
}
};
// Memoized helper functions for personalization (performance optimization)
const getExperienceIcon = useCallback((level: string) => {
switch (level) {
case 'beginner': return 'book-open';
case 'intermediate': return 'trending-up';
case 'advanced': return 'bar-chart-2';
default: return 'user';
}
}, []);
const getUserStyleSummary = useCallback((profile: ExtendedUserProfile): string => {
const experience = profile.experienceLevel;
const risk = profile.riskTolerance;
if (experience === 'beginner' && risk === 'conservative') {
return 'Conservative Beginner - Focus on learning and low-risk investments';
} else if (experience === 'beginner' && risk === 'moderate') {
return 'Balanced Beginner - Ready to explore moderate risk investments';
} else if (experience === 'intermediate' && risk === 'aggressive') {
return 'Growth-Oriented Investor - Seeking higher returns with calculated risk';
} else if (experience === 'advanced' && risk === 'aggressive') {
return 'Sophisticated Investor - Advanced strategies and high-risk opportunities';
} else {
return 'Balanced Investor - Steady growth with moderate risk';
}
}, []);
// Memoized portfolio calculations for better performance
const portfolioValues = useMemo(() => {
const totalValue = realPortfolioData?.totalValue || (isLiveData && liveTotalValue ? liveTotalValue : (portfolioData?.portfolioMetrics?.totalValue || 14303.52));
const totalReturn = realPortfolioData?.totalReturn || (isLiveData && liveTotalReturn ? liveTotalReturn : (portfolioData?.portfolioMetrics?.totalReturn || 2145.53));
const totalReturnPercent = realPortfolioData?.totalReturnPercent || (isLiveData && liveTotalReturnPercent ? liveTotalReturnPercent : (portfolioData?.portfolioMetrics?.totalReturnPercent || 17.65));
return { totalValue, totalReturn, totalReturnPercent };
}, [realPortfolioData, isLiveData, liveTotalValue, liveTotalReturn, liveTotalReturnPercent, portfolioData]);
const portfolioHoldings = useMemo(() => {
return realPortfolioData?.holdings || (isLiveData && liveHoldings.length > 0 ? liveHoldings : portfolioData?.portfolioMetrics?.holdings);
}, [realPortfolioData, isLiveData, liveHoldings, portfolioData]);
// Memoized portfolio history for better performance
const portfolioHistory = useMemo(() => [
// 1 year ago (September 2023)
{ date: '2023-09-08', value: 10000 },
{ date: '2023-10-08', value: 10200 },
{ date: '2023-11-08', value: 10500 },
{ date: '2023-12-08', value: 10800 },
// 6 months ago (March 2024)
{ date: '2024-01-08', value: 11000 },
{ date: '2024-02-08', value: 11200 },
{ date: '2024-03-08', value: 11500 },
{ date: '2024-04-08', value: 11800 },
{ date: '2024-05-08', value: 12000 },
// 3 months ago (June 2024)
{ date: '2024-06-08', value: 12200 },
{ date: '2024-07-08', value: 12500 },
// 1 month ago (August 2024)
{ date: '2024-08-08', value: 12800 },
{ date: '2024-08-15', value: 12900 },
{ date: '2024-08-22', value: 13000 },
{ date: '2024-08-29', value: 13050 },
// Recent (September 2024)
{ date: '2024-09-01', value: 13100 },
{ date: '2024-09-08', value: 13100 },
], []);
return (
<SafeAreaView style={styles.container}>
{/* Content */}
<ScrollView
style={styles.content}
>
{/* Personalized Welcome Section */}
{userProfile && (
<View style={styles.welcomeSection}>
<View style={styles.welcomeHeader}>
<View style={styles.profileIcon}>
<Icon 
name={getExperienceIcon(userProfile.experienceLevel)} 
size={20} 
color="#FFFFFF" 
/>
</View>
<View style={styles.welcomeText}>
<Text style={styles.welcomeTitle}>
Welcome back, {userProfile.experienceLevel} investor!
</Text>
<Text style={styles.welcomeSubtitle}>
{getUserStyleSummary(userProfile)}
</Text>
</View>
</View>
{/* Quick Stats */}
<View style={styles.quickStats}>
<View style={styles.statItem}>
<Icon name="clock" size={16} color="#007AFF" />
<Text style={styles.statValue}>{userProfile.stats.totalLearningTime}m</Text>
<Text style={styles.statLabel}>Learning</Text>
</View>
<View style={styles.statItem}>
<Icon name="check-circle" size={16} color="#34C759" />
<Text style={styles.statValue}>{userProfile.stats.modulesCompleted}</Text>
<Text style={styles.statLabel}>Modules</Text>
</View>
<View style={styles.statItem}>
<Icon name="trending-up" size={16} color="#FF3B30" />
<Text style={styles.statValue}>{userProfile.stats.streakDays}</Text>
<Text style={styles.statLabel}>Streak</Text>
</View>
</View>
</View>
)}
{/* Portfolio Graph - First thing users see */}
<PortfolioGraph
totalValue={portfolioValues.totalValue}
totalReturn={portfolioValues.totalReturn}
totalReturnPercent={portfolioValues.totalReturnPercent}
onPress={() => {
// Navigate to portfolio details
navigateTo('PortfolioEducation', { 
clickedElement: 'chart',
totalValue: portfolioValues.totalValue,
totalReturn: portfolioValues.totalReturn,
totalReturnPercent: portfolioValues.totalReturnPercent
});
}}
/>
{/* Portfolio Holdings */}
{portfolioHoldings && portfolioHoldings.length > 0 && (
<PortfolioHoldings
holdings={portfolioHoldings}
onStockPress={(symbol) => {
// Navigate to stock detail or search
navigateTo('StockDetail', { symbol });
}}
/>
)}
{/* Basic Risk Metrics */}
{portfolioHoldings && portfolioHoldings.length > 0 && (
<BasicRiskMetrics
holdings={portfolioHoldings}
totalValue={portfolioValues.totalValue}
totalReturn={portfolioValues.totalReturn}
totalReturnPercent={portfolioValues.totalReturnPercent}
onNavigate={navigateTo}
hasPremiumAccess={userData?.me?.hasPremiumAccess || false}
/>
)}
{/* Portfolio Comparison */}
{portfolioHoldings && portfolioHoldings.length > 0 && (
<PortfolioComparison
totalValue={portfolioValues.totalValue}
totalReturn={portfolioValues.totalReturn}
totalReturnPercent={portfolioValues.totalReturnPercent}
portfolioHistory={portfolioHistory}
/>
)}
{/* Learning Paths Quick Access */}
<View style={styles.learningSection}>
<View style={styles.learningHeader}>
<View style={styles.learningHeaderLeft}>
<Icon name="book-open" size={20} color="#AF52DE" />
<Text style={styles.learningTitle}>Learn Investing</Text>
</View>
<TouchableOpacity 
style={styles.learningButton}
onPress={() => navigateTo('learning-paths')}
>
<Text style={styles.learningButtonText}>View All</Text>
<Icon name="chevron-right" size={16} color="#AF52DE" />
</TouchableOpacity>
</View>
<View style={styles.learningCards}>
<TouchableOpacity 
style={styles.learningCard}
onPress={() => navigateTo('learning-paths')}
>
<View style={styles.learningCardIcon}>
<Icon name="play-circle" size={24} color="#34C759" />
</View>
<View style={styles.learningCardContent}>
<Text style={styles.learningCardTitle}>Getting Started</Text>
<Text style={styles.learningCardDescription}>Learn the basics of investing</Text>
<Text style={styles.learningCardMeta}>5 modules • 25 min</Text>
</View>
<Icon name="chevron-right" size={16} color="#8E8E93" />
</TouchableOpacity>
<TouchableOpacity 
style={styles.learningCard}
onPress={() => navigateTo('learning-paths')}
>
<View style={styles.learningCardIcon}>
<Icon name="bar-chart-2" size={24} color="#007AFF" />
</View>
<View style={styles.learningCardContent}>
<Text style={styles.learningCardTitle}>Portfolio Management</Text>
<Text style={styles.learningCardDescription}>Optimize your investments</Text>
<Text style={styles.learningCardMeta}>4 modules • 20 min</Text>
</View>
<Icon name="chevron-right" size={16} color="#8E8E93" />
</TouchableOpacity>
</View>
</View>
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
// Personalized Welcome Section
welcomeSection: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginTop: 16,
marginBottom: 8,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
welcomeHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 16,
},
profileIcon: {
width: 40,
height: 40,
borderRadius: 20,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 12,
},
welcomeText: {
flex: 1,
},
welcomeTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
welcomeSubtitle: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
quickStats: {
flexDirection: 'row',
justifyContent: 'space-around',
paddingTop: 16,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
statItem: {
alignItems: 'center',
},
statValue: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 4,
marginBottom: 2,
},
statLabel: {
fontSize: 12,
color: '#8E8E93',
},
// Portfolio Card Fallback
portfolioCardFallback: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
alignItems: 'center',
},
fallbackTitle: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
marginBottom: 8,
},
fallbackValue: {
fontSize: 32,
fontWeight: '800',
color: '#1C1C1E',
marginBottom: 4,
},
fallbackSubtext: {
fontSize: 14,
color: '#8E8E93',
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
// Learning Section
learningSection: {
marginTop: 24,
marginBottom: 16,
},
learningHeader: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
marginBottom: 16,
paddingHorizontal: 16,
},
learningHeaderLeft: {
flexDirection: 'row',
alignItems: 'center',
gap: 8,
},
learningTitle: {
fontSize: 18,
fontWeight: '700',
color: '#1C1C1E',
},
learningButton: {
flexDirection: 'row',
alignItems: 'center',
gap: 4,
},
learningButtonText: {
fontSize: 14,
fontWeight: '600',
color: '#AF52DE',
},
learningCards: {
paddingHorizontal: 16,
gap: 12,
},
learningCard: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
flexDirection: 'row',
alignItems: 'center',
shadowColor: '#000',
shadowOffset: { width: 0, height: 1 },
shadowOpacity: 0.05,
shadowRadius: 2,
elevation: 1,
},
learningCardIcon: {
width: 48,
height: 48,
borderRadius: 12,
backgroundColor: '#F2F2F7',
justifyContent: 'center',
alignItems: 'center',
marginRight: 12,
},
learningCardContent: {
flex: 1,
},
learningCardTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
learningCardDescription: {
fontSize: 13,
color: '#8E8E93',
marginBottom: 4,
},
learningCardMeta: {
fontSize: 12,
color: '#8E8E93',
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
// Social Guide Button
socialGuideButton: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
socialGuideContent: {
flexDirection: 'row',
alignItems: 'center',
},
socialGuideIcon: {
width: 48,
height: 48,
borderRadius: 24,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
socialGuideText: {
flex: 1,
},
socialGuideTitle: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
socialGuideSubtitle: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
// Test User Button
testUserButton: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
testUserContent: {
flexDirection: 'row',
alignItems: 'center',
},
testUserIcon: {
width: 48,
height: 48,
borderRadius: 24,
backgroundColor: '#34C759',
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
testUserText: {
flex: 1,
},
testUserTitle: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
testUserSubtitle: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
// Search Test Button
searchTestButton: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
searchTestContent: {
flexDirection: 'row',
alignItems: 'center',
},
searchTestIcon: {
width: 48,
height: 48,
borderRadius: 24,
backgroundColor: '#FF9500',
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
searchTestText: {
flex: 1,
},
searchTestTitle: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
searchTestSubtitle: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
// Modal Styles
modalOverlay: {
position: 'absolute',
top: 0,
left: 0,
right: 0,
bottom: 0,
backgroundColor: 'rgba(0, 0, 0, 0.5)',
justifyContent: 'center',
alignItems: 'center',
zIndex: 1000,
},
modalContainer: {
backgroundColor: '#FFFFFF',
borderRadius: 20,
width: '90%',
height: '80%',
shadowColor: '#000',
shadowOffset: { width: 0, height: 10 },
shadowOpacity: 0.25,
shadowRadius: 20,
elevation: 10,
},
modalHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
padding: 20,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
modalTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
},
modalCloseButton: {
padding: 8,
},
});
export default memo(HomeScreen);