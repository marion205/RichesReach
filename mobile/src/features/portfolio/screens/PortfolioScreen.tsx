import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
RefreshControl,
Alert,
TouchableOpacity,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { SecureMarketDataService } from '../../stocks/services/SecureMarketDataService';
import { GET_MY_PORTFOLIOS } from '../../../portfolioQueries';
interface PortfolioScreenProps {
navigateTo?: (screen: string) => void;
}
const PortfolioScreen: React.FC<PortfolioScreenProps> = ({ navigateTo }) => {
const [refreshing, setRefreshing] = useState(false);
const [realTimePrices, setRealTimePrices] = useState<{ [key: string]: number }>({});
const [loadingPrices, setLoadingPrices] = useState(false);
const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch } = useQuery(GET_MY_PORTFOLIOS);
// Fetch real-time prices when portfolio data changes
useEffect(() => {
if (portfolioData?.myPortfolios?.portfolios) {
const allHoldings = portfolioData.myPortfolios.portfolios.flatMap(p => p.holdings || []);
if (allHoldings.length > 0) {
fetchRealTimePrices(allHoldings);
}
}
}, [portfolioData]);
// Fetch real-time prices for portfolio holdings
const fetchRealTimePrices = async (holdings: any[]) => {
if (holdings.length === 0) return;
setLoadingPrices(true);
try {
const symbols = holdings.map(holding => holding.stock.symbol);
const service = SecureMarketDataService.getInstance();
const quotes = await service.fetchQuotes(symbols);
const prices: { [key: string]: number } = {};
quotes.forEach((quote) => {
if (quote.price > 0) {
prices[quote.symbol] = quote.price;
}
});
setRealTimePrices(prices);
} catch (error) {
console.error('Failed to fetch real-time prices for portfolio:', error);
} finally {
setLoadingPrices(false);
}
};
const onRefresh = async () => {
setRefreshing(true);
try {
await refetch();
} catch (error) {
// Error refreshing portfolio data
} finally {
setRefreshing(false);
}
};
if (portfolioLoading) {
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
</View>
<View style={styles.loadingContainer}>
<Icon name="refresh-cw" size={32} color="#34C759" />
<Text style={styles.loadingText}>Loading your portfolio...</Text>
</View>
</View>
);
}
if (portfolioError) {
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
</View>
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={48} color="#FF3B30" />
<Text style={styles.errorTitle}>Error Loading Portfolio</Text>
<Text style={styles.errorText}>
Unable to load your portfolio data. Please try again.
</Text>
<View style={styles.errorActions}>
<Text style={styles.errorActionText} onPress={onRefresh}>
Tap to retry
</Text>
</View>
</View>
</View>
);
}
const portfolios = portfolioData?.myPortfolios?.portfolios || [];
const totalValue = portfolioData?.myPortfolios?.totalValue || 0;
const totalPortfolios = portfolioData?.myPortfolios?.totalPortfolios || 0;

if (portfolios.length === 0) {
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
</View>
<View style={styles.emptyContainer}>
<Icon name="bar-chart-2" size={64} color="#9CA3AF" />
<Text style={styles.emptyTitle}>No Portfolios Yet</Text>
<Text style={styles.emptySubtitle}>
Start building your investment portfolio by adding stocks.
</Text>
<View style={styles.emptyActions}>
<Text 
style={styles.emptyActionText}
onPress={() => navigateTo?.('home')}
>
Go to Home to add stocks
</Text>
</View>
</View>
</View>
);
}
return (
<View style={styles.container}>
<View style={styles.header}>
<Icon name="bar-chart-2" size={24} color="#34C759" />
<Text style={styles.headerTitle}>Portfolio</Text>
</View>
<ScrollView
style={styles.content}
refreshControl={
<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
}
showsVerticalScrollIndicator={false}
>
{/* Portfolio Overview */}
<View style={styles.portfolioOverview}>
<Text style={styles.overviewTitle}>Your Portfolios</Text>
<Text style={styles.overviewSubtitle}>
{totalPortfolios} portfolios • ${totalValue.toLocaleString()} total value
{loadingPrices && ' • Loading prices...'}
</Text>
<View style={styles.watchlistGrid}>
{portfolios.slice(0, 3).map((portfolio: any) => (
<View key={portfolio.name} style={styles.watchlistItem}>
<Text style={styles.stockSymbol}>{portfolio.name}</Text>
<Text style={styles.stockName} numberOfLines={1}>
{portfolio.holdingsCount} holdings
</Text>
<View style={styles.priceContainer}>
<Text style={styles.stockPrice}>
${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0'}
</Text>
</View>
</View>
))}
</View>
{portfolios.length > 3 && (
<Text style={styles.moreStocks}>
+{portfolios.length - 3} more portfolios
</Text>
)}
</View>
{/* Portfolio Actions */}
<View style={styles.actionsSection}>
<Text style={styles.actionsTitle}>Portfolio Management</Text>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => navigateTo?.('portfolio-management')}
>
<View style={styles.actionContent}>
<Icon name="edit" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Manage Holdings</Text>
<Text style={styles.actionDescription}>
Add, edit, or remove stocks from your portfolio
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => navigateTo?.('stock')}
>
<View style={styles.actionContent}>
<Icon name="search" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Discover Stocks</Text>
<Text style={styles.actionDescription}>
Find new stocks to add to your watchlist
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => navigateTo?.('ai-portfolio')}
>
<View style={styles.actionContent}>
<Icon name="cpu" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>AI Recommendations</Text>
<Text style={styles.actionDescription}>
Get personalized stock recommendations
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => navigateTo?.('trading')}
>
<View style={styles.actionContent}>
<Icon name="dollar-sign" size={24} color="#34C759" />
<View style={styles.actionText}>
<Text style={styles.actionTitle}>Trading</Text>
<Text style={styles.actionDescription}>
Place buy/sell orders and manage your trades
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
<TouchableOpacity 
style={[styles.actionButton, { backgroundColor: '#FFF8E1' }]}
onPress={() => navigateTo?.('premium-analytics')}
>
<View style={styles.actionContent}>
<Icon name="star" size={24} color="#FFD700" />
<View style={styles.actionText}>
<Text style={[styles.actionTitle, { color: '#B8860B' }]}>Options Analysis</Text>
<Text style={styles.actionDescription}>
Advanced options strategies and market sentiment
</Text>
</View>
<Icon name="chevron-right" size={20} color="#8E8E93" />
</View>
</TouchableOpacity>
</View>

