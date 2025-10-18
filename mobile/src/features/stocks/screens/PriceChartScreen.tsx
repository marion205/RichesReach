import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Dimensions } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useFocusEffect } from '@react-navigation/native';
import StockChart from '../components/StockChart';
import StockTradingModal from '../../../components/forms/StockTradingModal';

type PriceChartParams = {
  symbol: string;
  tradeModal?: boolean;
  analysisModal?: boolean;
  _ts?: number;
};

interface PriceChartScreenProps {
  navigation: any;
  route: {
    params?: PriceChartParams;
  };
}

const { width: screenWidth } = Dimensions.get('window');

export default function PriceChartScreen({ navigation, route }: PriceChartScreenProps) {
  const { symbol, tradeModal, analysisModal, _ts } = (route.params || {}) as PriceChartParams;
  
  console.log('🔍 PriceChartScreen mounted with params:', { symbol, tradeModal, analysisModal, _ts });
  
  const [tradingModalVisible, setTradingModalVisible] = useState(false);
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const openedRef = React.useRef<number | null>(null);

  const openTradeModal = useCallback(() => {
    console.log('🔍 Opening trade modal for:', symbol);
    setTradingModalVisible(true);
  }, [symbol]);

  const openAnalysisModal = useCallback(() => {
    console.log('🔍 Opening analysis modal for:', symbol);
    setAnalysisModalVisible(true);
  }, [symbol]);

  useFocusEffect(
    useCallback(() => {
      // If caller asked to open the trade modal, do it once per timestamp
      if (tradeModal && _ts && openedRef.current !== _ts) {
        openedRef.current = _ts;
        openTradeModal();

        // Clear the param so back/refresh won't auto-open again
        requestAnimationFrame(() => {
          navigation.setParams({ tradeModal: undefined, _ts: undefined } as any);
        });
      }

      // If caller asked to open the analysis modal, do it once per timestamp
      if (analysisModal && _ts && openedRef.current !== _ts) {
        openedRef.current = _ts;
        openAnalysisModal();

        // Clear the param so back/refresh won't auto-open again
        requestAnimationFrame(() => {
          navigation.setParams({ analysisModal: undefined, _ts: undefined } as any);
        });
      }
    }, [tradeModal, analysisModal, _ts, navigation, openTradeModal, openAnalysisModal])
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          onPress={() => navigation.goBack()}
          style={styles.backButton}
        >
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.title}>Price Chart - {symbol}</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Chart Content */}
      <View style={styles.chartContainer}>
        <StockChart
          symbol={symbol}
          embedded={false}
          width={screenWidth - 40}
          height={400}
        />
      </View>

      {/* Trade Modal */}
      <StockTradingModal
        visible={tradingModalVisible}
        onClose={() => {
          console.log('🔍 Closing trading modal');
          setTradingModalVisible(false);
        }}
        symbol={symbol}
        currentPrice={150.00} // TODO: Get actual current price
        companyName={symbol}
      />

      {/* Analysis Modal - TODO: Implement analysis modal */}
      <Modal
        visible={analysisModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setAnalysisModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <TouchableOpacity 
                onPress={() => setAnalysisModalVisible(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#374151" />
              </TouchableOpacity>
              <Text style={styles.modalTitle}>Advanced Analysis - {symbol}</Text>
              <View style={{ width: 24 }} />
            </View>
            <View style={styles.modalContent}>
              <Text style={styles.placeholderText}>
                Advanced Analysis for {symbol} will be implemented here.
              </Text>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 5,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  chartContainer: {
    flex: 1,
    padding: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    backgroundColor: '#F9FAFB',
    borderRadius: 20,
    padding: 20,
    width: '90%',
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  closeButton: {
    padding: 5,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  modalContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
});
