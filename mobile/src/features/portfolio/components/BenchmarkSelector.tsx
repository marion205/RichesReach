import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  FlatList,
  useColorScheme,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQuery } from '@apollo/client';
import { GET_AVAILABLE_BENCHMARKS, formatBenchmarkSymbol, getBenchmarkColor } from '../../../graphql/benchmarkQueries';
import logger from '../../../utils/logger';

const PREF_BENCHMARK_SYMBOL = 'rr.pref.benchmark_symbol';

interface BenchmarkSelectorProps {
  selectedSymbol: string;
  onSymbolChange: (symbol: string) => void;
  style?: any;
}

interface BenchmarkOption {
  symbol: string;
  name: string;
  color: string;
}

export default function BenchmarkSelector({ 
  selectedSymbol, 
  onSymbolChange, 
  style 
}: BenchmarkSelectorProps) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const [showModal, setShowModal] = useState(false);

  // Get available benchmarks from GraphQL with error handling
  const { data: availableBenchmarksData, error: benchmarksError } = useQuery(GET_AVAILABLE_BENCHMARKS, {
    errorPolicy: 'all', // Continue rendering even if query has errors
    onError: (error) => {
      logger.warn('Available benchmarks query error:', error);
    },
  });

  // Load saved benchmark preference
  useEffect(() => {
    const loadBenchmarkPreference = async () => {
      try {
        const saved = await AsyncStorage.getItem(PREF_BENCHMARK_SYMBOL);
        if (saved && availableBenchmarksData?.availableBenchmarks?.includes(saved)) {
          onSymbolChange(saved);
        }
      } catch (error) {
        logger.error('Error loading benchmark preference:', error);
      }
    };
    loadBenchmarkPreference();
  }, [availableBenchmarksData, onSymbolChange]);

  // Save benchmark preference
  const handleSymbolChange = async (symbol: string) => {
    onSymbolChange(symbol);
    setShowModal(false);
    try {
      await AsyncStorage.setItem(PREF_BENCHMARK_SYMBOL, symbol);
    } catch (error) {
      logger.error('Error saving benchmark preference:', error);
    }
  };

  const availableBenchmarks = availableBenchmarksData?.availableBenchmarks || [
    'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD', 'SLV'
  ];

  const benchmarkOptions: BenchmarkOption[] = availableBenchmarks.map(symbol => ({
    symbol,
    name: formatBenchmarkSymbol(symbol),
    color: getBenchmarkColor(symbol, isDark),
  }));

  const palette = {
    bg: isDark ? '#111214' : '#FFFFFF',
    text: isDark ? '#F5F6F8' : '#1C1C1E',
    sub: isDark ? '#A1A7AF' : '#6B7280',
    border: isDark ? '#23262B' : '#E5E7EB',
    modalBg: isDark ? '#1C1F24' : '#FFFFFF',
    modalOverlay: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(0, 0, 0, 0.5)',
  };

  const renderBenchmarkOption = ({ item }: { item: BenchmarkOption }) => (
    <TouchableOpacity
      style={[
        styles.optionItem,
        {
          backgroundColor: palette.bg,
          borderColor: palette.border,
        },
        selectedSymbol === item.symbol && {
          backgroundColor: isDark ? '#2B2F36' : '#F3F4F6',
        },
      ]}
      onPress={() => handleSymbolChange(item.symbol)}
    >
      <View style={styles.optionContent}>
        <View style={[styles.colorSwatch, { backgroundColor: item.color }]} />
        <View style={styles.optionText}>
          <Text style={[styles.optionSymbol, { color: palette.text }]}>
            {item.symbol}
          </Text>
          <Text style={[styles.optionName, { color: palette.sub }]}>
            {item.name}
          </Text>
        </View>
        {selectedSymbol === item.symbol && (
          <Icon name="check" size={20} color={palette.text} />
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <>
      <TouchableOpacity
        style={[
          styles.selector,
          {
            backgroundColor: palette.bg,
            borderColor: palette.border,
          },
          style,
        ]}
        onPress={() => setShowModal(true)}
      >
        <View style={styles.selectorContent}>
          <View style={[styles.colorSwatch, { backgroundColor: getBenchmarkColor(selectedSymbol, isDark) }]} />
          <View style={styles.selectorText}>
            <Text style={[styles.selectorSymbol, { color: palette.text }]}>
              {selectedSymbol}
            </Text>
            <Text style={[styles.selectorName, { color: palette.sub }]}>
              {formatBenchmarkSymbol(selectedSymbol)}
            </Text>
          </View>
          <Icon name="chevron-down" size={16} color={palette.sub} />
        </View>
      </TouchableOpacity>

      <Modal
        visible={showModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={[styles.modalOverlay, { backgroundColor: palette.modalOverlay }]}>
          <View style={[styles.modal, { backgroundColor: palette.modalBg }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: palette.text }]}>
                Select Benchmark
              </Text>
              <TouchableOpacity
                onPress={() => setShowModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color={palette.sub} />
              </TouchableOpacity>
            </View>

            <FlatList
              data={benchmarkOptions}
              renderItem={renderBenchmarkOption}
              keyExtractor={(item) => item.symbol}
              style={styles.optionsList}
              showsVerticalScrollIndicator={false}
            />
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  selector: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    maxWidth: 100,
  },
  selectorContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  colorSwatch: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  selectorText: {
    flex: 1,
  },
  selectorSymbol: {
    fontSize: 12,
    fontWeight: '600',
  },
  selectorName: {
    fontSize: 10,
    marginTop: 1,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modal: {
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
    borderRadius: 16,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  closeButton: {
    padding: 4,
  },
  optionsList: {
    maxHeight: 400,
  },
  optionItem: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionText: {
    flex: 1,
    marginLeft: 8,
  },
  optionSymbol: {
    fontSize: 16,
    fontWeight: '600',
  },
  optionName: {
    fontSize: 14,
    marginTop: 2,
  },
});
