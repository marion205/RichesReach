import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  SafeAreaView,
  Dimensions,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

/* ----------------------------- GraphQL ----------------------------- */

const GET_BACKTEST_STRATEGIES = gql`
  query GetBacktestStrategies($isPublic: Boolean) {
    backtestStrategies(isPublic: $isPublic) {
      id
      name
      description
      strategyType
      parameters
      totalReturn
      winRate
      maxDrawdown
      sharpeRatio
      totalTrades
      isPublic
      likesCount
      sharesCount
      createdAt
      user { id username name }
    }
  }
`;

const GET_BACKTEST_RESULTS = gql`
  query GetBacktestResults($strategyId: ID, $limit: Int) {
    backtestResults(strategyId: $strategyId, limit: $limit) {
      id
      symbol
      timeframe
      startDate
      endDate
      initialCapital
      finalCapital
      totalReturn
      annualizedReturn
      maxDrawdown
      sharpeRatio
      sortinoRatio
      calmarRatio
      winRate
      profitFactor
      totalTrades
      winningTrades
      losingTrades
      avgWin
      avgLoss
      createdAt
    }
  }
`;

const RUN_BACKTEST = gql`
  mutation RunBacktest(
    $strategyName: String!
    $symbol: String!
    $startDate: DateTime
    $endDate: DateTime
    $config: BacktestConfigType
    $params: StrategyParamsType
  ) {
    runBacktest(
      strategyName: $strategyName
      symbol: $symbol
      startDate: $startDate
      endDate: $endDate
      config: $config
      params: $params
    ) {
      success
      result {
        totalReturn
        annualizedReturn
        maxDrawdown
        sharpeRatio
        sortinoRatio
        calmarRatio
        winRate
        profitFactor
        totalTrades
        winningTrades
        losingTrades
        avgWin
        avgLoss
        initialCapital
        finalCapital
        equityCurve
        dailyReturns
      }
      errors
    }
  }
`;

/* ------------------------------ Types ------------------------------ */

type TabKey = 'strategies' | 'results' | 'run';

interface UserLite { id: string; username: string; name: string | null; }
interface BacktestStrategy {
  id: string;
  name: string;
  description?: string | null;
  strategyType: string;
  parameters: any;
  totalReturn?: number | null;
  winRate?: number | null;
  maxDrawdown?: number | null;
  sharpeRatio?: number | null;
  totalTrades?: number | null;
  isPublic: boolean;
  likesCount: number;
  sharesCount: number;
  createdAt: string;
  user: UserLite;
}

interface BacktestResult {
  id: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio?: number | null;
  calmarRatio?: number | null;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  avgWin: number;
  avgLoss: number;
  createdAt: string;
}

/* ------------------------------ Helpers ------------------------------ */

const C = {
  bg: '#F9FAFB',
  card: '#FFFFFF',
  line: '#E5E7EB',
  text: '#111827',
  sub: '#6B7280',
  primary: '#3B82F6',
  green: '#10B981',
  red: '#EF4444',
};

const pct = (v?: number | null) =>
  typeof v === 'number' && isFinite(v) ? `${(v * 100).toFixed(2)}%` : 'N/A';

