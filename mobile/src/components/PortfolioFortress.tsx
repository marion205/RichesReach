/**
 * PortfolioFortress
 * =================
 * Visual representation of portfolio as a castle/fortress.
 * From the blueprint:
 * - Foundation: Emergency Fund + Core Index Funds
 * - Walls: Diversification (International, Bonds)
 * - Flags: Satellite positions
 * - Cracked walls indicate over-concentration
 */

import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Animated, Dimensions } from 'react-native';
import Svg, { 
  Rect, 
  Path, 
  Circle, 
  G, 
  Defs, 
  LinearGradient, 
  Stop,
  Polygon,
  Line,
} from 'react-native-svg';
import { Feather } from '@expo/vector-icons';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const FORTRESS_WIDTH = SCREEN_WIDTH - 64;
const FORTRESS_HEIGHT = 200;

interface FortressData {
  // Foundation (bottom)
  emergencyFundPercent: number; // % of 3-month target
  coreIndexPercent: number; // % in VTI/VOO type funds
  
  // Walls (sides)
  internationalPercent: number;
  bondsPercent: number;
  diversificationScore: number; // 0-100
  
  // Flags (top) - satellite positions
  satellitePositions: Array<{
    symbol: string;
    percent: number;
  }>;
  
  // Health indicators
  concentrationRisk: 'low' | 'medium' | 'high';
  overallHealth: number; // 0-100
}

interface PortfolioFortressProps {
  data: FortressData;
  onPress?: () => void;
  compact?: boolean;
}

const D = {
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  indigo:        '#6366F1',
  amber:         '#F59E0B',
  red:           '#EF4444',
  navy:          '#0B1426',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  stone:         '#78716C',
  stoneLight:    '#A8A29E',
  stoneDark:     '#57534E',
};

const DEMO_FORTRESS: FortressData = {
  emergencyFundPercent: 65, // 65% of target
  coreIndexPercent: 55, // 55% in index funds
  internationalPercent: 15,
  bondsPercent: 10,
  diversificationScore: 72,
  satellitePositions: [
    { symbol: 'AAPL', percent: 12 },
    { symbol: 'MSFT', percent: 8 },
    { symbol: 'GOOGL', percent: 5 },
  ],
  concentrationRisk: 'medium',
  overallHealth: 75,
};

