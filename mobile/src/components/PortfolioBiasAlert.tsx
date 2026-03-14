/**
 * PortfolioBiasAlert
 * ==================
 * Shows a compact bias detection alert on the portfolio screen.
 * Taps through to the full Investor Profile for details.
 */

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Pressable, Animated } from 'react-native';
import { Feather } from '@expo/vector-icons';
import BiasDetectionService, { BiasAnalysis } from '../features/wealth/services/BiasDetectionService';

interface PortfolioBiasAlertProps {
  onPress?: () => void;
}

const D = {
  amber:         '#F59E0B',
  amberFaint:    '#FEF3C7',
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  white:         '#FFFFFF',
};

export default function PortfolioBiasAlert({ onPress }: PortfolioBiasAlertProps) {
  const [biasAnalysis, setBiasAnalysis] = useState<BiasAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadBiasAnalysis();
  }, []);

  useEffect(() => {
    if (biasAnalysis && biasAnalysis.activeBiasCount > 0) {
      // Pulse animation for active biases
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [biasAnalysis]);

  const loadBiasAnalysis = async () => {
    try {
      const analysis = await BiasDetectionService.analyzePortfolio();
      setBiasAnalysis(analysis);
    } catch (error) {
      console.warn('Failed to load bias analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !biasAnalysis) {
    return null;
  }

  const activeBiases = [
    biasAnalysis.concentrationBias.isActive && 'Concentration',
    biasAnalysis.familiarityBias.isActive && 'Familiarity',
    biasAnalysis.recencyBias.isActive && 'Recency',
    biasAnalysis.lossAversion.isActive && 'Loss Aversion',
  ].filter(Boolean);

  // No biases - show healthy status
  if (activeBiases.length === 0) {
    return (
      <Pressable style={styles.cardHealthy} onPress={onPress}>
        <View style={styles.iconWrapHealthy}>
          <Feather name="check-circle" size={18} color={D.green} />
        </View>
        <View style={styles.content}>
          <Text style={styles.titleHealthy}>Portfolio Health: Good</Text>
          <Text style={styles.subtitle}>No behavioral biases detected</Text>
        </View>
        <Feather name="chevron-right" size={18} color={D.green} />
      </Pressable>
    );
  }

  // Has biases - show alert
  return (
    <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
      <Pressable style={styles.cardAlert} onPress={onPress}>
        <View style={styles.iconWrapAlert}>
          <Feather name="alert-triangle" size={18} color={D.amber} />
        </View>
        <View style={styles.content}>
          <View style={styles.titleRow}>
            <Text style={styles.titleAlert}>
              {activeBiases.length} Bias{activeBiases.length > 1 ? 'es' : ''} Detected
            </Text>
            <View style={styles.activeBadge}>
              <Text style={styles.activeBadgeText}>ACTION NEEDED</Text>
            </View>
          </View>
          <Text style={styles.biasesList}>
            {activeBiases.join(' · ')}
          </Text>
        </View>
        <Feather name="chevron-right" size={18} color={D.amber} />
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  cardHealthy: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.greenFaint,
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
  },
  cardAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.amberFaint,
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: D.amber + '40',
  },
  iconWrapHealthy: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: D.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  iconWrapAlert: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: D.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  titleHealthy: {
    fontSize: 14,
    fontWeight: '600',
    color: D.green,
  },
  titleAlert: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textPrimary,
  },
  activeBadge: {
    backgroundColor: D.amber,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  activeBadgeText: {
    fontSize: 8,
    fontWeight: '700',
    color: D.white,
  },
  subtitle: {
    fontSize: 12,
    color: D.textSecondary,
  },
  biasesList: {
    fontSize: 12,
    color: D.textSecondary,
  },
});
