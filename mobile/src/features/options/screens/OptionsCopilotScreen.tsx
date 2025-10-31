/**
 * Options Copilot Screen — RichesReach AI Hedge-Fund Edition
 * Adaptive AI Options Strategy Engine
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Dimensions,
  FlatList,
} from 'react-native';
import { useQuery, NetworkStatus } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { gql } from '@apollo/client';
import { LineChart } from 'react-native-chart-kit';

import OptionsCopilotService from '../services/OptionsCopilotService';
import {
  OptionsCopilotRequest,
  OptionsStrategy,
} from '../types/OptionsCopilotTypes';

const { width } = Dimensions.get('window');

// GraphQL — minimal set for performance
const GET_OPTIONS_CHAIN = gql`
  query GetOptionsChain($symbol: String!) {
    optionsChain(symbol: $symbol) {
      symbol
      underlyingPrice
      calls {
        strike
        impliedVolatility
        delta
        gamma
      }
      puts {
        strike
        impliedVolatility
        delta
        gamma
      }
    }
  }
`;

export default function OptionsCopilotScreen({ navigation }: any) {
  const [symbol, setSymbol] = useState('AAPL');
  const [riskTolerance, setRiskTolerance] = useState<'low' | 'medium' | 'high'>('medium');
  const [marketOutlook, setMarketOutlook] = useState<'bullish' | 'bearish' | 'neutral'>('neutral');
  const [accountValue, setAccountValue] = useState(25000);
  const [maxRisk, setMaxRisk] = useState(1000);
  const [recommendations, setRecommendations] = useState<OptionsStrategy[]>([]);
  const [selected, setSelected] = useState<OptionsStrategy | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const { data, refetch, networkStatus } = useQuery(GET_OPTIONS_CHAIN, {
    variables: { symbol },
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-and-network',
  });

  const logEvent = useCallback((event: string, meta?: any) => {
    console.log(JSON.stringify({ event, meta, t: new Date().toISOString() }));
  }, []);

  const loadAI = useCallback(async () => {
    try {
      setLoading(true);
      logEvent('options_copilot_request', { symbol, riskTolerance, marketOutlook });
      const req: OptionsCopilotRequest = {
        symbol,
        riskTolerance,
        marketOutlook,
        accountValue,
        maxRisk,
      };
      const resp = await OptionsCopilotService.getRecommendations(req);
      setRecommendations(resp.recommendedStrategies);
      logEvent('options_copilot_success', { count: resp.recommendedStrategies.length });
    } catch (e) {
      Alert.alert('Error', 'Failed to load AI strategies');
      logEvent('options_copilot_error', { error: e?.message });
    } finally {
      setLoading(false);
    }
  }, [symbol, riskTolerance, marketOutlook, accountValue, maxRisk]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([refetch(), loadAI()]);
    setRefreshing(false);
  }, [refetch, loadAI]);

  const handleTrade = useCallback(
    (s: OptionsStrategy) => {
      const riskPercent = (s.expectedPayoff.maxLoss / accountValue) * 100;
      if (riskPercent > 10) {
        Alert.alert('Risk Alert', `This trade risks ${riskPercent.toFixed(1)}% of your capital`);
        return;
      }
      navigation.navigate('Trading', { screen: 'Order', params: { strategy: s } });
    },
    [accountValue, navigation],
  );

  const renderSelector = (label: string, values: string[], selectedValue: string, setter: any) => (
    <View style={styles.selectorContainer}>
      <Text style={styles.selectorLabel}>{label}</Text>
      <View style={styles.selectorRow}>
        {values.map((v) => (
          <TouchableOpacity
            key={v}
            style={[styles.selectorButton, selectedValue === v && styles.selectorButtonActive]}
            onPress={() => setter(v)}
          >
            <Text style={[styles.selectorButtonText, selectedValue === v && styles.selectorButtonTextActive]}>
              {v[0].toUpperCase() + v.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderChart = useMemo(() => {
    if (!selected) return null;
    const xs = Array.from({ length: 11 }, (_, i) => i - 5);
    const ys = xs.map((x) => selected.expectedPayoff.expectedValue + x * selected.greeks.delta * 10);
    return (
      <LineChart
        data={{
          labels: xs.map((x) => (x * 5).toString()),
          datasets: [{ data: ys }],
        }}
        width={width - 32}
        height={180}
        chartConfig={{
          backgroundColor: '#fff',
          color: () => '#00cc99',
          labelColor: () => '#8E8E93',
        }}
        bezier
        style={{ borderRadius: 8, marginVertical: 12 }}
      />
    );
  }, [selected]);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-left" size={22} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Advanced</Text>
        <TouchableOpacity onPress={loadAI} disabled={loading}>
          <Icon name="refresh-ccw" size={20} color="#00cc99" />
        </TouchableOpacity>
      </View>

      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        {/* Input Row */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.symbolInput}
            value={symbol}
            onChangeText={setSymbol}
            autoCapitalize="characters"
          />
          <TextInput
            style={styles.numberInput}
            value={accountValue.toString()}
            keyboardType="numeric"
            onChangeText={(t) => setAccountValue(parseFloat(t) || 0)}
            placeholder="Account Value"
          />
        </View>

        {renderSelector('Risk Tolerance', ['low', 'medium', 'high'], riskTolerance, setRiskTolerance)}
        {renderSelector('Market Outlook', ['bullish', 'neutral', 'bearish'], marketOutlook, setMarketOutlook)}

        <TouchableOpacity
          style={[styles.actionBtn, loading && styles.disabledBtn]}
          onPress={loadAI}
          disabled={loading}
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Run AI Scan</Text>}
        </TouchableOpacity>

        {/* Strategies */}
        {recommendations.length > 0 && (
          <View style={styles.strategyList}>
            <Text style={styles.sectionTitle}>AI Strategies ({recommendations.length})</Text>
            {recommendations.map((s) => (
              <TouchableOpacity key={s.id} style={styles.strategyCard} onPress={() => { setSelected(s); setShowModal(true); }}>
                <Text style={styles.strategyName}>{s.name}</Text>
                <Text style={styles.strategyDesc}>{s.description}</Text>
                <View style={styles.metricRow}>
                  <Text style={styles.profit}>▲ ${s.expectedPayoff.maxProfit}</Text>
                  <Text style={styles.loss}>▼ ${s.expectedPayoff.maxLoss}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Strategy Modal */}
      <Modal visible={showModal} animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>{selected?.name}</Text>
            <TouchableOpacity onPress={() => handleTrade(selected!)}>
              <Text style={styles.tradeBtn}>Trade</Text>
            </TouchableOpacity>
          </View>
          <ScrollView contentContainerStyle={{ padding: 16 }}>
            {renderChart}
            <Text style={styles.modalText}>{selected?.description}</Text>
            <Text style={styles.modalSub}>Risk: {selected?.riskExplanation.plainEnglish}</Text>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomColor: '#E5E5EA',
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 18, fontWeight: '600' },
  inputRow: { flexDirection: 'row', padding: 16 },
  symbolInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: 8,
    marginRight: 8,
  },
  numberInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: 8,
  },
  selectorContainer: { paddingHorizontal: 16, marginTop: 12 },
  selectorLabel: { fontSize: 15, fontWeight: '600', marginBottom: 8 },
  selectorRow: { flexDirection: 'row' },
  selectorButton: {
    flex: 1,
    backgroundColor: '#F2F2F7',
    padding: 10,
    marginRight: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  selectorButtonActive: { backgroundColor: '#00cc99' },
  selectorButtonText: { color: '#8E8E93' },
  selectorButtonTextActive: { color: '#fff', fontWeight: '600' },
  actionBtn: {
    margin: 16,
    backgroundColor: '#00cc99',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  disabledBtn: { backgroundColor: '#8E8E93' },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  strategyList: { padding: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8 },
  strategyCard: {
    backgroundColor: '#F2F2F7',
    padding: 14,
    borderRadius: 10,
    marginBottom: 12,
  },
  strategyName: { fontSize: 16, fontWeight: '600' },
  strategyDesc: { fontSize: 13, color: '#8E8E93', marginVertical: 6 },
  metricRow: { flexDirection: 'row', justifyContent: 'space-between' },
  profit: { color: '#00cc99', fontWeight: '600' },
  loss: { color: '#FF3B30', fontWeight: '600' },
  modal: { flex: 1, backgroundColor: '#fff' },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomColor: '#E5E5EA',
    borderBottomWidth: 1,
  },
  modalTitle: { fontSize: 18, fontWeight: '600' },
  tradeBtn: { color: '#00cc99', fontWeight: '700' },
  modalText: { fontSize: 15, color: '#8E8E93', marginVertical: 12 },
  modalSub: { fontSize: 14, color: '#000' },
});