import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Dimensions } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useFocusEffect } from '@react-navigation/native';
import { useQuery, gql } from '@apollo/client';
import StockChart from '../components/StockChart';
import StockTradingModal from '../../../components/forms/StockTradingModal';
import logger from '../../../utils/logger';

const GET_STOCK_QUOTE = gql`
  query GetStockQuote($symbol: String!) {
    stockQuote(symbol: $symbol) {
      symbol
      currentPrice
      change
      changePercent
    }
  }
`;

type PriceChartParams = {
  symbol: string;
  tradeModal?: boolean;
  analysisModal?: boolean;
  _ts?: number;
};

interface NavigationParams {
  tradeModal?: boolean | undefined;
  analysisModal?: boolean | undefined;
  _ts?: number | undefined;
  [key: string]: unknown;
}

interface PriceChartScreenProps {
  navigation: {
    goBack: () => void;
    setParams: (params: NavigationParams) => void;
  };
  route: {
    params?: PriceChartParams;
  };
}

const { width: screenWidth } = Dimensions.get('window');

export default function PriceChartScreen({ navigation, route }: PriceChartScreenProps) {
  const { symbol, tradeModal, analysisModal, _ts } = (route.params || {}) as PriceChartParams;
  
  logger.log('🔍 PriceChartScreen mounted with params:', { symbol, tradeModal, analysisModal, _ts });
  
  // Fetch current stock price
  const { data: quoteData } = useQuery(GET_STOCK_QUOTE, {
    variables: { symbol },
    errorPolicy: 'ignore',
    fetchPolicy: 'cache-first',
  });
  
  const currentPrice = quoteData?.stockQuote?.currentPrice || 0;
  
  const [tradingModalVisible, setTradingModalVisible] = useState(false);
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const openedRef = React.useRef<number | null>(null);

  const openTradeModal = useCallback(() => {
    logger.log('🔍 Opening trade modal for:', symbol);
    setTradingModalVisible(true);
  }, [symbol]);

  const openAnalysisModal = useCallback(() => {
    logger.log('🔍 Opening analysis modal for:', symbol);
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
          navigation.setParams({ tradeModal: undefined, _ts: undefined });
        });
      }

      // If caller asked to open the analysis modal, do it once per timestamp
      if (analysisModal && _ts && openedRef.current !== _ts) {
        openedRef.current = _ts;
        openAnalysisModal();

        // Clear the param so back/refresh won't auto-open again
        requestAnimationFrame(() => {
          navigation.setParams({ analysisModal: undefined, _ts: undefined });
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
          logger.log('🔍 Closing trading modal');
          setTradingModalVisible(false);
        }}
        symbol={symbol}
        currentPrice={currentPrice}
        companyName={symbol}
      />

      {/* Analysis Modal - Future enhancement: Add stock analysis features */}
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