const money = (v?: number | null) =>
  typeof v === 'number' && isFinite(v)
    ? `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '$0.00';

const num = (v?: number | null) =>
  typeof v === 'number' && isFinite(v) ? v.toString() : '—';

const colorForReturn = (v?: number | null) =>
  typeof v === 'number' ? (v > 0 ? C.green : v < 0 ? C.red : C.sub) : C.sub;

const isISODate = (s: string) => /^\d{4}-\d{2}-\d{2}/.test(s);

/* ----------------------------- Component ----------------------------- */

interface BacktestingScreenProps {
  navigateTo?: (screen: string) => void;
}

const BacktestingScreen: React.FC<BacktestingScreenProps> = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('strategies');
  const [selectedStrategy, setSelectedStrategy] = useState<BacktestStrategy | null>(null);
  const [runBacktestModalVisible, setRunBacktestModalVisible] = useState(false);
  const [isRunningBacktest, setIsRunningBacktest] = useState(false);
  const [resultLimit, setResultLimit] = useState(20);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [backtestInputs, setBacktestInputs] = useState({
    strategyName: 'ema_crossover',
    symbol: 'AAPL',
    startDate: '',
    endDate: '',
    initialCapital: '10000',
    commissionPerTrade: '1.0',
    slippagePct: '0.001',
    maxPositionSize: '0.1',
    riskPerTrade: '0.01',
    maxTradesPerDay: '5',
    maxOpenPositions: '10',
  });

  const {
    data: strategiesData,
    loading: strategiesLoading,
    error: strategiesError,
    refetch: refetchStrategies,
    networkStatus: strategiesNetworkStatus,
  } = useQuery<{ backtestStrategies: BacktestStrategy[] }>(GET_BACKTEST_STRATEGIES, {
    variables: { isPublic: true },
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
  });

  const {
    data: resultsData,
    loading: resultsLoading,
    error: resultsError,
    refetch: refetchResults,
  } = useQuery<{ backtestResults: BacktestResult[] }>(GET_BACKTEST_RESULTS, {
    variables: { strategyId: selectedStrategy?.id, limit: 20 }, // Fixed limit to prevent loops
    skip: !selectedStrategy,
    errorPolicy: 'all',
    fetchPolicy: 'cache-first', // Use cache-first to prevent excessive requests
  });

  const [runBacktest] = useMutation(RUN_BACKTEST, { errorPolicy: 'all' });

  const strategies = useMemo(
    () => strategiesData?.backtestStrategies ?? [],
    [strategiesData]
  );
  const results = useMemo(
    () => resultsData?.backtestResults ?? [],
    [resultsData]
  );

  /* -------------------------- Handlers & Validation -------------------------- */

  const updateInput = useCallback((field: string, value: string) => {
    setBacktestInputs((p) => ({ ...p, [field]: value }));
    setErrors((e) => ({ ...e, [field]: '' }));
  }, []);

  const validateInputs = useCallback(() => {
    const e: Record<string, string> = {};
    const {
      strategyName, symbol, startDate, endDate,
      initialCapital, commissionPerTrade, slippagePct, maxPositionSize, riskPerTrade,
      maxTradesPerDay, maxOpenPositions,
    } = backtestInputs;

    if (!strategyName) e.strategyName = 'Select a strategy';
    if (!symbol || symbol.length < 1) e.symbol = 'Enter a symbol';
    if (startDate && !isISODate(startDate)) e.startDate = 'Use YYYY-MM-DD';
    if (endDate && !isISODate(endDate)) e.endDate = 'Use YYYY-MM-DD';

    const mustNum = [
      ['initialCapital', initialCapital],
      ['commissionPerTrade', commissionPerTrade],
      ['slippagePct', slippagePct],
      ['maxPositionSize', maxPositionSize],
      ['riskPerTrade', riskPerTrade],
      ['maxTradesPerDay', maxTradesPerDay],
      ['maxOpenPositions', maxOpenPositions],
    ] as const;

    for (const [k, v] of mustNum) {
      if (v === '' || isNaN(Number(v))) e[k] = 'Enter a valid number';
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  }, [backtestInputs]);

  const openRunModal = useCallback(() => {
    if (validateInputs()) setRunBacktestModalVisible(true);
  }, [validateInputs]);

  const handleRunBacktest = useCallback(async () => {
    if (isRunningBacktest) return;
    if (!validateInputs()) return;

    setIsRunningBacktest(true);
    try {
      const vars = {
        strategyName: backtestInputs.strategyName,
        symbol: backtestInputs.symbol.toUpperCase(),
        startDate: backtestInputs.startDate || undefined,
        endDate: backtestInputs.endDate || undefined,
        config: {
          initialCapital: parseFloat(backtestInputs.initialCapital),
          commissionPerTrade: parseFloat(backtestInputs.commissionPerTrade),
          slippagePct: parseFloat(backtestInputs.slippagePct),
          maxPositionSize: parseFloat(backtestInputs.maxPositionSize),
          riskPerTrade: parseFloat(backtestInputs.riskPerTrade),
          maxTradesPerDay: parseInt(backtestInputs.maxTradesPerDay, 10),
          maxOpenPositions: parseInt(backtestInputs.maxOpenPositions, 10),
        },
        // Optional params; leave empty unless you expose per-strategy params UI
        params: {},
      };

      const res = await runBacktest({ variables: vars });
      const payload = res?.data?.runBacktest;

      if (payload?.success) {
        Alert.alert('Backtest Complete', 'Results are now available.');
        setRunBacktestModalVisible(false);
        setActiveTab('results');
        // Results will be automatically refetched due to the useQuery dependency on selectedStrategy
      } else {
        const firstErr = payload?.errors?.[0] || 'Backtest failed. Please try again.';
        Alert.alert('Error', firstErr);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to run backtest.');
    } finally {
      setIsRunningBacktest(false);
    }
  }, [runBacktest, backtestInputs, isRunningBacktest, selectedStrategy, resultLimit]);

  const loadMoreResults = useCallback(async () => {
    if (!selectedStrategy || resultsLoading || isLoadingMore) return;
    
    setIsLoadingMore(true);
    try {
      const next = resultLimit + 20;
      setResultLimit(next);
      // Manually refetch with the new limit
      await refetchResults({ strategyId: selectedStrategy.id, limit: next });
    } catch (error) {
      console.error('Error loading more results:', error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [resultLimit, selectedStrategy, resultsLoading, isLoadingMore, refetchResults]);

  /* ------------------------------ Renderers ------------------------------ */

  const StrategyCard = useCallback(({ item }: { item: BacktestStrategy }) => {
    return (
      <TouchableOpacity
        testID={`strategy-${item.id}`}
        style={styles.strategyCard}
        onPress={() => setSelectedStrategy(item)}
      >
        <View style={styles.strategyHeader}>
          <View style={styles.strategyInfo}>
            <Text style={styles.strategyName}>{item.name}</Text>
            <Text style={styles.strategyType}>{item.strategyType.replace(/_/g, ' ').toUpperCase()}</Text>
          </View>
          <View style={styles.strategyStats}>
            {typeof item.totalReturn === 'number' && (
              <Text style={[styles.statValue, { color: colorForReturn(item.totalReturn) }]}>{pct(item.totalReturn)}</Text>
            )}
            <Text style={styles.statLabel}>Return</Text>
          </View>
        </View>

        <Text style={styles.strategyDescription} numberOfLines={2}>
          {item.description || 'No description available'}
        </Text>

        <View style={styles.strategyMetrics}>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Win Rate</Text>
            <Text style={styles.metricValue}>{pct(item.winRate)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Sharpe</Text>
            <Text style={styles.metricValue}>{typeof item.sharpeRatio === 'number' ? item.sharpeRatio.toFixed(2) : 'N/A'}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Max DD</Text>
            <Text style={styles.metricValue}>{pct(item.maxDrawdown)}</Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Trades</Text>
            <Text style={styles.metricValue}>{num(item.totalTrades)}</Text>
          </View>
        </View>

        <View style={styles.strategyFooter}>
          <View style={styles.authorInfo}>
            <Text style={styles.authorText}>by {item.user.name || item.user.username}</Text>
          </View>
          <View style={styles.strategyActions}>
            <View style={styles.actionItem}>
              <Icon name="heart" size={16} color={C.sub} />
              <Text style={styles.actionText}>{num(item.likesCount)}</Text>
            </View>
            <View style={styles.actionItem}>
              <Icon name="share-2" size={16} color={C.sub} />
              <Text style={styles.actionText}>{num(item.sharesCount)}</Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  }, []);

  const MemoStrategyCard = React.memo(StrategyCard) as React.ComponentType<{ item: BacktestStrategy }>;

  const ResultCard = useCallback(({ item }: { item: BacktestResult }) => {
    return (
      <View testID={`result-${item.id}`} style={styles.resultCard}>
        <View style={styles.resultHeader}>
          <View style={styles.resultInfo}>
            <Text style={styles.resultSymbol}>{item.symbol}</Text>
            <Text style={styles.resultTimeframe}>{item.timeframe}</Text>
          </View>
          <View style={styles.resultReturn}>
            <Text style={[styles.returnValue, { color: colorForReturn(item.totalReturn) }]}>{pct(item.totalReturn)}</Text>
            <Text style={styles.returnLabel}>Total Return</Text>
          </View>
        </View>

        <View style={styles.resultMetrics}>
          <MetricRow label="Initial Capital" value={money(item.initialCapital)} />
          <MetricRow label="Final Capital" value={money(item.finalCapital)} />
          <MetricRow label="Win Rate" value={pct(item.winRate)} />
          <MetricRow label="Sharpe Ratio" value={typeof item.sharpeRatio === 'number' ? item.sharpeRatio.toFixed(2) : 'N/A'} />
          <MetricRow label="Max Drawdown" value={pct(item.maxDrawdown)} />
          <MetricRow label="Total Trades" value={num(item.totalTrades)} />
        </View>

        <View style={styles.resultFooter}>
          <Text style={styles.resultDate}>{new Date(item.createdAt).toLocaleDateString()}</Text>
          <Text style={styles.resultPeriod}>
            {new Date(item.startDate).toLocaleDateString()} - {new Date(item.endDate).toLocaleDateString()}
          </Text>
        </View>
      </View>
    );
  }, []);
  const MemoResultCard = React.memo(ResultCard) as React.ComponentType<{ item: BacktestResult }>;

  const renderStrategies = useCallback(() => {
    if (strategiesLoading) {
      return <CenteredLoader label="Loading strategies..." />;
    }
    if (strategiesError) {
      return <CenteredError label="Failed to load strategies" onRetry={() => refetchStrategies()} />;
    }
    if (!strategies.length) {
      return (
        <EmptyState
          icon="box"
          title="No strategies yet"
          text="Create or publish a strategy to see it here."
        />
      );
    }
    return (
      <FlatList
        data={strategies}
        keyExtractor={(s) => s.id}
        renderItem={({ item }) => <MemoStrategyCard item={item} />}
        contentContainerStyle={styles.listContent}
        initialNumToRender={6}
        windowSize={8}
        removeClippedSubviews
        testID="strategies-list"
      />
    );
  }, [strategiesLoading, strategiesError, strategies, refetchStrategies, MemoStrategyCard]);

  const renderResults = useCallback(() => {
    if (!selectedStrategy) {
      return (
        <EmptyState
          icon="bar-chart-2"
          title="Select a strategy"
          text="Choose a strategy from the Strategies tab to view results."
        />
      );
    }
    if (resultsLoading && !results.length) {
      return <CenteredLoader label="Loading results..." />;
    }
    if (resultsError && !results.length) {
      return <CenteredError label="Failed to load results" onRetry={() => refetchResults()} />;
    }
    return (
      <View style={{ flex: 1, padding: 20 }}>
        <View style={styles.selectedStrategyHeader}>
          <Text style={styles.selectedStrategyName}>{selectedStrategy.name}</Text>
          <TouchableOpacity style={styles.runBacktestButton} onPress={openRunModal} testID="open-run-modal">
            <Icon name="play" size={16} color="#FFFFFF" />
            <Text style={styles.runBacktestButtonText}>Run Backtest</Text>
          </TouchableOpacity>
        </View>

        <FlatList
          data={results}
          keyExtractor={(r) => r.id}
          renderItem={({ item }) => <MemoResultCard item={item} />}
          contentContainerStyle={styles.listContent}
          ListFooterComponent={
            <View style={{ paddingVertical: 12, alignItems: 'center' }}>
              {resultsLoading ? (
                <ActivityIndicator color={C.primary} />
              ) : (
                <TouchableOpacity 
                  style={styles.loadMoreButton} 
                  onPress={loadMoreResults}
                  disabled={isLoadingMore}
                >
                  <Text style={styles.loadMoreButtonText}>
                    {isLoadingMore ? 'Loading...' : 'Load More Results'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          }
          initialNumToRender={6}
          windowSize={8}
          removeClippedSubviews
          testID="results-list"
        />
      </View>
    );
  }, [
    selectedStrategy,
    resultsLoading,
    resultsError,
    results,
    MemoResultCard,
    openRunModal,
    loadMoreResults,
    isLoadingMore,
  ]);

  const renderRun = useCallback(() => {
    return (
      <View style={{ flex: 1, padding: 20 }}>
        <Text style={styles.sectionTitle}>Strategy Configuration</Text>

        <InputGroup
          label="Strategy Name"
          error={errors.strategyName}
          children={
            <View style={styles.segmentedControl}>
              {(['ema_crossover', 'rsi_mean_reversion', 'breakout'] as const).map((key) => (
                <TouchableOpacity
                  key={key}
                  style={[styles.segmentButton, backtestInputs.strategyName === key && styles.segmentButtonActive]}
                  onPress={() => updateInput('strategyName', key)}
                >
                  <Text style={[styles.segmentButtonText, backtestInputs.strategyName === key && styles.segmentButtonTextActive]}>
                    {key.replace(/_/g, ' ').toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          }
        />

        <InputGroup label="Symbol" error={errors.symbol}>
          <TextInput
            style={styles.input}
            value={backtestInputs.symbol}
            onChangeText={(v) => updateInput('symbol', v.toUpperCase())}
            placeholder="AAPL"
            autoCapitalize="characters"
            testID="input-symbol"
          />
        </InputGroup>

        <InputGroup label="Start Date (optional)" error={errors.startDate}>
          <TextInput
            style={styles.input}
            value={backtestInputs.startDate}
            onChangeText={(v) => updateInput('startDate', v)}
            placeholder="YYYY-MM-DD"
            testID="input-startDate"
          />
        </InputGroup>

        <InputGroup label="End Date (optional)" error={errors.endDate}>
          <TextInput
            style={styles.input}
            value={backtestInputs.endDate}
            onChangeText={(v) => updateInput('endDate', v)}
            placeholder="YYYY-MM-DD"
            testID="input-endDate"
          />
        </InputGroup>

        <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Backtest Configuration</Text>

        <TwoCol>
          <InputGroup label="Initial Capital" error={errors.initialCapital}>
            <TextInput
              style={styles.input}
              value={backtestInputs.initialCapital}
              onChangeText={(v) => updateInput('initialCapital', v)}
              keyboardType="numeric"
              placeholder="10000"
              testID="input-initialCapital"
            />
          </InputGroup>
          <InputGroup label="Commission / Trade" error={errors.commissionPerTrade}>
            <TextInput
              style={styles.input}
              value={backtestInputs.commissionPerTrade}
              onChangeText={(v) => updateInput('commissionPerTrade', v)}
              keyboardType="numeric"
              placeholder="1.0"
              testID="input-commission"
            />
          </InputGroup>
        </TwoCol>

        <TwoCol>
          <InputGroup label="Slippage %" error={errors.slippagePct}>
            <TextInput
              style={styles.input}
              value={backtestInputs.slippagePct}
              onChangeText={(v) => updateInput('slippagePct', v)}
              keyboardType="numeric"
              placeholder="0.001"
              testID="input-slippage"
            />
          </InputGroup>
          <InputGroup label="Max Position Size" error={errors.maxPositionSize}>
            <TextInput
              style={styles.input}
              value={backtestInputs.maxPositionSize}
              onChangeText={(v) => updateInput('maxPositionSize', v)}
              keyboardType="numeric"
              placeholder="0.1"
              testID="input-maxpos"
            />
          </InputGroup>
        </TwoCol>

        <TwoCol>
          <InputGroup label="Risk / Trade" error={errors.riskPerTrade}>
            <TextInput
              style={styles.input}
              value={backtestInputs.riskPerTrade}
              onChangeText={(v) => updateInput('riskPerTrade', v)}
              keyboardType="numeric"
              placeholder="0.01"
              testID="input-risk"
            />
          </InputGroup>
          <InputGroup label="Max Trades / Day" error={errors.maxTradesPerDay}>
            <TextInput
              style={styles.input}
              value={backtestInputs.maxTradesPerDay}
              onChangeText={(v) => updateInput('maxTradesPerDay', v)}
              keyboardType="numeric"
              placeholder="5"
              testID="input-maxtrades"
            />
          </InputGroup>
        </TwoCol>

        <InputGroup label="Max Open Positions" error={errors.maxOpenPositions}>
          <TextInput
            style={styles.input}
            value={backtestInputs.maxOpenPositions}
            onChangeText={(v) => updateInput('maxOpenPositions', v)}
            keyboardType="numeric"
            placeholder="10"
            testID="input-maxopen"
          />
        </InputGroup>

        <TouchableOpacity style={styles.runButton} onPress={openRunModal} testID="run-backtest">
          <Icon name="play" size={20} color="#FFFFFF" />
          <Text style={styles.runButtonText}>Run Backtest</Text>
        </TouchableOpacity>
      </View>
    );
  }, [backtestInputs, errors, updateInput, openRunModal]);

  /* ------------------------------ Main Render ------------------------------ */

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo?.('swing-trading-test')}
        >
          <Icon name="arrow-left" size={24} color="#6B7280" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Backtesting</Text>
      </View>

      <View style={styles.tabBar}>
        {(['strategies','results','run'] as const).map((key) => (
          <TouchableOpacity
            key={key}
            style={[styles.tab, activeTab === key && styles.activeTab]}
            onPress={() => setActiveTab(key)}
            testID={`tab-${key}`}
          >
            <Text style={[styles.tabText, activeTab === key && styles.activeTabText]}>
              {key === 'run' ? 'Run Test' : key[0].toUpperCase() + key.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={{ flex: 1 }}>
        {activeTab === 'strategies' && (
          <View style={styles.tabContent}>{renderStrategies()}</View>
        )}
        {activeTab === 'results' && (
          <View style={styles.tabContent}>{renderResults()}</View>
        )}
        {activeTab === 'run' && (
          <View style={styles.tabContent}>{renderRun()}</View>
        )}
      </View>

      <Modal
        visible={runBacktestModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => !isRunningBacktest && setRunBacktestModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Run Backtest</Text>
              <TouchableOpacity
                onPress={() => !isRunningBacktest && setRunBacktestModalVisible(false)}
                style={styles.closeButton}
                disabled={isRunningBacktest}
                testID="modal-close"
              >
                <Icon name="x" size={24} color={C.sub} />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.modalText}>
                Run {backtestInputs.strategyName.replace(/_/g,' ')} on {backtestInputs.symbol}?
              </Text>
              <Text style={styles.modalSubtext}>This can take a few minutes.</Text>
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setRunBacktestModalVisible(false)}
                disabled={isRunningBacktest}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.confirmButton, isRunningBacktest && styles.disabledButton]}
                onPress={handleRunBacktest}
                disabled={isRunningBacktest}
                testID="modal-confirm-run"
              >
                {isRunningBacktest
                  ? <ActivityIndicator size="small" color="#FFFFFF" />
                  : <Text style={styles.confirmButtonText}>Run Backtest</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

/* ---------------------------- Small Components ---------------------------- */

const MetricRow = ({ label, value }: { label: string; value: string }) => (
  <View style={styles.metricRow}>
    <Text style={styles.metricLabel}>{label}</Text>
    <Text style={styles.metricValue}>{value}</Text>
  </View>
);

const InputGroup = ({
  label, error, children,
}: { label: string; error?: string; children: React.ReactNode }) => (
  <View style={{ marginBottom: 16 }}>
    <Text style={styles.inputLabel}>{label}</Text>
    {children}
    {!!error && <Text style={{ color: C.red, marginTop: 6 }}>{error}</Text>}
  </View>
);

const TwoCol = ({ children }: { children: React.ReactNode }) => (
  <View style={{ flexDirection: 'row', gap: 12 }}>
    <View style={{ flex: 1 }}>{(Array.isArray(children) ? children[0] : children)}</View>
    <View style={{ flex: 1 }}>{(Array.isArray(children) ? children[1] : null)}</View>
  </View>
);

const CenteredLoader = ({ label }: { label: string }) => (
  <View style={styles.loadingContainer}>
    <ActivityIndicator size="large" color={C.primary} />
    <Text style={styles.loadingText}>{label}</Text>
  </View>
);

const CenteredError = ({ label, onRetry }: { label: string; onRetry: () => void }) => (
  <View style={styles.loadingContainer}>
    <Text style={[styles.loadingText, { color: C.red }]}>{label}</Text>
    <TouchableOpacity onPress={onRetry} style={[styles.runBacktestButton, { marginTop: 12 }]}>
      <Icon name="refresh-ccw" size={16} color="#FFFFFF" />
      <Text style={styles.runBacktestButtonText}>Retry</Text>
    </TouchableOpacity>
  </View>
);

const EmptyState = ({ icon, title, text }: { icon: string; title: string; text: string }) => (
  <View style={styles.emptyState}>
    <Icon name={icon as any} size={64} color="#D1D5DB" />
    <Text style={styles.emptyStateTitle}>{title}</Text>
    <Text style={styles.emptyStateText}>{text}</Text>
  </View>
);

/* -------------------------------- Styles -------------------------------- */

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16, backgroundColor: C.card,
    borderBottomWidth: 1, borderBottomColor: C.line,
  },
  backButton: { padding: 8, marginRight: 8 },
  headerTitle: { fontSize: 24, fontWeight: '700', color: C.text },

  tabBar: { flexDirection: 'row', backgroundColor: C.card, borderBottomWidth: 1, borderBottomColor: C.line },
  tab: { flex: 1, paddingVertical: 16, alignItems: 'center' },
  activeTab: { borderBottomWidth: 2, borderBottomColor: C.primary },
  tabText: { fontSize: 16, color: C.sub, fontWeight: '500' },
  activeTabText: { color: C.primary, fontWeight: '600' },

  tabContent: { flex: 1 },
  listContent: { padding: 20 },

  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loadingText: { fontSize: 16, color: C.sub, marginTop: 12 },

  /* Strategy cards */
  strategyCard: {
    backgroundColor: C.card, borderRadius: 12, padding: 16, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1, shadowRadius: 3.84, elevation: 5,
  },
  strategyHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  strategyInfo: { flex: 1 },
  strategyName: { fontSize: 18, fontWeight: '700', color: C.text, marginBottom: 4 },
  strategyType: { fontSize: 12, color: C.sub, backgroundColor: '#F3F4F6', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start' },
  strategyStats: { alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700' },
  statLabel: { fontSize: 12, color: C.sub },
  strategyDescription: { fontSize: 14, color: C.sub, lineHeight: 20, marginBottom: 16 },
  strategyMetrics: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  metricItem: { alignItems: 'center' },
  metricLabel: { fontSize: 12, color: C.sub, marginBottom: 4 },
  metricValue: { fontSize: 14, fontWeight: '600', color: C.text },
  strategyFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  authorInfo: { flex: 1 },
  authorText: { fontSize: 12, color: C.sub },
  strategyActions: { flexDirection: 'row' },
  actionItem: { flexDirection: 'row', alignItems: 'center', marginLeft: 16 },
  actionText: { fontSize: 12, color: C.sub, marginLeft: 4 },

  /* Empty state */
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 32 },
  emptyStateTitle: { fontSize: 20, fontWeight: '600', color: '#374151', marginTop: 16, marginBottom: 8 },
  emptyStateText: { fontSize: 16, color: C.sub, textAlign: 'center', lineHeight: 24 },

  /* Results */
  selectedStrategyHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 12, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: C.line,
  },
  selectedStrategyName: { 
    fontSize: 20, 
    fontWeight: '700', 
    color: C.text, 
    flex: 1, 
    marginRight: 12,
    flexWrap: 'wrap'
  },
  runBacktestButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: C.primary, 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 6,
    flexShrink: 0
  },
  runBacktestButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF', marginLeft: 4 },
  loadMoreButton: { backgroundColor: C.primary, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  loadMoreButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF' },

  resultCard: {
    backgroundColor: C.card, borderRadius: 12, padding: 16, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 3.84, elevation: 5,
  },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  resultInfo: { flexDirection: 'row', alignItems: 'center' },
  resultSymbol: { fontSize: 18, fontWeight: '700', color: C.text, marginRight: 8 },
  resultTimeframe: { fontSize: 12, color: C.sub, backgroundColor: '#F3F4F6', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  resultReturn: { alignItems: 'center' },
  returnValue: { fontSize: 20, fontWeight: '700' },
  returnLabel: { fontSize: 12, color: C.sub },
  resultMetrics: { marginBottom: 16 },
  metricRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 4 },
  resultFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  resultDate: { fontSize: 12, color: C.sub },
  resultPeriod: { fontSize: 12, color: C.sub },

  /* Inputs */
  sectionTitle: { fontSize: 18, fontWeight: '600', color: C.text, marginBottom: 12 },
  inputLabel: { fontSize: 14, fontWeight: '500', color: '#374151', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 12, fontSize: 16, color: C.text, backgroundColor: C.card },
  segmentedControl: { flexDirection: 'row', backgroundColor: '#F3F4F6', borderRadius: 8, padding: 4, marginBottom: 8 },
  segmentButton: { flex: 1, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6, alignItems: 'center' },
  segmentButtonActive: { backgroundColor: C.primary },
  segmentButtonText: { fontSize: 12, fontWeight: '500', color: C.sub },
  segmentButtonTextActive: { color: '#FFFFFF' },

  runButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: C.primary, paddingVertical: 16, borderRadius: 8, marginTop: 8 },
  runButtonText: { fontSize: 16, fontWeight: '600', color: '#FFFFFF', marginLeft: 8 },

  /* Modal */
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { backgroundColor: C.card, borderRadius: 12, padding: 20, width: width * 0.9, maxWidth: 420 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { fontSize: 18, fontWeight: '600', color: C.text },
  closeButton: { padding: 4 },
  modalBody: { marginBottom: 20 },
  modalText: { fontSize: 16, color: '#374151', marginBottom: 8 },
  modalSubtext: { fontSize: 14, color: C.sub },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end' },
  cancelButton: { paddingHorizontal: 16, paddingVertical: 8, marginRight: 12 },
  cancelButtonText: { fontSize: 16, color: C.sub },
  confirmButton: { backgroundColor: C.primary, paddingHorizontal: 16, paddingVertical: 8, borderRadius: 6, minWidth: 120, alignItems: 'center' },
  disabledButton: { backgroundColor: '#9CA3AF' },
  confirmButtonText: { fontSize: 16, fontWeight: '600', color: '#FFFFFF' },
});

export default BacktestingScreen;