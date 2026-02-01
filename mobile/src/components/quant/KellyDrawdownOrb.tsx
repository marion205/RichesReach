// components/quant/KellyDrawdownOrb.tsx
/**
 * Kelly Criterion + Drawdown Visual Orb
 * 
 * Visualizes optimal position sizing (Kelly) and expected drawdown risk
 * in an intuitive, Apple-style orb interface.
 * 
 * Based on Ernest P. Chan's risk management principles.
 */

import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Text as SvgText } from 'react-native-svg';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');
const ORB_SIZE = Math.min(width * 0.4, 160);

interface KellyDrawdownOrbProps {
  kellyFraction: number; // 0-1, optimal Kelly fraction
  recommendedFraction: number; // 0-1, conservative recommendation
  maxDrawdownRisk: number; // 0-1, expected max drawdown
  winRate: number; // 0-1, historical win rate
  avgWin: number; // Average win percentage
  avgLoss: number; // Average loss percentage
  symbol?: string;
  showDetails?: boolean;
}

export default function KellyDrawdownOrb({
  kellyFraction,
  recommendedFraction,
  maxDrawdownRisk,
  winRate,
  avgWin,
  avgLoss,
  symbol,
  showDetails = true,
}: KellyDrawdownOrbProps) {
  
  // Color mapping based on risk level
  const getRiskColor = (risk: number): string => {
    if (risk < 0.02) return '#10B981'; // Green - Low risk
    if (risk < 0.05) return '#3B82F6'; // Blue - Medium risk
    if (risk < 0.10) return '#F59E0B'; // Orange - Elevated risk
    return '#EF4444'; // Red - High risk
  };
  
  const riskColor = getRiskColor(maxDrawdownRisk);
  const kellyColor = recommendedFraction > 0.1 ? '#EF4444' : 
                     recommendedFraction > 0.05 ? '#F59E0B' : 
                     recommendedFraction > 0.02 ? '#3B82F6' : '#10B981';
  
  // Orb fill percentage (based on recommended fraction, capped at 100%)
  const orbFill = Math.min(recommendedFraction * 5, 1.0); // Scale for visibility
  
  // Drawdown ring percentage
  const drawdownRing = Math.min(maxDrawdownRisk * 10, 1.0); // Scale for visibility
  
  return (
    <View style={styles.container}>
      {/* Main Orb */}
      <View style={styles.orbContainer}>
        {/* Outer ring (drawdown risk indicator) */}
        <View style={[styles.outerRing, { borderColor: riskColor }]}>
          <View style={[styles.drawdownRing, { 
            width: `${drawdownRing * 100}%`, 
            backgroundColor: riskColor,
            opacity: 0.2 
          }]} />
        </View>
        
        {/* Inner orb (Kelly position size) */}
        <LinearGradient
          colors={[
            kellyColor,
            kellyColor + '80', // 50% opacity
            kellyColor + '40', // 25% opacity
          ]}
          style={[
            styles.innerOrb,
            {
              width: `${orbFill * 100}%`,
              height: `${orbFill * 100}%`,
            }
          ]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.orbContent}>
            <Text style={styles.orbValue}>
              {(recommendedFraction * 100).toFixed(1)}%
            </Text>
            <Text style={styles.orbLabel}>Position</Text>
          </View>
        </LinearGradient>
        
        {/* Center indicator */}
        <View style={styles.centerIndicator}>
          <Icon name="target" size={16} color={riskColor} />
        </View>
      </View>
      
      {/* Details Panel */}
      {showDetails && (
        <View style={styles.detailsPanel}>
          <View style={styles.detailRow}>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>KELLY OPTIMAL MAX</Text>
              <Text style={[styles.detailValue, { color: kellyColor }]}>
                {(kellyFraction * 100).toFixed(1)}%
              </Text>
            </View>
            
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>DRAWDOWN</Text>
              <Text style={[styles.detailValue, { color: riskColor }]}>
                {(maxDrawdownRisk * 100).toFixed(1)}%
              </Text>
            </View>
          </View>
        </View>
      )}
      
      {/* Risk Level Badge */}
      <View style={[styles.riskBadge, { backgroundColor: riskColor + '20' }]}>
        <View style={[styles.riskDot, { backgroundColor: riskColor }]} />
        <Text style={[styles.riskText, { color: riskColor }]}>
          {maxDrawdownRisk < 0.02 ? 'Low Risk' :
           maxDrawdownRisk < 0.05 ? 'Medium Risk' :
           maxDrawdownRisk < 0.10 ? 'Elevated Risk' : 'High Risk'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    padding: 20,
  },
  orbContainer: {
    width: ORB_SIZE,
    height: ORB_SIZE,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  outerRing: {
    position: 'absolute',
    width: ORB_SIZE,
    height: ORB_SIZE,
    borderRadius: ORB_SIZE / 2,
    borderWidth: 3,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawdownRing: {
    position: 'absolute',
    height: '100%',
    borderRadius: ORB_SIZE / 2,
    top: 0,
    left: 0,
  },
  innerOrb: {
    width: ORB_SIZE * 0.6,
    height: ORB_SIZE * 0.6,
    borderRadius: (ORB_SIZE * 0.6) / 2,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  orbContent: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  orbValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.5,
  },
  orbLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.9,
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  centerIndicator: {
    position: 'absolute',
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  detailsPanel: {
    marginTop: 24,
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  detailItem: {
    flex: 1,
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detailValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    letterSpacing: -0.3,
  },
  symbolBadge: {
    marginTop: 8,
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    alignSelf: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  symbolText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111827',
    letterSpacing: 0.5,
  },
  riskBadge: {
    marginTop: 16,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  riskDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  riskText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});

