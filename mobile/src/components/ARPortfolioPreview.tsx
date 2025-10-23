import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  Modal,
  Alert,
  Platform,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';

const { width, height } = Dimensions.get('window');

interface ARPortfolioPreviewProps {
  portfolio: any;
  onClose: () => void;
  onTrade: (action: string) => void;
}

export default function ARPortfolioPreview({ portfolio, onClose, onTrade }: ARPortfolioPreviewProps) {
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

  const requestCameraPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    setHasPermission(status === 'granted');
    return status === 'granted';
  };

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
    Alert.alert(
      'Trade Simulation',
      `Simulating ${action} trade in AR environment...`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', onPress: () => onTrade(action) },
      ]
    );
  };

  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Modal visible={true} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
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
            styles.portfolioOverlay,
            {
              opacity: fadeAnim,
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          <ScrollView style={styles.portfolioContent} showsVerticalScrollIndicator={false}>
            <View style={styles.portfolioHeader}>
              <Text style={styles.portfolioTitle}>Your Portfolio</Text>
              <Text style={styles.portfolioValue}>
                ${portfolio?.totalValue?.toLocaleString() || '0'}
              </Text>
            </View>

            {portfolio?.allocation?.map((item: any, index: number) => (
              <View key={index} style={styles.allocationItem}>
                <View style={styles.allocationHeader}>
                  <View style={[styles.allocationColor, { backgroundColor: item.color }]} />
                  <Text style={styles.allocationName}>{item.name}</Text>
                  <Text style={styles.allocationPercentage}>{item.percentage}%</Text>
                </View>
                <View style={styles.allocationBar}>
                  <View
                    style={[
                      styles.allocationFill,
                      { width: `${item.percentage}%`, backgroundColor: item.color },
                    ]}
                  />
                </View>
                <Text style={styles.allocationValue}>
                  ${item.value?.toLocaleString() || '0'}
                </Text>
              </View>
            ))}

            {/* Simulation Results */}
            {simulationData && (
              <View style={styles.simulationResults}>
                <Text style={styles.simulationTitle}>AR Simulation Results</Text>
                <View style={styles.simulationMetrics}>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Projected Value</Text>
                    <Text style={styles.metricValue}>
                      ${simulationData.projectedValue.toLocaleString()}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Growth Rate</Text>
                    <Text style={styles.metricValue}>
                      +{simulationData.growthRate}%
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Risk Score</Text>
                    <Text style={styles.metricValue}>
                      {simulationData.riskScore}/10
                    </Text>
                  </View>
                </View>
                
                <View style={styles.recommendationsContainer}>
                  <Text style={styles.recommendationsTitle}>AI Recommendations</Text>
                  {simulationData.recommendations.map((rec: string, index: number) => (
                    <View key={index} style={styles.recommendationItem}>
                      <Text style={styles.recommendationText}>• {rec}</Text>
                    </View>
                  ))}
                </View>
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
                  style={styles.simulateButtonGradient}
                >
                  <Text style={styles.simulateButtonText}>
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
                  style={styles.tradeButtonGradient}
                >
                  <Text style={styles.tradeButtonText}>Simulate Buy</Text>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.tradeButton}
                onPress={() => handleTrade('sell')}
              >
                <LinearGradient
                  colors={['#FF3B30', '#FF6B6B']}
                  style={styles.tradeButtonGradient}
                >
                  <Text style={styles.tradeButtonText}>Simulate Sell</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </Animated.View>

        {/* Close Button */}
        <TouchableOpacity style={styles.closeButton} onPress={onClose}>
          <LinearGradient
            colors={['#8E8E93', '#6D6D70']}
            style={styles.closeButtonGradient}
          >
            <Text style={styles.closeButtonText}>Close AR</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  arBackground: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#1a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  arOverlay: {
    alignItems: 'center',
    padding: 20,
  },
  arTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#667eea',
    textAlign: 'center',
    marginBottom: 8,
  },
  arSubtitle: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    opacity: 0.8,
  },
  portfolioOverlay: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    bottom: 100,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
  },
  portfolioContent: {
    flex: 1,
    padding: 20,
  },
  portfolioHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  portfolioTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  portfolioValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#667eea',
  },
  allocationItem: {
    marginBottom: 16,
  },
  allocationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  allocationColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  allocationName: {
    fontSize: 16,
    color: '#1a1a1a',
    flex: 1,
  },
  allocationPercentage: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  allocationBar: {
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  allocationFill: {
    height: '100%',
    borderRadius: 4,
  },
  allocationValue: {
    fontSize: 14,
    color: '#666',
  },
  simulationResults: {
    marginTop: 20,
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
  },
  simulationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  simulationMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  recommendationsContainer: {
    marginTop: 12,
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  recommendationItem: {
    marginBottom: 4,
  },
  recommendationText: {
    fontSize: 14,
    color: '#666',
  },
  actionButtons: {
    marginTop: 20,
    gap: 12,
  },
  simulateButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  simulateButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  simulateButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  tradeButton: {
    borderRadius: 20,
    overflow: 'hidden',
  },
  tradeButtonGradient: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  tradeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  closeButton: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    borderRadius: 20,
    overflow: 'hidden',
  },
  closeButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});