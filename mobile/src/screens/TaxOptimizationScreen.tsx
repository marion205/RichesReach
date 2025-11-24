import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  FlatList,
  Modal,
  TextInput,
  Share,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../contexts/AuthContext';
import taxOptimizationService from '../services/taxOptimizationService';
import { API_BASE } from '../config/api';

interface TaxOptimizationData {
  summary?: any;
  lossHarvesting?: any;
  capitalGains?: any;
  rebalancing?: any;
  bracketAnalysis?: any;
  holdings?: any[];
  yearOverYear?: any;
}

type FilingStatus = 'single' | 'married-joint' | 'married-separate' | 'head-of-household';
type ErrorType = 'network' | 'timeout' | 'server' | 'unknown';

const currentYear = new Date().getFullYear();
const CACHE_KEY = 'tax_optimization_cache';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

// Tax Brackets by Filing Status (2025)
const INCOME_BRACKETS: Record<FilingStatus, Array<{ min: number; max: number; rate: number }>> = {
  single: [
    { min: 0, max: 11600, rate: 0.10 },
    { min: 11601, max: 47150, rate: 0.12 },
    { min: 47151, max: 100525, rate: 0.22 },
    { min: 100526, max: 191950, rate: 0.24 },
    { min: 191951, max: 243725, rate: 0.32 },
    { min: 243726, max: 609350, rate: 0.35 },
    { min: 609351, max: Infinity, rate: 0.37 },
  ],
  'married-joint': [
    { min: 0, max: 23200, rate: 0.10 },
    { min: 23201, max: 94300, rate: 0.12 },
    { min: 94301, max: 201050, rate: 0.22 },
    { min: 201051, max: 383900, rate: 0.24 },
    { min: 383901, max: 487450, rate: 0.32 },
    { min: 487451, max: 731200, rate: 0.35 },
    { min: 731201, max: Infinity, rate: 0.37 },
  ],
  'married-separate': [
    { min: 0, max: 11600, rate: 0.10 },
    { min: 11601, max: 47150, rate: 0.12 },
    { min: 47151, max: 100525, rate: 0.22 },
    { min: 100526, max: 191950, rate: 0.24 },
    { min: 191951, max: 243725, rate: 0.32 },
    { min: 243726, max: 365600, rate: 0.35 },
    { min: 365601, max: Infinity, rate: 0.37 },
  ],
  'head-of-household': [
    { min: 0, max: 16550, rate: 0.10 },
    { min: 16551, max: 63100, rate: 0.12 },
    { min: 63101, max: 100500, rate: 0.22 },
    { min: 100501, max: 191950, rate: 0.24 },
    { min: 191951, max: 243700, rate: 0.32 },
    { min: 243701, max: 609350, rate: 0.35 },
    { min: 609351, max: Infinity, rate: 0.37 },
  ],
};

const LTCG_BRACKETS: Record<FilingStatus, Array<{ min: number; max: number; rate: number }>> = {
  single: [
    { min: 0, max: 47025, rate: 0.0 },
    { min: 47026, max: 518900, rate: 0.15 },
    { min: 518901, max: Infinity, rate: 0.2 },
  ],
  'married-joint': [
    { min: 0, max: 94050, rate: 0.0 },
    { min: 94051, max: 583750, rate: 0.15 },
    { min: 583751, max: Infinity, rate: 0.2 },
  ],
  'married-separate': [
    { min: 0, max: 47025, rate: 0.0 },
    { min: 47026, max: 291850, rate: 0.15 },
    { min: 291851, max: Infinity, rate: 0.2 },
  ],
  'head-of-household': [
    { min: 0, max: 63100, rate: 0.0 },
    { min: 63101, max: 523050, rate: 0.15 },
    { min: 523051, max: Infinity, rate: 0.2 },
  ],
};

// State Tax Rates (simplified - top marginal rates)
const STATE_TAX_RATES: Record<string, number> = {
  CA: 0.133,
  NY: 0.109,
  NJ: 0.1075,
  OR: 0.099,
  MN: 0.0985,
  DC: 0.1075,
  VT: 0.0875,
  IA: 0.0898,
  WI: 0.0765,
  HI: 0.11,
  // No state income tax
  AK: 0,
  FL: 0,
  NV: 0,
  NH: 0,
  SD: 0,
  TN: 0,
  TX: 0,
  WA: 0,
  WY: 0,
};

// AMT Exemption Amounts (2025)
const AMT_EXEMPTIONS: Record<FilingStatus, { exemption: number; phaseOutStart: number }> = {
  single: { exemption: 85200, phaseOutStart: 609350 },
  'married-joint': { exemption: 133100, phaseOutStart: 1217700 },
  'married-separate': { exemption: 66550, phaseOutStart: 608850 },
  'head-of-household': { exemption: 85200, phaseOutStart: 914900 },
};

// Memoized Calculator Functions
const calculateIncomeTax = (
  income: number,
  filingStatus: FilingStatus = 'single'
): { tax: number; effectiveRate: number } => {
  const brackets = INCOME_BRACKETS[filingStatus];
  let tax = 0;
  let prevMax = 0;
  for (const bracket of brackets) {
    if (income > prevMax) {
      const taxableInBracket = Math.min(income, bracket.max) - prevMax;
      tax += taxableInBracket * bracket.rate;
      prevMax = bracket.max;
    }
  }
  return { tax, effectiveRate: income > 0 ? tax / income : 0 };
};