export default function PortfolioFortress({
  data = DEMO_FORTRESS,
  onPress,
  compact = false,
}: PortfolioFortressProps) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();

    // Pulse if concentration risk is high
    if (data.concentrationRisk === 'high') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.02,
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
  }, [data.concentrationRisk]);

  const getHealthColor = (score: number) => {
    if (score >= 80) return D.green;
    if (score >= 60) return D.amber;
    return D.red;
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return D.green;
      case 'medium': return D.amber;
      case 'high': return D.red;
      default: return D.textMuted;
    }
  };

  const healthColor = getHealthColor(data.overallHealth);
  const riskColor = getRiskColor(data.concentrationRisk);
  const showCracks = data.concentrationRisk === 'high';

  if (compact) {
    return (
      <Pressable style={styles.compactCard} onPress={onPress}>
        <View style={styles.compactIconWrap}>
          <Feather name="shield" size={20} color={healthColor} />
        </View>
        <View style={styles.compactContent}>
          <Text style={styles.compactTitle}>Portfolio Fortress</Text>
          <View style={styles.compactStats}>
            <Text style={[styles.compactHealth, { color: healthColor }]}>
              {data.overallHealth}% Strong
            </Text>
            {data.concentrationRisk !== 'low' && (
              <View style={[styles.riskBadge, { backgroundColor: riskColor + '20' }]}>
                <Text style={[styles.riskBadgeText, { color: riskColor }]}>
                  {data.concentrationRisk === 'high' ? 'Reinforce Needed' : 'Minor Cracks'}
                </Text>
              </View>
            )}
          </View>
        </View>
        <Feather name="chevron-right" size={18} color={D.textMuted} />
      </Pressable>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ scale: pulseAnim }],
        },
      ]}
    >
      <Pressable onPress={onPress}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Portfolio Fortress</Text>
          <View style={[styles.healthBadge, { backgroundColor: healthColor + '20' }]}>
            <Feather name="shield" size={14} color={healthColor} />
            <Text style={[styles.healthText, { color: healthColor }]}>
              {data.overallHealth}% Strong
            </Text>
          </View>
        </View>

        {/* Castle Visualization */}
        <View style={styles.fortressWrap}>
          <Svg 
            width={FORTRESS_WIDTH} 
            height={FORTRESS_HEIGHT}
            viewBox={`0 0 ${FORTRESS_WIDTH} ${FORTRESS_HEIGHT}`}
          >
            <Defs>
              <LinearGradient id="wallGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <Stop offset="0%" stopColor={D.stoneLight} />
                <Stop offset="100%" stopColor={D.stoneDark} />
              </LinearGradient>
              <LinearGradient id="foundationGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <Stop offset="0%" stopColor={D.stoneDark} />
                <Stop offset="100%" stopColor="#3F3F3F" />
              </LinearGradient>
            </Defs>

            {/* Foundation */}
            <G>
              <Rect
                x={40}
                y={FORTRESS_HEIGHT - 40}
                width={FORTRESS_WIDTH - 80}
                height={35}
                fill="url(#foundationGradient)"
                rx={4}
              />
              {/* Foundation fill based on emergency fund % */}
              <Rect
                x={42}
                y={FORTRESS_HEIGHT - 38}
                width={(FORTRESS_WIDTH - 84) * (data.emergencyFundPercent / 100)}
                height={31}
                fill={data.emergencyFundPercent >= 100 ? D.green : D.amber}
                opacity={0.6}
                rx={3}
              />
            </G>

            {/* Left Wall */}
            <G>
              <Rect
                x={40}
                y={60}
                width={40}
                height={FORTRESS_HEIGHT - 105}
                fill="url(#wallGradient)"
              />
              {/* Left wall strength based on international % */}
              <Rect
                x={42}
                y={60 + (FORTRESS_HEIGHT - 107) * (1 - data.internationalPercent / 30)}
                width={36}
                height={(FORTRESS_HEIGHT - 107) * (data.internationalPercent / 30)}
                fill={D.indigo}
                opacity={0.5}
              />
              {showCracks && (
                <G>
                  <Line x1={50} y1={80} x2={60} y2={100} stroke={D.red} strokeWidth={2} />
                  <Line x1={65} y1={120} x2={55} y2={140} stroke={D.red} strokeWidth={2} />
                </G>
              )}
            </G>

            {/* Right Wall */}
            <G>
              <Rect
                x={FORTRESS_WIDTH - 80}
                y={60}
                width={40}
                height={FORTRESS_HEIGHT - 105}
                fill="url(#wallGradient)"
              />
              {/* Right wall strength based on bonds % */}
              <Rect
                x={FORTRESS_WIDTH - 78}
                y={60 + (FORTRESS_HEIGHT - 107) * (1 - data.bondsPercent / 30)}
                width={36}
                height={(FORTRESS_HEIGHT - 107) * (data.bondsPercent / 30)}
                fill={D.green}
                opacity={0.5}
              />
              {showCracks && (
                <G>
                  <Line x1={FORTRESS_WIDTH - 70} y1={90} x2={FORTRESS_WIDTH - 60} y2={110} stroke={D.red} strokeWidth={2} />
                </G>
              )}
            </G>

            {/* Center Keep (Core Holdings) */}
            <G>
              <Rect
                x={(FORTRESS_WIDTH - 120) / 2}
                y={40}
                width={120}
                height={FORTRESS_HEIGHT - 85}
                fill="url(#wallGradient)"
                rx={4}
              />
              {/* Core index fund fill */}
              <Rect
                x={(FORTRESS_WIDTH - 116) / 2}
                y={40 + (FORTRESS_HEIGHT - 89) * (1 - data.coreIndexPercent / 80)}
                width={116}
                height={(FORTRESS_HEIGHT - 89) * (data.coreIndexPercent / 80)}
                fill={D.indigo}
                opacity={0.4}
                rx={3}
              />
            </G>

            {/* Tower Tops (Crenellations) */}
            <G>
              {[0, 1, 2, 3, 4].map((i) => (
                <Rect
                  key={`left-${i}`}
                  x={42 + i * 8}
                  y={50}
                  width={6}
                  height={12}
                  fill={D.stone}
                />
              ))}
              {[0, 1, 2, 3, 4].map((i) => (
                <Rect
                  key={`right-${i}`}
                  x={FORTRESS_WIDTH - 78 + i * 8}
                  y={50}
                  width={6}
                  height={12}
                  fill={D.stone}
                />
              ))}
            </G>

            {/* Flags (Satellite Positions) */}
            <G>
              {data.satellitePositions.slice(0, 3).map((pos, i) => {
                const x = (FORTRESS_WIDTH / 2) - 40 + i * 40;
                return (
                  <G key={pos.symbol}>
                    <Line x1={x} y1={10} x2={x} y2={35} stroke={D.textMuted} strokeWidth={2} />
                    <Polygon
                      points={`${x},10 ${x + 20},18 ${x},26`}
                      fill={i === 0 ? D.amber : i === 1 ? D.indigo : D.green}
                    />
                  </G>
                );
              })}
            </G>
          </Svg>

          {/* Flag Labels */}
          <View style={styles.flagLabels}>
            {data.satellitePositions.slice(0, 3).map((pos, i) => (
              <Text key={pos.symbol} style={styles.flagLabel}>
                {pos.symbol} {pos.percent}%
              </Text>
            ))}
          </View>
        </View>

        {/* Legend */}
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: D.stoneDark }]} />
            <Text style={styles.legendText}>Foundation: Emergency Fund ({data.emergencyFundPercent}%)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: D.indigo }]} />
            <Text style={styles.legendText}>Core: Index Funds ({data.coreIndexPercent}%)</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: D.stone }]} />
            <Text style={styles.legendText}>Walls: Intl {data.internationalPercent}% | Bonds {data.bondsPercent}%</Text>
          </View>
          {showCracks && (
            <View style={[styles.legendItem, styles.legendWarning]}>
              <Feather name="alert-triangle" size={12} color={D.red} />
              <Text style={[styles.legendText, { color: D.red }]}>
                Concentration risk detected - walls need reinforcement
              </Text>
            </View>
          )}
        </View>

        {/* CTA */}
        {showCracks && (
          <Pressable style={styles.ctaButton} onPress={onPress}>
            <Feather name="shield" size={16} color={D.white} />
            <Text style={styles.ctaText}>Reinforce Your Fortress</Text>
          </Pressable>
        )}
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: D.white,
    borderRadius: 20,
    padding: 20,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  healthBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
  },
  healthText: {
    fontSize: 13,
    fontWeight: '600',
  },
  fortressWrap: {
    alignItems: 'center',
    marginBottom: 16,
  },
  flagLabels: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
    marginTop: -8,
  },
  flagLabel: {
    fontSize: 10,
    color: D.textMuted,
    fontWeight: '500',
  },
  legend: {
    gap: 8,
    marginBottom: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 12,
    color: D.textSecondary,
  },
  legendWarning: {
    backgroundColor: D.red + '10',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginTop: 4,
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: D.indigo,
    paddingVertical: 14,
    borderRadius: 12,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '600',
    color: D.white,
  },
  
  // Compact
  compactCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.white,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  compactIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: D.greenFaint,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  compactContent: {
    flex: 1,
  },
  compactTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textPrimary,
    marginBottom: 4,
  },
  compactStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  compactHealth: {
    fontSize: 12,
    fontWeight: '600',
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  riskBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
});
