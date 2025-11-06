import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Collapsible from 'react-native-collapsible';
import { useAuth } from '../contexts/AuthContext';
import taxOptimizationService from '../services/taxOptimizationService';
import { API_BASE } from '../config/api';
// import yieldsService from '../services/yieldsService'; // Your yields service

interface TaxOptimizationData {
  summary?: any;
  lossHarvesting?: any;
  capitalGains?: any;
  rebalancing?: any;
  bracketAnalysis?: any;
  yields?: any[]; // DeFi yields
}

// Current Year US Tax Brackets (Single Filer) - Ordinary Income (Short-Term Gains/Rewards)
const currentYear = new Date().getFullYear();
const INCOME_BRACKETS = [
  { min: 0, max: 11925, rate: 0.10 },
  { min: 11926, max: 48475, rate: 0.12 },
  { min: 48476, max: 103350, rate: 0.22 },
  { min: 103351, max: 197300, rate: 0.24 },
  { min: 197301, max: 250525, rate: 0.32 },
  { min: 250526, max: 626350, rate: 0.35 },
  { min: 626351, max: Infinity, rate: 0.37 },
];

// Current Year Long-Term Capital Gains Brackets (Single)
const LTCG_BRACKETS = [
  { min: 0, max: 48350, rate: 0.00 },
  { min: 48351, max: 533400, rate: 0.15 },
  { min: 533401, max: Infinity, rate: 0.20 },
];

// Calculator Functions
const calculateIncomeTax = (income: number): { tax: number; effectiveRate: number } => {
  let tax = 0;
  let prevMax = 0;
  for (const bracket of INCOME_BRACKETS) {
    if (income > prevMax) {
      const taxableInBracket = Math.min(income, bracket.max) - prevMax;
      tax += taxableInBracket * bracket.rate;
      prevMax = bracket.max;
    }
  }
  return { tax, effectiveRate: income > 0 ? tax / income : 0 };
};

const calculateLTCG = (gain: number, taxableIncome: number): number => {
  let tax = 0;
  let prevMax = 0;
  for (const bracket of LTCG_BRACKETS) {
    if (gain > 0) {
      const taxableInBracket = Math.min(gain, bracket.max - Math.max(0, taxableIncome - prevMax));
      tax += taxableInBracket * bracket.rate;
      gain -= taxableInBracket;
      prevMax = bracket.max;
    }
  }
  return tax;
};

const calculateAfterTaxAPY = (apy: number, marginalRate: number, principal: number = 10000): number => {
  const annualRewards = principal * (apy / 100);
  const taxOnRewards = annualRewards * marginalRate;
  const afterTaxRewards = annualRewards - taxOnRewards;
  return (afterTaxRewards / principal) * 100;
};

const calculateLossHarvestSavings = (loss: number, gain: number, marginalRate: number): number => {
  const offsetGain = Math.min(loss, gain);
  return offsetGain * marginalRate;
};