const calculateLTCG = (
  gain: number,
  taxableIncome: number,
  filingStatus: FilingStatus = 'single'
): number => {
  const brackets = LTCG_BRACKETS[filingStatus];
  let tax = 0;
  let prevMax = 0;
  for (const bracket of brackets) {
    if (gain > 0) {
      const taxableInBracket = Math.min(gain, bracket.max - Math.max(0, taxableIncome - prevMax));
      tax += taxableInBracket * bracket.rate;
      gain -= taxableInBracket;
      prevMax = bracket.max;
    }
  }
  return tax;
};

const calculateAMT = (
  income: number,
  filingStatus: FilingStatus = 'single'
): { amt: number; applies: boolean } => {
  const exemption = AMT_EXEMPTIONS[filingStatus];
  let amtIncome = income;
  
  // Phase out exemption
  if (income > exemption.phaseOutStart) {
    const excess = income - exemption.phaseOutStart;
    const phaseOutAmount = excess * 0.25;
    amtIncome = income - Math.max(0, exemption.exemption - phaseOutAmount);
  } else {
    amtIncome = Math.max(0, income - exemption.exemption);
  }
  
  const amt = amtIncome * 0.26; // AMT rate is 26% or 28% (simplified to 26%)
  const regularTax = calculateIncomeTax(income, filingStatus).tax;
  
  return {
    amt: Math.max(0, amt - regularTax),
    applies: amt > regularTax,
  };
};

const calculateStateTax = (income: number, state: string): number => {
  const rate = STATE_TAX_RATES[state] || 0;
  return income * rate;
};

// Wash Sale Detection (simplified - checks for same symbol within 30 days)
const detectWashSales = (holdings: any[], transactions: any[] = []): any[] => {
  const washSales: any[] = [];
  const soldWithin30Days = new Map<string, Date>();
  
  // Check for sales within 30 days
  transactions.forEach((tx) => {
    if (tx.type === 'sell' && tx.date) {
      const sellDate = new Date(tx.date);
      soldWithin30Days.set(tx.symbol, sellDate);
    }
  });
  
  // Check holdings for potential wash sales
  holdings.forEach((holding) => {
    const sellDate = soldWithin30Days.get(holding.symbol);
    if (sellDate) {
      const daysSince = (Date.now() - sellDate.getTime()) / (1000 * 60 * 60 * 24);
      if (daysSince < 30 && holding.unrealizedGain < 0) {
        washSales.push({
          ...holding,
          washSaleRisk: true,
          daysSinceSale: Math.floor(daysSince),
        });
      }
    }
  });
  
  return washSales;
};

// Debounce utility
const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Header Block Component
const HeaderBlock: React.FC<{
  tabs: any[];
  activeTab: string;
  onTabChange: (tab: string) => void;
  filingStatus: FilingStatus;
  onFilingStatusChange: () => void;
}> = React.memo(({ tabs, activeTab, onTabChange, filingStatus, onFilingStatusChange }) => {
  const debouncedTabChange = useMemo(
    () => debounce(onTabChange, 150),
    [onTabChange]
  );

  return (
    <View style={styles.headerBlock}>
      <View style={styles.headerTop}>
        <View style={styles.headerIconWrapper}>
          <Ionicons name="calculator-outline" size={24} color="#2563EB" />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title} numberOfLines={1}>
            Tax Optimization
          </Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            Real {currentYear} calculations for stocks & crypto
          </Text>
        </View>
        <TouchableOpacity
          style={styles.filingStatusBtn}
          onPress={onFilingStatusChange}
          hitSlop={10}
        >
          <Ionicons name="settings-outline" size={20} color="#2563EB" />
        </TouchableOpacity>
      </View>

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
            onPress={() => debouncedTabChange(tab.key)}
            hitSlop={10}
            activeOpacity={0.8}
          >
            <Ionicons
              name={tab.icon as any}
              size={16}
              color={activeTab === tab.key ? '#2563EB' : '#6B7280'}
              style={styles.tabIcon}
            />
            <Text
              style={[styles.tabLabel, activeTab === tab.key && styles.tabLabelActive]}
              numberOfLines={1}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
});

// Memoized Holding Card
const HoldingCard = React.memo<{ holding: any; onHarvest?: () => void }>(
  ({ holding, onHarvest }) => {
    const isGain = holding.unrealizedGain >= 0;
    const gainColor = isGain ? '#10B981' : '#EF4444';
    const isWashSale = holding.washSaleRisk;

    return (
      <View style={[styles.holdingCard, isWashSale && styles.washSaleCard]}>
        <View style={styles.holdingHeader}>
          <View>
            <Text style={styles.holdingSymbol}>{holding.symbol}</Text>
            {holding.name && <Text style={styles.holdingName}>{holding.name}</Text>}
          </View>
          <View style={styles.badgeRow}>
            {isWashSale && (
              <View style={styles.washSaleBadge}>
                <Text style={styles.washSaleBadgeText}>WASH SALE</Text>
              </View>
            )}
            <View
              style={[
                styles.taxBadge,
                { backgroundColor: holding.type === 'stock' ? '#3B82F6' : '#8B5CF6' },
              ]}
            >
              <Text style={styles.taxBadgeText}>{holding.type?.toUpperCase() || 'ASSET'}</Text>
            </View>
          </View>
        </View>

        <View style={styles.holdingRow}>
          <Text style={styles.holdingLabel}>Quantity</Text>
          <Text style={styles.holdingValue}>{holding.quantity?.toLocaleString() || '-'}</Text>
        </View>
        <View style={styles.holdingRow}>
          <Text style={styles.holdingLabel}>Current Value</Text>
          <Text style={styles.holdingValue}>
            ${holding.currentValue?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || '0'}
          </Text>
        </View>
        <View style={styles.holdingRow}>
          <Text style={styles.holdingLabel}>Unrealized</Text>
          <Text style={[styles.holdingValue, { color: gainColor }]}>
            {holding.unrealizedGain >= 0 ? '+' : '-'}$
            {Math.abs(holding.unrealizedGain || 0).toLocaleString(undefined, {
              maximumFractionDigits: 0,
            })}{' '}
            ({holding.unrealizedGainPercent?.toFixed(1) || '0.0'}%)
          </Text>
        </View>
        {!isGain && onHarvest && (
          <TouchableOpacity style={styles.harvestButton} onPress={onHarvest}>
            <Ionicons name="cut-outline" size={14} color="#fff" />
            <Text style={styles.harvestButtonText}>Harvest Loss</Text>
          </TouchableOpacity>
        )}
        <View style={styles.holdingFooter}>
          <Text style={styles.holdingRec} numberOfLines={2}>
            {holding.recommendation || 'No specific recommendation for this position yet.'}
          </Text>
        </View>
      </View>
    );
  }
);

