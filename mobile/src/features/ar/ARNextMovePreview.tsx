import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useQuery } from '@apollo/client';
import { LinearGradient } from 'expo-linear-gradient';
import { GET_MY_PORTFOLIOS } from '../../portfolioQueries';
import Icon from 'react-native-vector-icons/Feather';
import logger from '../../utils/logger';

const { width, height } = Dimensions.get('window');

export default function ARNextMovePreview() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  
  // Get portfolio data from route params or fetch it
  const { data: portfolioData } = useQuery(GET_MY_PORTFOLIOS, {
    errorPolicy: 'all',
    fetchPolicy: 'cache-first',
  });

  // Get portfolio from route params or use the first portfolio from query
  const routePortfolio = route?.params?.portfolio;
  const queryPortfolios = portfolioData?.myPortfolios?.portfolios || [];
  const firstPortfolio = queryPortfolios.length > 0 ? queryPortfolios[0] : null;
  
  // Use route portfolio, first query portfolio, or create demo portfolio
  const portfolio = routePortfolio || firstPortfolio || {
    name: 'Main Portfolio',
    totalValue: 14303.52,
    holdingsCount: 3,
    holdings: [
      { id: 'h1', stock: { symbol: 'AAPL' }, shares: 10, averagePrice: 150, currentPrice: 180, totalValue: 1800 },
      { id: 'h2', stock: { symbol: 'MSFT' }, shares: 8, averagePrice: 230, currentPrice: 320, totalValue: 2560 },
      { id: 'h3', stock: { symbol: 'SPY' }, shares: 15, averagePrice: 380, currentPrice: 420, totalValue: 6300 },
    ],
  };

  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationData, setSimulationData] = useState<any>(null);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Start entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Start rotation animation
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 10000,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const startSimulation = async () => {
    setIsSimulating(true);
    
    // Simulate AR processing
    setTimeout(() => {
      setSimulationData({
        projectedValue: portfolio.totalValue * 1.15,
        growthRate: 15.2,
        riskScore: 7.8,
        recommendations: [
          'Consider increasing tech allocation',
          'Rebalance international exposure',
          'Add defensive positions',
        ],
      });
      setIsSimulating(false);
    }, 3000);
  };

  const handleTrade = (action: string) => {
    navigation.navigate('Stocks', { action, portfolio });
  };

  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <SafeAreaView style={styles.container}>
      {/* AR Background Simulation */}
      <View style={styles.arBackground}>
        <Animated.View
          style={[
            styles.arOverlay,
            {
              opacity: fadeAnim,
              transform: [
                { scale: scaleAnim },
                { rotate: rotateInterpolate },
              ],
            },
          ]}
        >
          <Text style={styles.arTitle}>AR Portfolio Preview</Text>
          <Text style={styles.arSubtitle}>Immersive 3D Visualization</Text>
        </Animated.View>
      </View>

      {/* Portfolio Data Overlay */}
      <Animated.View
        style={[
          styles.contentOverlay,
          {
            opacity: fadeAnim,
          },
        ]}
      >
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Portfolio Summary */}
          <View style={styles.portfolioCard}>
            <Text style={styles.portfolioTitle}>{portfolio.name}</Text>
            <Text style={styles.portfolioValue}>
              ${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0.00'}
            </Text>
            <Text style={styles.portfolioSubtext}>
              {portfolio.holdingsCount || portfolio.holdings?.length || 0} Holdings
            </Text>
          </View>

          {/* Simulation Results */}
          {simulationData && (
            <View style={styles.simulationCard}>
              <Text style={styles.simulationTitle}>Projected Analysis</Text>
              <Text style={styles.simulationValue}>
                ${simulationData.projectedValue.toLocaleString()}
              </Text>
              <Text style={styles.simulationGrowth}>
                +{simulationData.growthRate}% Growth Potential
              </Text>
              <Text style={styles.simulationRisk}>Risk Score: {simulationData.riskScore}/10</Text>
              
              <View style={styles.recommendationsContainer}>
                <Text style={styles.recommendationsTitle}>Recommendations:</Text>
                {simulationData.recommendations.map((rec: string, index: number) => (
                  <Text key={index} style={styles.recommendationItem}>• {rec}</Text>
                ))}
              </View>
            </View>
          )}

          {/* Holdings List */}
          {portfolio.holdings && portfolio.holdings.length > 0 && (
            <View style={styles.holdingsCard}>
              <Text style={styles.holdingsTitle}>Portfolio Holdings</Text>
              {portfolio.holdings.map((holding: any) => (
                <View key={holding.id} style={styles.holdingItem}>
                  <Text style={styles.holdingSymbol}>{holding.stock?.symbol}</Text>
                  <Text style={styles.holdingShares}>{holding.shares} shares</Text>
                  <Text style={styles.holdingValue}>
                    ${holding.totalValue?.toLocaleString() || '0'}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.simulateButton}
              onPress={startSimulation}
              disabled={isSimulating}
            >
              <LinearGradient
                colors={['#667eea', '#764ba2']}
                style={styles.buttonGradient}
              >
                <Text style={styles.buttonText}>
                  {isSimulating ? 'Simulating...' : 'Start AR Simulation'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.tradeButton}
              onPress={() => handleTrade('buy')}
            >
              <LinearGradient
                colors={['#34C759', '#30D158']}
                style={styles.buttonGradient}
              >
                <Text style={styles.buttonText}>Simulate Buy</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.tradeButton}
              onPress={() => handleTrade('sell')}
            >
              <LinearGradient
                colors={['#FF3B30', '#FF6B6B']}
                style={styles.buttonGradient}
              >
                <Text style={styles.buttonText}>Simulate Sell</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </ScrollView>

        {/* Close Button */}
        <TouchableOpacity 
          style={styles.closeButton} 
          onPress={() => navigation.goBack()}
        >
          <LinearGradient
            colors={['#8E8E93', '#6D6D70']}
            style={styles.buttonGradient}
          >
            <Icon name="x" size={20} color="#fff" />
            <Text style={styles.buttonText}>Close AR</Text>
          </LinearGradient>
        </TouchableOpacity>
      </Animated.View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  arBackground: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#1a1a2e',
  },
  arOverlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  arTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
  },
  arSubtitle: {
    fontSize: 18,
    color: '#8B5CF6',
    opacity: 0.8,
  },
  contentOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 100,
  },
  portfolioCard: {
    backgroundColor: 'rgba(139, 92, 246, 0.2)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(139, 92, 246, 0.3)',
  },
  portfolioTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  portfolioValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  portfolioSubtext: {
    fontSize: 14,
    color: '#8B5CF6',
  },
  simulationCard: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  simulationTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  simulationValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#10B981',
    marginBottom: 8,
  },
  simulationGrowth: {
    fontSize: 16,
    color: '#10B981',
    marginBottom: 4,
  },
  simulationRisk: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 12,
  },
  recommendationsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(16, 185, 129, 0.3)',
  },
  recommendationsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  recommendationItem: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 4,
    opacity: 0.9,
  },
  holdingsCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  holdingsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  holdingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  holdingSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    flex: 1,
  },
  holdingShares: {
    fontSize: 14,
    color: '#8E8E93',
    marginRight: 12,
  },
  holdingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10B981',
  },
  actionButtons: {
    gap: 12,
    marginBottom: 16,
  },
  simulateButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  tradeButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
  closeButton: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
});


