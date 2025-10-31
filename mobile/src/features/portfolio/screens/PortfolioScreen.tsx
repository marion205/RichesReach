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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { SecureMarketDataService } from '../../stocks/services/SecureMarketDataService';
import { GET_MY_PORTFOLIOS } from '../../../portfolioQueries';
import MilestonesTimeline, { Milestone } from '../../../components/MilestonesTimeline';
import MilestoneUnlockOverlay from '../../../components/MilestoneUnlockOverlay';
import { useNavigation } from '@react-navigation/native';
interface PortfolioScreenProps {
navigateTo?: (screen: string) => void;
}
const PortfolioScreen: React.FC<PortfolioScreenProps> = ({ navigateTo }) => {
const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  
  // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
  const [refreshing, setRefreshing] = useState(false);
  const [realTimePrices, setRealTimePrices] = useState<{ [key: string]: number }>({});
  const [loadingPrices, setLoadingPrices] = useState(false);
  const [celebrateTitle, setCelebrateTitle] = useState<string | null>(null);
  
  const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch } = useQuery(GET_MY_PORTFOLIOS, {
    errorPolicy: 'all', // Continue even if there are errors
    fetchPolicy: 'cache-and-network', // Use cache but also fetch fresh data
    notifyOnNetworkStatusChange: true,
  });
  
  const go = (name: string, params?: any) => {
    console.log('PortfolioScreen: Navigating to', name, params);
    try {
      if (navigation && (navigation as any).navigate) {
        console.log('PortfolioScreen: Using navigation.navigate');
        // For screens in the same stack, navigate directly
        (navigation as any).navigate(name as never, params as never);
        return;
      }
    } catch (error) {
      console.error('PortfolioScreen: Navigation error', error);
      // Try alternative navigation approach
      try {
        // If direct navigation fails, try nested navigation for InvestStack screens
        if (name === 'premium-analytics') {
          (navigation as any).navigate('Invest' as never, {
            screen: 'premium-analytics',
            params: params
          } as never);
          return;
        }
      } catch (nestedError) {
        console.error('PortfolioScreen: Nested navigation error', nestedError);
      }
    }
    console.log('PortfolioScreen: Using navigateTo fallback');
    navigateTo?.(name);
  };
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
// Log error for debugging but don't block rendering
if (portfolioError) {
  console.warn('Portfolio query error:', portfolioError);
  // Continue to render with demo data instead of showing error screen
}
// Fallback demo data when backend has no portfolios yet or on error
const demoPortfolios = [
{ name: 'Main', totalValue: 14303.52, holdingsCount: 3, holdings: [
  { id: 'h1', stock: { symbol: 'AAPL' }, shares: 10, averagePrice: 150, currentPrice: 180, totalValue: 1800 },
  { id: 'h2', stock: { symbol: 'MSFT' }, shares: 8, averagePrice: 230, currentPrice: 320, totalValue: 2560 },
  { id: 'h3', stock: { symbol: 'SPY' }, shares: 15, averagePrice: 380, currentPrice: 420, totalValue: 6300 },
]},
];
// Use data if available, otherwise fall back to demo data
const rawPortfolios = portfolioData?.myPortfolios?.portfolios || [];
const portfolios = (rawPortfolios.length > 0 && !portfolioError) ? rawPortfolios : demoPortfolios;
const totalValue = (portfolioData?.myPortfolios?.totalValue != null)
  ? portfolioData.myPortfolios.totalValue
  : portfolios.reduce((sum: number, p: any) => sum + (p.totalValue || 0), 0);
const totalPortfolios = (portfolioData?.myPortfolios?.totalPortfolios != null)
  ? portfolioData.myPortfolios.totalPortfolios
  : portfolios.length;

// Basic milestones (v1)
const milestones: Milestone[] = [
  { id: 'm1', title: 'First $1,000 invested', subtitle: 'A solid foundation' },
  { id: 'm2', title: 'First dividend received', subtitle: 'Income begins to compound' },
  { id: 'm3', title: 'Best month performance', subtitle: '+5% return month' },
];

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
      contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
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

{/* Milestones Timeline (placed outside grid for full width) */}
<MilestonesTimeline milestones={milestones} onCelebrate={(t) => setCelebrateTitle(t)} />

</View>
{/* Portfolio Actions */}
<View style={styles.actionsSection}>
<Text style={styles.actionsTitle}>Portfolio Management</Text>
<TouchableOpacity 
 style={styles.actionButton}
 onPress={() => go('portfolio-management')}
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
 onPress={() => go('stock')}
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
 onPress={() => go('ai-portfolio')}
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
 onPress={() => go('trading')}
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
 onPress={() => go('premium-analytics')}
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

      {/* Portfolio Health & Visualization Section */}
      <View style={styles.wellnessSection}>
        <Text style={styles.wellnessTitle}>Portfolio Health & Visualization</Text>
        
        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('wellness-dashboard')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="heart" size={24} color="#EF4444" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>Wellness Score Dashboard</Text>
              <Text style={styles.wellnessButtonDescription}>
                Dynamic portfolio health metrics and insights
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('ar-preview')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="camera" size={24} color="#10B981" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>AR Portfolio Preview</Text>
              <Text style={styles.wellnessButtonDescription}>
                Augmented reality portfolio visualization
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#8E8E93" />
          </View>
        </TouchableOpacity>
      </View>

      {/* Advanced Portfolio Features Section */}
      <View style={styles.wellnessSection}>
        <Text style={styles.wellnessTitle}>Advanced Portfolio Features</Text>
        
        <TouchableOpacity 
          style={styles.wellnessButton}
          onPress={() => go('blockchain-integration')}
        >
          <View style={styles.wellnessButtonContent}>
            <Icon name="link" size={24} color="#8B5CF6" />
            <View style={styles.wellnessText}>
              <Text style={styles.wellnessButtonTitle}>Blockchain Integration</Text>
              <Text style={styles.wellnessButtonDescription}>
                DeFi meets traditional finance - tokenize your portfolio
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
onPress={() => go('premium-analytics')}
>
<View style={styles.analyticsButtonContent}>
<Icon name="pie-chart" size={20} color="#007AFF" />
<Text style={styles.analyticsButtonText}>View Detailed Analytics</Text>
<Icon name="chevron-right" size={16} color="#8E8E93" />
</View>
</TouchableOpacity>
</View>
</ScrollView>
  {/* Celebration Overlay */}
  <MilestoneUnlockOverlay visible={!!celebrateTitle} title={celebrateTitle ?? ''} onClose={() => setCelebrateTitle(null)} />
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
  rowGap: 12,
  },
  watchlistItem: {
  width: '48%',
  backgroundColor: '#F8F9FA',
  borderRadius: 12,
  padding: 14,
  marginBottom: 12,
  alignItems: 'flex-start',
  },
  stockSymbol: {
  fontSize: 16,
  fontWeight: '700',
  color: '#1C1C1E',
  marginBottom: 2,
  },
  stockName: {
  fontSize: 12,
  color: '#8E8E93',
  textAlign: 'left',
  marginBottom: 6,
  },
priceContainer: {
  alignItems: 'flex-start',
},
stockPrice: {
  fontSize: 16,
  fontWeight: '700',
  color: '#34C759',
  lineHeight: 18,
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
  wellnessSection: {
    marginTop: 8,
    paddingHorizontal: 16,
  },
  wellnessTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  wellnessButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  wellnessButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  wellnessText: {
    flex: 1,
    marginLeft: 16,
  },
  wellnessButtonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  wellnessButtonDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
});
export default PortfolioScreen;