{/* Analytics Section */}
<View style={styles.analyticsSection}>
<Text style={styles.analyticsTitle}>Portfolio Analytics</Text>
<View style={styles.analyticsGrid}>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Total Return</Text>
<Text style={styles.analyticsValue}>+12.5%</Text>
<Text style={styles.analyticsSubtext}>This month</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Sharpe Ratio</Text>
<Text style={styles.analyticsValue}>1.4</Text>
<Text style={styles.analyticsSubtext}>Risk-adjusted</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Volatility</Text>
<Text style={styles.analyticsValue}>15.8%</Text>
<Text style={styles.analyticsSubtext}>Annualized</Text>
</View>
<View style={styles.analyticsCard}>
<Text style={styles.analyticsLabel}>Max Drawdown</Text>
<Text style={styles.analyticsValue}>-5.2%</Text>
<Text style={styles.analyticsSubtext}>Worst decline</Text>
</View>
</View>
<TouchableOpacity 
style={styles.analyticsButton}
onPress={() => navigateTo?.('premium-analytics')}
>
<View style={styles.analyticsButtonContent}>
<Icon name="pie-chart" size={20} color="#007AFF" />
<Text style={styles.analyticsButtonText}>View Detailed Analytics</Text>
<Icon name="chevron-right" size={16} color="#8E8E93" />
</View>
</TouchableOpacity>
</View>
</ScrollView>
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#f8f9fa',
paddingTop: 0,
},
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
fontSize: 20,
fontWeight: '600',
color: '#1C1C1E',
},
content: {
flex: 1,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
marginTop: 16,
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
errorTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
errorText: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 20,
},
errorActions: {
marginTop: 20,
},
errorActionText: {
fontSize: 16,
color: '#34C759',
fontWeight: '600',
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
emptyTitle: {
fontSize: 20,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
emptySubtitle: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 20,
marginBottom: 20,
},
emptyActions: {
marginTop: 20,
},
emptyActionText: {
fontSize: 16,
color: '#34C759',
fontWeight: '600',
},
portfolioOverview: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 20,
marginHorizontal: 16,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
overviewTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
overviewSubtitle: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 16,
},
watchlistGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
},
watchlistItem: {
width: '30%',
backgroundColor: '#F8F9FA',
borderRadius: 8,
padding: 12,
marginBottom: 12,
alignItems: 'center',
},
stockSymbol: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
stockName: {
fontSize: 12,
color: '#8E8E93',
textAlign: 'center',
marginBottom: 4,
},
priceContainer: {
alignItems: 'center',
},
stockPrice: {
fontSize: 14,
fontWeight: '600',
color: '#34C759',
},
livePriceIndicator: {
fontSize: 10,
fontWeight: '600',
color: '#34C759',
backgroundColor: '#E8F5E8',
paddingHorizontal: 4,
paddingVertical: 2,
borderRadius: 4,
textAlign: 'center',
marginTop: 2,
},
moreStocks: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
fontStyle: 'italic',
marginTop: 8,
},
actionsSection: {
marginTop: 8,
paddingHorizontal: 16,
},
actionsTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
actionButton: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
actionContent: {
flexDirection: 'row',
alignItems: 'center',
},
actionText: {
flex: 1,
marginLeft: 16,
},
actionTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
actionDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
analyticsSection: {
marginTop: 8,
paddingHorizontal: 16,
},
analyticsTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
analyticsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
marginBottom: 16,
},
analyticsCard: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
width: '48%',
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
analyticsLabel: {
fontSize: 12,
color: '#8E8E93',
fontWeight: '500',
marginBottom: 4,
},
analyticsValue: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 2,
},
analyticsSubtext: {
fontSize: 11,
color: '#8E8E93',
},
analyticsButton: {
backgroundColor: '#F0F8FF',
borderRadius: 12,
padding: 16,
borderWidth: 1,
borderColor: '#E3F2FD',
},
analyticsButtonContent: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
},
analyticsButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#007AFF',
marginLeft: 8,
marginRight: 8,
},
});
export default PortfolioScreen;