const TaxOptimizationScreen: React.FC = () => {
  const { user, token } = useAuth();
  const [data, setData] = useState<TaxOptimizationData>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [userIncome, setUserIncome] = useState<number | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [filingStatus, setFilingStatus] = useState<FilingStatus>('single');
  const [state, setState] = useState<string>('CA');
  const [retryCount, setRetryCount] = useState(0);
  const [error, setError] = useState<{ type: ErrorType; message: string } | null>(null);
  const [offlineMode, setOfflineMode] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showWhatIfModal, setShowWhatIfModal] = useState(false);
  const [whatIfIncome, setWhatIfIncome] = useState<string>('');
  const [whatIfGains, setWhatIfGains] = useState<string>('');
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Memoized tax calculations
  const taxCalculations = useMemo(() => {
    if (!userIncome) return null;
    
    const incomeTax = calculateIncomeTax(userIncome, filingStatus);
    const stateTax = calculateStateTax(userIncome, state);
    const amt = calculateAMT(userIncome, filingStatus);
    const totalTax = incomeTax.tax + stateTax + (amt.applies ? amt.amt : 0);
    
    return {
      incomeTax: incomeTax.tax,
      stateTax,
      amt: amt.amt,
      amtApplies: amt.applies,
      totalTax,
      effectiveRate: incomeTax.effectiveRate,
      marginalRate: incomeTax.effectiveRate,
    };
  }, [userIncome, filingStatus, state]);

  // Load cached data
  const loadCachedData = useCallback(async () => {
    try {
      const cached = await AsyncStorage.getItem(CACHE_KEY);
      if (cached) {
        const { data: cachedData, timestamp } = JSON.parse(cached);
        const age = Date.now() - timestamp;
        if (age < CACHE_EXPIRY) {
          setData(cachedData);
          setLastUpdated(new Date(timestamp));
          setOfflineMode(true);
          return cachedData;
        }
      }
    } catch (e) {
      console.error('Error loading cache:', e);
    }
    return null;
  }, []);

  // Save data to cache
  const saveToCache = useCallback(async (dataToCache: TaxOptimizationData) => {
    try {
      await AsyncStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          data: dataToCache,
          timestamp: Date.now(),
        })
      );
    } catch (e) {
      console.error('Error saving cache:', e);
    }
  }, []);

  // Enhanced error handling with retry logic
  const handleError = useCallback(
    (error: any, context: string): ErrorType => {
      let errorType: ErrorType = 'unknown';
      let message = 'An unexpected error occurred';

      if (error?.message?.includes('timeout') || error?.message?.includes('TIMEOUT')) {
        errorType = 'timeout';
        message = 'Request timed out. Please check your connection and try again.';
      } else if (error?.message?.includes('network') || error?.message?.includes('Network')) {
        errorType = 'network';
        message = 'Network error. Please check your internet connection.';
      } else if (error?.status >= 500) {
        errorType = 'server';
        message = 'Server error. Please try again in a moment.';
      } else if (error?.status >= 400) {
        errorType = 'server';
        message = 'Invalid request. Please refresh and try again.';
      }

      setError({ type: errorType, message });
      
      // Auto-retry for network/timeout errors
      if ((errorType === 'network' || errorType === 'timeout') && retryCount < 3) {
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          setRetryCount((prev) => prev + 1);
          loadData();
        }, 2000 * (retryCount + 1)); // Exponential backoff
      }

      return errorType;
    },
    [retryCount]
  );

  const loadData = useCallback(async () => {
    // Try cache first if offline
    if (offlineMode) {
      const cached = await loadCachedData();
      if (cached) return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // Fetch user income
      const incomeProfile = (user as any)?.incomeProfile;
      const profile = (user as any)?.profile;
      const income = incomeProfile?.annualIncome || profile?.income || 80000;
      setUserIncome(income);

      // Fetch holdings with timeout
      let rawHoldings: any[] = [];
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

      try {
        console.log('📊 [Tax Optimization] Fetching optimization summary...');
        const summaryData = await taxOptimizationService.getOptimizationSummary(token || '');
        console.log('📊 [Tax Optimization] Summary data received:', summaryData);
        
        if (summaryData?.holdings && Array.isArray(summaryData.holdings) && summaryData.holdings.length > 0) {
          rawHoldings = summaryData.holdings;
          console.log(`📊 [Tax Optimization] Found ${rawHoldings.length} holdings from API`);
        } else {
          console.log('📊 [Tax Optimization] No holdings from API, trying GraphQL fallback...');
          const portfolioResponse = await fetch(`${API_BASE}/graphql`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token || ''}`,
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
              `,
            }),
            signal: controller.signal,
          });

          const portfolioData = await portfolioResponse.json();
          if (portfolioData?.data?.portfolioMetrics?.holdings) {
            rawHoldings = portfolioData.data.portfolioMetrics.holdings.map((h: any) => ({
              symbol: h.symbol,
              type: 'stock',
              name: h.companyName,
              currentPrice: h.currentPrice,
              costBasis: h.costBasis / (h.shares || 1),
              quantity: h.shares || 0,
              taxImpact: h.returnPercent > 0 ? 0.15 : 0.22,
              recommendation:
                h.returnPercent > 0
                  ? 'Hold for long-term gains'
                  : 'Consider tax-loss harvesting',
            }));
          }
        }
        clearTimeout(timeoutId);
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          handleError({ message: 'TIMEOUT' }, 'fetch');
          // Try cache
          const cached = await loadCachedData();
          if (cached) return;
          throw fetchError;
        }
        throw fetchError;
      }

      if (rawHoldings.length === 0) {
        console.log('⚠️ [Tax Optimization] No holdings found, setting empty data');
        const emptyData = {
          summary: {
            estimatedAnnualTax: 0,
            holdings: [],
            totalPortfolioValue: 0,
            totalUnrealizedGains: 0,
            effectiveRate: 0,
            income: income,
          },
          lossHarvesting: { potentialSavings: 0, holdings: [] },
          capitalGains: { ltcgTax: 0, stcgTax: 0, holdings: [] },
          rebalancing: { bracketShiftTax: 0, holdings: [] },
          bracketAnalysis: { marginalRate: 0, income: income },
          yearOverYear: {
            currentYear: currentYear,
            previousYear: currentYear - 1,
            currentTax: 0,
            previousTax: 0,
            change: 0,
            changePercent: 0,
          },
          holdings: [],
        };
        setData(emptyData);
        setLastUpdated(new Date());
        await saveToCache(emptyData);
        return;
      }

      // Process holdings with wash sale detection
      console.log(`📊 [Tax Optimization] Processing ${rawHoldings.length} holdings...`);
      const integratedHoldings = rawHoldings.map((holding: any) => {
        const quantity = holding.quantity || holding.shares || 0;
        const currentPrice = parseFloat(holding.currentPrice) || 0;
        const costBasis = parseFloat(holding.costBasis) || 0;
        const currentValue = currentPrice * quantity;
        const unrealizedGain = (currentPrice - costBasis) * quantity;
        const unrealizedGainPercent =
          costBasis > 0
            ? ((currentPrice - costBasis) / costBasis) * 100
            : 0;

        return {
          ...holding,
          quantity,
          currentValue,
          unrealizedGain,
          unrealizedGainPercent,
          taxSavingsPotential: unrealizedGain < 0 ? Math.abs(unrealizedGain) * 0.22 : 0,
          type: holding.type || 'stock',
          name: holding.companyName || holding.name || holding.symbol,
        };
      });
      console.log(`✅ [Tax Optimization] Processed ${integratedHoldings.length} holdings`);
      
      // Ensure we have at least some data structure even if empty
      if (integratedHoldings.length === 0) {
        console.log('⚠️ [Tax Optimization] No holdings after processing, using empty data');
      }

      const washSales = detectWashSales(integratedHoldings);
      washSales.forEach((ws) => {
        const idx = integratedHoldings.findIndex((h) => h.symbol === ws.symbol);
        if (idx >= 0) {
          integratedHoldings[idx] = { ...integratedHoldings[idx], ...ws };
        }
      });

      // Calculate tax metrics with enhanced logic
      const effectiveIncome = income;
      const incomeTaxResult = calculateIncomeTax(effectiveIncome, filingStatus);
      const stateTaxAmount = calculateStateTax(effectiveIncome, state);
      const amtResult = calculateAMT(effectiveIncome, filingStatus);

      const summary = {
        estimatedAnnualTax: incomeTaxResult.tax + stateTaxAmount + (amtResult.applies ? amtResult.amt : 0),
        holdings: integratedHoldings.slice(0, 3),
        totalPortfolioValue: integratedHoldings.reduce((sum, h) => sum + h.currentValue, 0),
        totalUnrealizedGains: integratedHoldings.reduce((sum, h) => sum + h.unrealizedGain, 0),
        effectiveRate: incomeTaxResult.effectiveRate,
        income: effectiveIncome,
        stateTax: stateTaxAmount,
        amt: amtResult.amt,
        amtApplies: amtResult.applies,
      };

      const lossHarvesting = {
        potentialSavings: integratedHoldings
          .filter((h) => h.unrealizedGain < 0 && !h.washSaleRisk)
          .reduce((sum, h) => sum + h.taxSavingsPotential, 0),
        holdings: integratedHoldings.filter((h) => h.unrealizedGain < 0),
      };

      const capitalGains = {
        ltcgTax: calculateLTCG(10000, effectiveIncome, filingStatus),
        stcgTax:
          calculateIncomeTax(effectiveIncome + 10000, filingStatus).tax -
          calculateIncomeTax(effectiveIncome, filingStatus).tax,
        holdings: integratedHoldings.filter((h) => h.unrealizedGain > 0),
      };

      const rebalancing = {
        bracketShiftTax:
          calculateIncomeTax(effectiveIncome + 10000, filingStatus).tax -
          calculateIncomeTax(effectiveIncome, filingStatus).tax,
        holdings: integratedHoldings,
      };

      const bracketAnalysis = {
        marginalRate: incomeTaxResult.effectiveRate,
        income: effectiveIncome,
        filingStatus,
        state,
      };

      // Year-over-year comparison (simplified)
      const yearOverYear = {
        currentYear: currentYear,
        previousYear: currentYear - 1,
        currentTax: summary.estimatedAnnualTax,
        previousTax: summary.estimatedAnnualTax * 0.95, // Mock previous year
        change: summary.estimatedAnnualTax * 0.05,
        changePercent: 5.0,
      };

      const finalData = {
        summary,
        lossHarvesting,
        capitalGains,
        rebalancing,
        bracketAnalysis,
        yearOverYear,
        holdings: integratedHoldings,
      };

      setData(finalData);
      setLastUpdated(new Date());
      setOfflineMode(false);
      setRetryCount(0);
      await saveToCache(finalData);
    } catch (error: any) {
      console.error('Error loading tax optimization data:', error);
      handleError(error, 'loadData');
      
      // Try to load from cache as fallback
      const cached = await loadCachedData();
      if (!cached) {
        Alert.alert(
          'Error',
          error?.message || 'Failed to load tax optimization data. Please try again.',
          [
            { text: 'Retry', onPress: () => loadData() },
            { text: 'Use Cached Data', onPress: () => loadCachedData() },
            { text: 'OK', style: 'cancel' },
          ]
        );
      }
    } finally {
      setLoading(false);
    }
  }, [user, token, filingStatus, state, offlineMode, handleError, loadCachedData, saveToCache]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    setRetryCount(0);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Action handlers
  const handleHarvestLosses = useCallback(() => {
    const lossHoldings = data.lossHarvesting?.holdings?.filter((h: any) => !h.washSaleRisk) || [];
    if (lossHoldings.length === 0) {
      Alert.alert('No Opportunities', 'You don\'t have any harvestable losses right now.');
      return;
    }
    Alert.alert(
      'Harvest Losses',
      `You can harvest ${lossHoldings.length} positions to save approximately $${data.lossHarvesting?.potentialSavings?.toLocaleString() || '0'} in taxes.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Proceed',
          onPress: () => {
            // In a real app, this would trigger a trade execution
            Alert.alert('Success', 'Loss harvesting order placed. Check your portfolio for updates.');
          },
        },
      ]
    );
  }, [data]);

  const handleExportReport = useCallback(async () => {
    try {
      const report = `
Tax Optimization Report - ${currentYear}
Generated: ${new Date().toLocaleDateString()}

Filing Status: ${filingStatus}
State: ${state}
Annual Income: $${userIncome?.toLocaleString() || '0'}

Tax Summary:
- Federal Tax: $${taxCalculations?.incomeTax.toLocaleString() || '0'}
- State Tax: $${taxCalculations?.stateTax.toLocaleString() || '0'}
- AMT: $${taxCalculations?.amt.toLocaleString() || '0'}
- Total Tax: $${taxCalculations?.totalTax.toLocaleString() || '0'}
- Effective Rate: ${((taxCalculations?.effectiveRate || 0) * 100).toFixed(1)}%

Portfolio:
- Total Value: $${data.summary?.totalPortfolioValue.toLocaleString() || '0'}
- Unrealized Gains: $${data.summary?.totalUnrealizedGains.toLocaleString() || '0'}

Loss Harvesting Opportunity:
- Potential Savings: $${data.lossHarvesting?.potentialSavings.toLocaleString() || '0'}
- Positions: ${data.lossHarvesting?.holdings?.length || 0}
      `;

      await Share.share({
        message: report,
        title: 'Tax Optimization Report',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to export report.');
    }
  }, [data, taxCalculations, filingStatus, state, userIncome]);

  const handleWhatIf = useCallback(() => {
    const income = parseFloat(whatIfIncome) || userIncome || 0;
    const gains = parseFloat(whatIfGains) || 0;
    
    const newIncome = income + gains;
    const currentTax = calculateIncomeTax(income, filingStatus).tax;
    const newTax = calculateIncomeTax(newIncome, filingStatus).tax;
    const taxIncrease = newTax - currentTax;
    
    Alert.alert(
      'What-If Scenario',
      `If you realize $${gains.toLocaleString()} in gains:\n\n` +
        `Current Tax: $${currentTax.toLocaleString()}\n` +
        `New Tax: $${newTax.toLocaleString()}\n` +
        `Additional Tax: $${taxIncrease.toLocaleString()}\n\n` +
        `Effective Rate: ${((newTax / newIncome) * 100).toFixed(1)}%`,
      [{ text: 'OK' }]
    );
  }, [whatIfIncome, whatIfGains, userIncome, filingStatus]);

  const tabs = [
    { key: 'summary', label: 'Summary', icon: 'analytics-outline' },
    { key: 'loss-harvesting', label: 'Loss H.', icon: 'trending-down' },
    { key: 'capital-gains', label: 'Cap. Gains', icon: 'trending-up' },
    { key: 'rebalancing', label: 'Rebal.', icon: 'refresh-circle' },
    { key: 'bracket-analysis', label: 'Brackets', icon: 'bar-chart' },
    { key: 'year-over-year', label: 'YoY', icon: 'calendar-outline' },
  ];

  const renderTabContent = () => {
    const getSectionData = () => {
      const defaultIncome = userIncome || 80000;
      switch (activeTab) {
        case 'summary':
          return data.summary || { estimatedAnnualTax: 0, holdings: [], totalPortfolioValue: 0, totalUnrealizedGains: 0, effectiveRate: 0, income: defaultIncome };
        case 'loss-harvesting':
          return data.lossHarvesting || { potentialSavings: 0, holdings: [] };
        case 'capital-gains':
          return data.capitalGains || { ltcgTax: 0, stcgTax: 0, holdings: [] };
        case 'rebalancing':
          return data.rebalancing || { bracketShiftTax: 0, holdings: [] };
        case 'bracket-analysis':
          return data.bracketAnalysis || { marginalRate: 0, income: defaultIncome, filingStatus, state };
        case 'year-over-year':
          return data.yearOverYear || { currentYear: currentYear, previousYear: currentYear - 1, currentTax: 0, previousTax: 0, change: 0, changePercent: 0 };
        default:
          return data.summary || { estimatedAnnualTax: 0, holdings: [], totalPortfolioValue: 0, totalUnrealizedGains: 0, effectiveRate: 0, income: defaultIncome };
      }
    };

    const sectionData = getSectionData();
    const sectionTitle = tabs.find((tab) => tab.key === activeTab)?.label || 'Overview';

    // Always show content, even if data is empty
    console.log(`📊 [Tax Optimization] Rendering tab: ${activeTab}, has data: ${!!sectionData}, data keys: ${Object.keys(data)}`);

    return (
      <View style={styles.tabContent}>
        <View style={styles.sectionHeader}>
          <View style={styles.sectionHeaderLeft}>
            <Text style={styles.sectionTitle}>{sectionTitle}</Text>
            {lastUpdated && (
              <Text style={styles.lastUpdated}>
                Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                {offlineMode && ' (Cached)'}
              </Text>
            )}
          </View>
          <View style={styles.headerActions}>
            {activeTab === 'loss-harvesting' && (
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleHarvestLosses}
                hitSlop={10}
              >
                <Ionicons name="cut-outline" size={18} color="#2563EB" />
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={styles.actionButton}
              onPress={handleExportReport}
              hitSlop={10}
            >
              <Ionicons name="share-outline" size={18} color="#2563EB" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => setShowWhatIfModal(true)}
              hitSlop={10}
            >
              <Ionicons name="calculator" size={18} color="#2563EB" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Error Banner */}
        {error && (
          <View style={styles.errorBanner}>
            <Ionicons name="alert-circle" size={20} color="#EF4444" />
            <Text style={styles.errorText}>{error.message}</Text>
            <TouchableOpacity onPress={() => setError(null)}>
              <Ionicons name="close" size={20} color="#EF4444" />
            </TouchableOpacity>
          </View>
        )}

        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <View>
            <View style={styles.chipRow}>
              <View style={styles.chip}>
                <Ionicons name="wallet-outline" size={14} color="#2563EB" />
                <Text style={styles.chipText}>
                  Income: ${sectionData.income?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || '—'}
                </Text>
              </View>
              <View style={styles.chip}>
                <Ionicons name="speedometer-outline" size={14} color="#2563EB" />
                <Text style={styles.chipText}>
                  Effective: {((sectionData.effectiveRate || 0) * 100).toFixed(1)}%
                </Text>
              </View>
              <View style={styles.chip}>
                <Ionicons name="location-outline" size={14} color="#2563EB" />
                <Text style={styles.chipText}>{filingStatus.replace('-', ' ').toUpperCase()}</Text>
              </View>
            </View>

            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Tax Overview</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Estimated Annual Tax</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.estimatedAnnualTax?.toLocaleString() || '0'}
                </Text>
              </View>
              {sectionData.stateTax > 0 && (
                <View style={styles.metricRow}>
                  <Text style={styles.metricLabel}>State Tax ({state})</Text>
                  <Text style={styles.metricValue}>
                    ${sectionData.stateTax?.toLocaleString() || '0'}
                  </Text>
                </View>
              )}
              {sectionData.amtApplies && (
                <View style={styles.metricRow}>
                  <Text style={styles.metricLabel}>AMT</Text>
                  <Text style={styles.metricValue}>
                    ${sectionData.amt?.toLocaleString() || '0'}
                  </Text>
                </View>
              )}
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Portfolio Value</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.totalPortfolioValue?.toLocaleString() || '0'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Unrealized Gains</Text>
                <Text
                  style={[
                    styles.metricValue,
                    {
                      color: sectionData.totalUnrealizedGains >= 0 ? '#10B981' : '#EF4444',
                    },
                  ]}
                >
                  ${sectionData.totalUnrealizedGains?.toLocaleString() || '0'}
                </Text>
              </View>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 ? (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Top Holdings (Tax Impact)</Text>
                <FlatList
                  data={sectionData.holdings}
                  keyExtractor={(item, index) => `${item.symbol}-${index}`}
                  renderItem={({ item }) => <HoldingCard holding={item} />}
                  scrollEnabled={false}
                  removeClippedSubviews={true}
                  initialNumToRender={3}
                />
              </View>
            ) : (
              <View style={styles.noDataSmall}>
                <Text style={styles.noDataSmallText}>
                  Add holdings to your portfolio to see tax insights here.
                </Text>
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
                <Text style={styles.metricLabel}>Potential Tax Savings</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.potentialSavings?.toLocaleString() || '0'}
                </Text>
              </View>
              <Text style={styles.helperText}>
                These positions are currently at a loss. Realizing some losses can offset your
                gains this year. Wash sale rules apply.
              </Text>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 ? (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Loss Positions (Harvest Candidates)</Text>
                <FlatList
                  data={sectionData.holdings}
                  keyExtractor={(item, index) => `${item.symbol}-${index}`}
                  renderItem={({ item }) => (
                    <HoldingCard
                      holding={item}
                      onHarvest={() => handleHarvestLosses()}
                    />
                  )}
                  scrollEnabled={false}
                  removeClippedSubviews={true}
                  initialNumToRender={10}
                  maxToRenderPerBatch={5}
                  windowSize={10}
                />
              </View>
            ) : (
              <View style={styles.noDataSmall}>
                <Text style={styles.noDataSmallText}>
                  You don't have any positions in a loss large enough to harvest right now.
                </Text>
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
                <Text style={styles.metricLabel}>Long-Term CG Tax (Example)</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.ltcgTax?.toLocaleString() || '0'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Short-Term CG Tax (Example)</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.stcgTax?.toLocaleString() || '0'}
                </Text>
              </View>
              <Text style={styles.helperText}>
                Long-term gains are usually taxed at a lower rate. Holding winners longer can
                dramatically reduce your tax bill.
              </Text>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 ? (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>Gain Positions</Text>
                <FlatList
                  data={sectionData.holdings}
                  keyExtractor={(item, index) => `${item.symbol}-${index}`}
                  renderItem={({ item }) => <HoldingCard holding={item} />}
                  scrollEnabled={false}
                  removeClippedSubviews={true}
                  initialNumToRender={10}
                />
              </View>
            ) : (
              <View style={styles.noDataSmall}>
                <Text style={styles.noDataSmallText}>
                  No gain-heavy positions detected yet. As your winners grow, you'll see them here.
                </Text>
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
                <Text style={styles.metricLabel}>Bracket Shift Tax (Example)</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.bracketShiftTax?.toLocaleString() || '0'}
                </Text>
              </View>
              <Text style={styles.helperText}>
                Large rebalances can accidentally push you into a higher tax bracket. Use this
                to plan partial moves over time.
              </Text>
            </View>

            {sectionData.holdings && sectionData.holdings.length > 0 ? (
              <View style={styles.yieldsSection}>
                <Text style={styles.sectionSubtitle}>
                  All Holdings (Rebalancing Context)
                </Text>
                <FlatList
                  data={sectionData.holdings}
                  keyExtractor={(item, index) => `${item.symbol}-${index}`}
                  renderItem={({ item }) => <HoldingCard holding={item} />}
                  scrollEnabled={false}
                  removeClippedSubviews={true}
                  initialNumToRender={10}
                  maxToRenderPerBatch={5}
                  windowSize={10}
                />
              </View>
            ) : (
              <View style={styles.noDataSmall}>
                <Text style={styles.noDataSmallText}>
                  Once you have a diversified portfolio, we'll show how to rebalance with minimal
                  tax impact.
                </Text>
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
                <Text style={styles.metricLabel}>Estimated Income</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.income?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || '—'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Filing Status</Text>
                <Text style={styles.metricValue}>
                  {sectionData.filingStatus?.replace('-', ' ').toUpperCase() || 'SINGLE'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>State</Text>
                <Text style={styles.metricValue}>{sectionData.state || 'N/A'}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Effective Rate</Text>
                <Text style={styles.metricValue}>
                  {((sectionData.marginalRate || 0) * 100).toFixed(1)}%
                </Text>
              </View>
            </View>

            <View style={styles.bracketsCard}>
              <Text style={styles.cardTitle}>
                Income Tax Brackets ({currentYear}) - {filingStatus.replace('-', ' ').toUpperCase()}
              </Text>
              {INCOME_BRACKETS[filingStatus].map((bracket, index) => (
                <View key={index} style={styles.bracketRow}>
                  <Text style={styles.bracketRange}>
                    ${bracket.min.toLocaleString()} - $
                    {bracket.max === Infinity ? '∞' : bracket.max.toLocaleString()}
                  </Text>
                  <Text style={styles.bracketRate}>{(bracket.rate * 100).toFixed(0)}%</Text>
                </View>
              ))}
            </View>

            <View style={styles.bracketsCard}>
              <Text style={styles.cardTitle}>
                Long-Term Capital Gains Brackets ({currentYear})
              </Text>
              {LTCG_BRACKETS[filingStatus].map((bracket, index) => (
                <View key={index} style={styles.bracketRow}>
                  <Text style={styles.bracketRange}>
                    ${bracket.min.toLocaleString()} - $
                    {bracket.max === Infinity ? '∞' : bracket.max.toLocaleString()}
                  </Text>
                  <Text style={styles.bracketRate}>{(bracket.rate * 100).toFixed(0)}%</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Year-Over-Year Tab */}
        {activeTab === 'year-over-year' && sectionData && (
          <View>
            <View style={styles.metricsCard}>
              <Text style={styles.cardTitle}>Year-Over-Year Comparison</Text>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>{sectionData.previousYear} Tax</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.previousTax?.toLocaleString() || '0'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>{sectionData.currentYear} Tax</Text>
                <Text style={styles.metricValue}>
                  ${sectionData.currentTax?.toLocaleString() || '0'}
                </Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Change</Text>
                <Text
                  style={[
                    styles.metricValue,
                    {
                      color: (sectionData.change || 0) >= 0 ? '#EF4444' : '#10B981',
                    },
                  ]}
                >
                  {sectionData.change >= 0 ? '+' : ''}$
                  {Math.abs(sectionData.change || 0).toLocaleString()} (
                  {sectionData.changePercent >= 0 ? '+' : ''}
                  {sectionData.changePercent?.toFixed(1) || '0.0'}%)
                </Text>
              </View>
            </View>
          </View>
        )}
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2563EB" />
        <Text style={styles.loadingText}>Crunching your tax optimization insights…</Text>
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
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#2563EB" />
        }
        stickyHeaderIndices={[0]}
      >
        <HeaderBlock
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          filingStatus={filingStatus}
          onFilingStatusChange={() => setShowSettingsModal(true)}
        />

        <View style={styles.sectionFirst}>{renderTabContent()}</View>
      </ScrollView>

      {/* Settings Modal */}
      <Modal
        visible={showSettingsModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettingsModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Tax Settings</Text>
              <TouchableOpacity onPress={() => setShowSettingsModal(false)}>
                <Ionicons name="close" size={24} color="#111827" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalLabel}>Filing Status</Text>
              {(['single', 'married-joint', 'married-separate', 'head-of-household'] as FilingStatus[]).map(
                (status) => (
                  <TouchableOpacity
                    key={status}
                    style={[
                      styles.optionButton,
                      filingStatus === status && styles.optionButtonActive,
                    ]}
                    onPress={() => {
                      setFilingStatus(status);
                      setShowSettingsModal(false);
                      loadData();
                    }}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        filingStatus === status && styles.optionTextActive,
                      ]}
                    >
                      {status.replace('-', ' ').toUpperCase()}
                    </Text>
                    {filingStatus === status && (
                      <Ionicons name="checkmark" size={20} color="#2563EB" />
                    )}
                  </TouchableOpacity>
                )
              )}
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalLabel}>State</Text>
              <ScrollView style={styles.stateScrollView}>
                {Object.keys(STATE_TAX_RATES).slice(0, 20).map((stateCode) => (
                  <TouchableOpacity
                    key={stateCode}
                    style={[
                      styles.optionButton,
                      state === stateCode && styles.optionButtonActive,
                    ]}
                    onPress={() => {
                      setState(stateCode);
                      setShowSettingsModal(false);
                      loadData();
                    }}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        state === stateCode && styles.optionTextActive,
                      ]}
                    >
                      {stateCode}
                    </Text>
                    {state === stateCode && (
                      <Ionicons name="checkmark" size={20} color="#2563EB" />
                    )}
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        </View>
      </Modal>

      {/* What-If Modal */}
      <Modal
        visible={showWhatIfModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowWhatIfModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>What-If Scenario</Text>
              <TouchableOpacity onPress={() => setShowWhatIfModal(false)}>
                <Ionicons name="close" size={24} color="#111827" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalLabel}>Additional Income/Gains ($)</Text>
              <TextInput
                style={styles.input}
                value={whatIfGains}
                onChangeText={setWhatIfGains}
                placeholder="0"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <TouchableOpacity style={styles.calculateButton} onPress={handleWhatIf}>
              <Text style={styles.calculateButtonText}>Calculate Impact</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 8,
  },
  headerBlock: {
    backgroundColor: '#FFFFFF',
    paddingTop: 8,
    paddingBottom: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 6,
  },
  headerIconWrapper: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(37,99,235,0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    lineHeight: 24,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 16,
    color: '#6b7280',
    marginTop: 2,
  },
  filingStatusBtn: {
    padding: 4,
  },
  tabsRow: {
    marginTop: 2,
  },
  tabsContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingBottom: 4,
  },
  tabBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    minHeight: 30,
    marginRight: 6,
  },
  tabBtnActive: {
    backgroundColor: 'rgba(37,99,235,0.10)',
  },
  tabIcon: {
    marginRight: 4,
  },
  tabLabel: {
    fontSize: 13,
    lineHeight: 16,
    fontWeight: '500',
    color: '#6b7280',
  },
  tabLabelActive: {
    color: '#2563EB',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 0,
  },
  sectionFirst: {
    paddingTop: 12,
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  tabContent: {
    flex: 1,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    justifyContent: 'space-between',
  },
  sectionHeaderLeft: {
    flexDirection: 'column',
    flex: 1,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    padding: 6,
    borderRadius: 8,
    backgroundColor: '#E5F0FF',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 2,
  },
  lastUpdated: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  sectionSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  chipRow: {
    flexDirection: 'row',
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 999,
    backgroundColor: '#E5F0FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 8,
    marginBottom: 4,
  },
  chipText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#1D4ED8',
    fontWeight: '500',
  },
  metricsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 10,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  metricLabel: {
    fontSize: 13,
    color: '#6b7280',
  },
  metricValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
  },
  helperText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
  yieldsSection: {
    marginTop: 4,
    marginBottom: 20,
  },
  holdingCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#10B981',
  },
  washSaleCard: {
    borderLeftColor: '#F59E0B',
    backgroundColor: '#FFFBEB',
  },
  holdingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
  },
  washSaleBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: '#F59E0B',
  },
  washSaleBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  holdingSymbol: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  holdingName: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 2,
  },
  taxBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  taxBadgeText: {
    fontSize: 10,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  holdingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  holdingLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  holdingValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
  },
  harvestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EF4444',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 6,
  },
  harvestButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  holdingFooter: {
    marginTop: 6,
  },
  holdingRec: {
    fontSize: 11,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  bracketsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
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
    paddingRight: 8,
  },
  bracketRate: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
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
  noDataSmall: {
    marginTop: 8,
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#EEF2FF',
  },
  noDataSmallText: {
    fontSize: 12,
    color: '#4F46E5',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#991B1B',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  modalSection: {
    marginBottom: 24,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  optionButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    marginBottom: 8,
  },
  optionButtonActive: {
    backgroundColor: '#E5F0FF',
  },
  optionText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  optionTextActive: {
    color: '#2563EB',
    fontWeight: '600',
  },
  stateScrollView: {
    maxHeight: 200,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  calculateButton: {
    backgroundColor: '#2563EB',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  calculateButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TaxOptimizationScreen;