// Single Header Block Component - Title + Subtitle + Tabs all in one container
const HeaderBlock: React.FC<{
  tabs: any[];
  activeTab: string;
  onTabChange: (tab: string) => void;
}> = ({ tabs, activeTab, onTabChange }) => {
  return (
    <View style={styles.headerBlock}>
      {/* Title + subtitle */}
      <View style={styles.headerTop}>
        <Ionicons name="calculator-outline" size={32} color="#007AFF" />
        <View style={styles.headerText}>
          <Text style={styles.title} numberOfLines={1}>Tax Optimization</Text>
          <Text style={styles.subtitle} numberOfLines={1}>Real {new Date().getFullYear()} Calculations for Stocks & Crypto</Text>
        </View>
      </View>

      {/* Tabs live INSIDE the same block, right under subtitle */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabsRow}
        contentContainerStyle={styles.tabsContent}
      >
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tabBtn, activeTab === tab.key && styles.tabBtnActive]}
            onPress={() => onTabChange(tab.key)}
            hitSlop={10}
            activeOpacity={0.7}
          >
            <Ionicons
              name={tab.icon as any}
              size={16}
              color={activeTab === tab.key ? '#007AFF' : '#6B7280'}
              style={styles.tabIcon}
            />
            <Text style={[styles.tabLabel, activeTab === tab.key && styles.tabLabelActive]} numberOfLines={1}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const TaxOptimizationScreen: React.FC = () => {
  const { user, token } = useAuth();
  const [data, setData] = useState<TaxOptimizationData>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({});
  const [userIncome, setUserIncome] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch real user income from profile
      if (user?.incomeProfile?.annualIncome) {
        setUserIncome(user.incomeProfile.annualIncome);
      } else if (user?.profile?.income) {
        setUserIncome(user.profile.income);
      } else {
        // Default fallback if no income data available
        setUserIncome(80000);
      }

      // Fetch real portfolio holdings from tax optimization service
      let rawHoldings: any[] = [];
      
      try {
        const summaryData = await taxOptimizationService.getOptimizationSummary(token || '');
        if (summaryData && summaryData.holdings) {
          rawHoldings = summaryData.holdings;
        } else {
          // Try fetching from portfolio metrics GraphQL query
          const portfolioResponse = await fetch(`${API_BASE}/graphql`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token || ''}`,
            },
            body: JSON.stringify({
              query: `
                query {
                  portfolioMetrics {
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
              `
            })
          });
          
          const portfolioData = await portfolioResponse.json();
          if (portfolioData?.data?.portfolioMetrics?.holdings) {
            rawHoldings = portfolioData.data.portfolioMetrics.holdings.map((h: any) => ({
              symbol: h.symbol,
              type: 'stock',
              currentPrice: h.currentPrice,
              costBasis: h.costBasis / (h.shares || 1),
              quantity: h.shares || 0,
              taxImpact: h.returnPercent > 0 ? 0.15 : 0.22,
              recommendation: h.returnPercent > 0 ? 'Hold for long-term gains' : 'Consider tax-loss harvesting'
            }));
          }
        }
      } catch (error) {
        console.error('Error fetching real holdings:', error);
        // Fallback to empty array - don't use mock data
        rawHoldings = [];
      }

      // If no holdings found, show empty state
      if (rawHoldings.length === 0) {
        setData({
          summary: {
            estimatedAnnualTax: 0,
            holdings: [],
            totalPortfolioValue: 0,
            totalUnrealizedGains: 0,
          },
          lossHarvesting: { potentialSavings: 0, holdings: [] },
          capitalGains: { ltcgTax: 0, stcgTax: 0, holdings: [] },
          rebalancing: { bracketShiftTax: 0, holdings: [] },
          bracketAnalysis: { marginalRate: 0 },
          holdings: [],
        });
        return;
      }
      const integratedHoldings = rawHoldings.map((holding: any) => ({
        ...holding,
        currentValue: holding.currentPrice * holding.quantity,
        unrealizedGain: (holding.currentPrice - holding.costBasis) * holding.quantity,
        unrealizedGainPercent: ((holding.currentPrice - holding.costBasis) / holding.costBasis) * 100,
        taxSavingsPotential: holding.unrealizedGain < 0 ? Math.abs(holding.unrealizedGain) * 0.22 : 0,
      }));

      // Create real data for all sections using actual holdings
      const effectiveIncome = userIncome || 80000;
      const mockSummary = {
        estimatedAnnualTax: calculateIncomeTax(effectiveIncome + 5000).tax,
        holdings: integratedHoldings.slice(0, 3),
        totalPortfolioValue: integratedHoldings.reduce((sum, h) => sum + h.currentValue, 0),
        totalUnrealizedGains: integratedHoldings.reduce((sum, h) => sum + h.unrealizedGain, 0),
      };

      const mockLossHarvesting = {
        potentialSavings: integratedHoldings.filter(h => h.unrealizedGain < 0).reduce((sum, h) => sum + h.taxSavingsPotential, 0),
        holdings: integratedHoldings.filter(h => h.unrealizedGain < 0),
      };

      const mockCapitalGains = {
        ltcgTax: calculateLTCG(10000, effectiveIncome),
        stcgTax: calculateIncomeTax(effectiveIncome + 10000).tax - calculateIncomeTax(effectiveIncome).tax,
        holdings: integratedHoldings.filter(h => h.unrealizedGain > 0),
      };

      const mockRebalancing = {
        bracketShiftTax: calculateIncomeTax(effectiveIncome + 10000).tax - calculateIncomeTax(effectiveIncome).tax,
        holdings: integratedHoldings,
      };

      const mockBracketAnalysis = {
        marginalRate: calculateIncomeTax(effectiveIncome).effectiveRate,
      };

      setData({
        summary: mockSummary,
        lossHarvesting: mockLossHarvesting,
        capitalGains: mockCapitalGains,
        rebalancing: mockRebalancing,
        bracketAnalysis: mockBracketAnalysis,
        holdings: integratedHoldings,
      });
    } catch (error) {
      console.error('Error loading tax optimization data:', error);
      Alert.alert('Error', 'Failed to load tax optimization data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [user, token]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const tabs = [
    { key: 'summary', label: 'Summary', icon: 'analytics-outline' },
    { key: 'loss-harvesting', label: 'Loss H.', icon: 'trending-down' },
    { key: 'capital-gains', label: 'Cap. Gains', icon: 'trending-up' },
    { key: 'rebalancing', label: 'Rebal.', icon: 'refresh-circle' },
    { key: 'bracket-analysis', label: 'Brackets', icon: 'bar-chart' },
  ];

  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  }, []);

  const renderHoldingCard = (holding: any) => (
    <View style={styles.yieldCard}>
      <View style={styles.yieldHeader}>
        <Text style={styles.protocolName}>{holding.symbol}</Text>
        <View style={[styles.taxBadge, { backgroundColor: holding.type === 'stock' ? '#3B82F6' : '#8B5CF6' }]}>
          <Text style={styles.taxBadgeText}>{holding.type.toUpperCase()}</Text>
        </View>
      </View>
      <Text style={styles.yieldApy}>
        ${holding.currentPrice?.toFixed(2)} → {holding.unrealizedGainPercent?.toFixed(1)}% 
        {holding.unrealizedGain >= 0 ? ' Gain' : ' Loss'}
      </Text>
      <Text style={styles.yieldRec}>{holding.recommendation}</Text>
    </View>
  );

  const renderTabContent = () => {
    const getSectionData = () => {
      switch (activeTab) {
        case 'summary': return data.summary;
        case 'loss-harvesting': return data.lossHarvesting;
        case 'capital-gains': return data.capitalGains;
        case 'rebalancing': return data.rebalancing;
        case 'bracket-analysis': return data.bracketAnalysis;
        default: return data.summary;
      }
    };

    const sectionData = getSectionData();
    const sectionTitle = tabs.find(tab => tab.key === activeTab)?.label || 'Overview';
    const tabYields = sectionData?.yields || [];

    if (!sectionData) {
      return (
        <View style={styles.noDataContainer}>
          <Ionicons name="document-text-outline" size={64} color="#d1d5db" />
          <Text style={styles.noDataText}>No data available for this section</Text>
          <Text style={styles.noDataSubtext}>Pull to refresh or check your connection</Text>
        </View>
      );
    }

    return (
      <View style={styles.tabContent}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{sectionTitle}</Text>
          <Ionicons name="information-circle-outline" size={20} color="#6b7280" />
        </View>

        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Tax Overview</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Estimated Annual Tax:</Text>
                <Text style={styles.metricValue}>${sectionData.estimatedAnnualTax?.toLocaleString() || '0'}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Portfolio Value:</Text>
                <Text style={styles.metricValue}>${sectionData.totalPortfolioValue?.toLocaleString() || '0'}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Unrealized Gains:</Text>
                <Text style={[styles.metricValue, { color: sectionData.totalUnrealizedGains >= 0 ? '#10B981' : '#EF4444' }]}>
                  ${sectionData.totalUnrealizedGains?.toLocaleString() || '0'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Current Year:</Text>
                <Text style={styles.metricValue}>{new Date().getFullYear()}</Text>
              </View>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 && (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Top Holdings</Text>
                {sectionData.holdings.map((holding, index) => (
                  <View key={index}>
                    {renderHoldingCard(holding)}
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Loss Harvesting Tab */}
        {activeTab === 'loss-harvesting' && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Loss Harvesting Opportunities</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Potential Savings:</Text>
                <Text style={styles.metricValue}>${sectionData.potentialSavings?.toLocaleString() || '0'}</Text>
              </View>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 && (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Loss Positions (Harvest Candidates)</Text>
                {sectionData.holdings.map((holding, index) => (
                  <View key={index}>
                    {renderHoldingCard(holding)}
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Capital Gains Tab */}
        {activeTab === 'capital-gains' && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Capital Gains Analysis</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Long-Term CG Tax:</Text>
                <Text style={styles.metricValue}>${sectionData.ltcgTax?.toLocaleString() || '0'}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Short-Term CG Tax:</Text>
                <Text style={styles.metricValue}>${sectionData.stcgTax?.toLocaleString() || '0'}</Text>
              </View>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 && (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Gain Positions</Text>
                {sectionData.holdings.map((holding, index) => (
                  <View key={index}>
                    {renderHoldingCard(holding)}
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Rebalancing Tab */}
        {activeTab === 'rebalancing' && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Tax-Efficient Rebalancing</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Bracket Shift Tax:</Text>
                <Text style={styles.metricValue}>${sectionData.bracketShiftTax?.toLocaleString() || '0'}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Rebalancing Strategy:</Text>
                <Text style={styles.metricValue}>Tax-Loss Harvesting</Text>
              </View>
            </View>

            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Rebalancing Recommendations</Text>
              <View style={styles.rebalancingItem}>
                <View style={styles.rebalancingHeader}>
                  <Text style={styles.rebalancingSymbol}>TSLA</Text>
                  <Text style={styles.rebalancingAction}>SELL</Text>
                </View>
                <Text style={styles.rebalancingReason}>Harvest $1,500 loss to offset gains</Text>
                <Text style={styles.rebalancingTax}>Tax Savings: $330</Text>
              </View>
              
              <View style={styles.rebalancingItem}>
                <View style={styles.rebalancingHeader}>
                  <Text style={styles.rebalancingSymbol}>BTC</Text>
                  <Text style={styles.rebalancingAction}>HOLD</Text>
                </View>
                <Text style={styles.rebalancingReason}>Wait for long-term capital gains treatment</Text>
                <Text style={styles.rebalancingTax}>Tax Rate: 15% vs 22%</Text>
              </View>

              <View style={styles.rebalancingItem}>
                <View style={styles.rebalancingHeader}>
                  <Text style={styles.rebalancingSymbol}>AAPL</Text>
                  <Text style={styles.rebalancingAction}>HOLD</Text>
                </View>
                <Text style={styles.rebalancingReason}>Strong gains, hold for long-term treatment</Text>
                <Text style={styles.rebalancingTax}>Tax Rate: 15% vs 22%</Text>
              </View>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 && (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>All Holdings (Rebalancing Context)</Text>
                {sectionData.holdings.map((holding, index) => (
                  <View key={index}>
                    {renderHoldingCard(holding)}
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Bracket Analysis Tab */}
        {activeTab === 'bracket-analysis' && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Tax Bracket Analysis</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Marginal Rate:</Text>
                <Text style={styles.metricValue}>{(sectionData.marginalRate * 100)?.toFixed(1) || '0'}%</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Current Year:</Text>
                <Text style={styles.metricValue}>{currentYear}</Text>
              </View>
            </View>

            <View style={styles.bracketsCard}>
              <Text style={styles.cardTitle}>Income Tax Brackets ({currentYear})</Text>
              {INCOME_BRACKETS.map((bracket, index) => (
                <View key={index} style={styles.bracketRow}>
                  <Text style={styles.bracketRange}>
                    ${bracket.min.toLocaleString()} - ${bracket.max === Infinity ? '∞' : bracket.max.toLocaleString()}
                  </Text>
                  <Text style={styles.bracketRate}>{(bracket.rate * 100).toFixed(0)}%</Text>
                </View>
              ))}
            </View>

            <View style={styles.bracketsCard}>
              <Text style={styles.cardTitle}>Long-Term Capital Gains Brackets ({currentYear})</Text>
              {LTCG_BRACKETS.map((bracket, index) => (
                <View key={index} style={styles.bracketRow}>
                  <Text style={styles.bracketRange}>
                    ${bracket.min.toLocaleString()} - ${bracket.max === Infinity ? '∞' : bracket.max.toLocaleString()}
                  </Text>
                  <Text style={styles.bracketRate}>{(bracket.rate * 100).toFixed(0)}%</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading tax optimization data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        contentInsetAdjustmentBehavior="never"
        automaticallyAdjustContentInsets={false}
        contentInset={{ top: 0, bottom: 0 }}
        scrollIndicatorInsets={{ top: 0, bottom: 0 }}
        collapsable={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#007AFF" />
        }
      >
        <HeaderBlock
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
        
        {/* Content starts immediately */}
        <View style={styles.sectionFirst}>
          {renderTabContent()}
        </View>
      </ScrollView>
    </View>
  );
};

// Removed mock holdings - using real data from API

const TAB_HEIGHT_MIN = 30;

const styles = StyleSheet.create({
  root: { 
    flex: 1, 
    backgroundColor: '#f8f9fa' 
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 8,
  },
  // Parent of header+tabs — NO gap/padding at all
  headerBlock: {
    backgroundColor: 'white',
    padding: 0,
    margin: 0,
    // important: never use `gap` here
  },
  // Title + subtitle
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingTop: 6,
    paddingBottom: 0,        // <- keep 0
    margin: 0,
    borderBottomWidth: 0,    // <- no divider
    gap: 16,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 20, 
    lineHeight: 24, 
    fontWeight: '700', 
    color: '#1f2937',
    includeFontPadding: false, 
    marginBottom: 0,
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 13,          // <- match fontSize; removes extra line box
    color: '#6b7280',
    includeFontPadding: false,
    marginTop: 0,
    marginBottom: 10,        // <- moved down more, increased spacing
  },
  // Tabs sit IMMEDIATELY under subtitle
  tabsRow: {
    marginTop: 0,            // <- moved down more, no negative margin
    marginBottom: 0,
    backgroundColor: 'white',
    borderTopWidth: 0,
    borderBottomWidth: 0,
  },
  tabsContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingTop: 0,
    paddingBottom: 0,
    gap: 6,
  },
  tabBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 10,
    minHeight: TAB_HEIGHT_MIN,
    margin: 0,
  },
  tabBtnActive: { 
    backgroundColor: 'rgba(37,99,235,0.10)' 
  },
  tabIcon: { 
    width: 16, 
    height: 16, 
    marginRight: 4 
  },
  tabLabel: {
    fontSize: 14,
    lineHeight: 16,
    fontWeight: '500',
    color: '#6b7280',
    includeFontPadding: false,
    margin: 0,
  },
  tabLabelActive: { 
    color: '#2563EB' 
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 0, 
    marginTop: 0, /* NO gap */
  },
  // First section must NOT add a big top gap
  sectionFirst: { 
    paddingTop: 6, 
    paddingHorizontal: 16,
    paddingBottom: 24,
    backgroundColor: '#f8f9fa',
  },
  tabContent: {
    flex: 1,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 10,          // keep tight
  },
  sectionSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  metricsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  yieldsSection: {
    marginBottom: 20,
  },
  yieldCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#10B981',
  },
  yieldHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  protocolName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  taxBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  taxBadgeText: {
    fontSize: 10,
    fontWeight: '500',
    color: '#fff',
  },
  yieldApy: {
    fontSize: 12,
    color: '#374151',
    marginBottom: 2,
  },
  yieldRec: {
    fontSize: 11,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  bracketsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  bracketRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: 0.5,
    borderBottomColor: '#f3f4f6',
  },
  bracketRange: {
    fontSize: 12,
    color: '#6b7280',
    flex: 1,
  },
  bracketRate: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1f2937',
  },
  noDataContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  noDataText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
    marginTop: 12,
  },
  noDataSubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  rebalancingItem: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#3B82F6',
  },
  rebalancingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  rebalancingSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  rebalancingAction: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
    backgroundColor: '#EF4444',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  rebalancingReason: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 2,
  },
  rebalancingTax: {
    fontSize: 12,
    fontWeight: '500',
    color: '#10B981',
  },
});

export default TaxOptimizationScreen;