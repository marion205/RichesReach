import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import LottieView from 'lottie-react-native';
import Svg, { Circle, Line, Path } from 'react-native-svg';

interface GreeksData {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

interface RepairPlan {
  positionId: string;
  ticker: string;
  originalStrategy: string;
  currentDelta: number;
  deltaDriftPct: number;
  currentMaxLoss: number;
  repairType: string;
  repairStrikes: string;
  repairCredit: number;
  newMaxLoss: number;
  newBreakEven: number;
  confidenceBoost: number;
  headline: string;
  reason: string;
  actionDescription: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

interface ShieldStatusProps {
  status: 'healthy' | 'warning' | 'critical';
  priority?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidenceBoost?: number;
}

/**
 * Shield Status Bar Component
 * Shows real-time health status with color-coded indicator
 */
export const ShieldStatusBar: React.FC<ShieldStatusProps> = ({
  status,
  priority,
  confidenceBoost = 0,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return '#10B981'; // Green
      case 'warning':
        return '#F59E0B'; // Amber
      case 'critical':
        return '#EF4444'; // Red
      default:
        return '#6B7280'; // Gray
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'healthy':
        return '✓ Healthy';
      case 'warning':
        return '⚠ Caution';
      case 'critical':
        return '🚨 Alert';
      default:
        return 'Unknown';
    }
  };

  const priorityLabel = priority ? `${priority} Priority` : '';
  const boostLabel = confidenceBoost > 0 ? `+${(confidenceBoost * 100).toFixed(0)}% Confidence` : '';

  return (
    <View style={styles.statusBarContainer}>
      <View
        style={[
          styles.statusBar,
          { backgroundColor: getStatusColor() },
        ]}
      >
        <Text style={styles.statusLabel}>{getStatusLabel()}</Text>
        {priorityLabel && (
          <Text style={styles.priorityLabel}>{priorityLabel}</Text>
        )}
        {boostLabel && (
          <Text style={styles.boostLabel}>{boostLabel}</Text>
        )}
      </View>
    </View>
  );
};

/**
 * Greeks Radar Chart Component
 * Visualizes option Greeks as a radar/spider chart
 */
export const GreeksRadarChart: React.FC<{ greeks: GreeksData; title?: string }> = ({
  greeks,
  title = 'Greeks Profile',
}) => {
  const size = 240;
  const center = size / 2;
  const radius = 80;

  // Normalize Greeks to 0-1 scale for visualization
  const normalizedGreeks = {
    delta: Math.min(Math.abs(greeks.delta), 1),
    gamma: Math.min(Math.abs(greeks.gamma) * 10, 1), // Scale up gamma
    theta: Math.min(Math.abs(greeks.theta) / 5, 1),
    vega: Math.min(Math.abs(greeks.vega) / 2, 1),
  };

  const angles = [0, 72, 144, 216, 288]; // 5 points: delta, gamma, theta, vega, rho
  const labels = ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho'];
  const values = [
    normalizedGreeks.delta,
    normalizedGreeks.gamma,
    normalizedGreeks.theta,
    normalizedGreeks.vega,
    Math.min(Math.abs(greeks.rho) / 5, 1),
  ];

  const polarToCartesian = (angle: number, distance: number) => {
    const radians = (angle * Math.PI) / 180;
    return {
      x: center + distance * Math.cos(radians - Math.PI / 2),
      y: center + distance * Math.sin(radians - Math.PI / 2),
    };
  };

  // Build path for radar area
  let pathData = '';
  values.forEach((value, i) => {
    const point = polarToCartesian(angles[i], radius * value);
    pathData += `${i === 0 ? 'M' : 'L'} ${point.x} ${point.y} `;
  });
  pathData += 'Z'; // Close the path

  return (
    <View style={styles.radarContainer}>
      <Text style={styles.radarTitle}>{title}</Text>
      <View style={{ width: size, height: size, backgroundColor: '#F3F4F6', borderRadius: 12 }}>
        <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Grid circles */}
          {[0.25, 0.5, 0.75, 1].map((scale, i) => (
            <Circle
              key={`grid-${i}`}
              cx={center}
              cy={center}
              r={radius * scale}
              fill="none"
              stroke="#D1D5DB"
              strokeWidth="1"
            />
          ))}

          {/* Axis lines */}
          {angles.map((angle, i) => {
            const point = polarToCartesian(angle, radius);
            return (
              <Line
                key={`axis-${i}`}
                x1={center}
                y1={center}
                x2={point.x}
                y2={point.y}
                stroke="#D1D5DB"
                strokeWidth="1"
              />
            );
          })}

          {/* Data polygon */}
          <Path d={pathData} fill="#3B82F6" fillOpacity="0.2" stroke="#3B82F6" strokeWidth="2" />

          {/* Data points */}
          {values.map((value, i) => {
            const point = polarToCartesian(angles[i], radius * value);
            return (
              <Circle
                key={`point-${i}`}
                cx={point.x}
                cy={point.y}
                r="4"
                fill="#3B82F6"
                stroke="white"
                strokeWidth="2"
              />
            );
          })}
        </Svg>
      </View>

      {/* Legend */}
      <View style={styles.radarLegend}>
        {labels.map((label, i) => (
          <View key={label} style={styles.legendItem}>
            <View
              style={[
                styles.legendDot,
                {
                  backgroundColor:
                    values[i] > 0.7
                      ? '#3B82F6'
                      : values[i] > 0.4
                        ? '#60A5FA'
                        : '#BFDBFE',
                },
              ]}
            />
            <Text style={styles.legendLabel}>
              {label}: {(values[i] * 100).toFixed(0)}%
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
};

/**
 * Main Repair Shield Component
 * Shows position health and repair button
 */
export const RepairShield: React.FC<{
  repairPlan: RepairPlan;
  onAccept: () => void;
  onReject: () => void;
  loading?: boolean;
}> = ({ repairPlan, onAccept, onReject, loading = false }) => {
  const scaleAnim = React.useRef(new Animated.Value(0)).current;
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Entrance animation
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
    }).start();

    // Pulse animation
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
      ]),
    ).start();
  }, []);

  const getBackgroundColor = () => {
    switch (repairPlan.priority) {
      case 'CRITICAL':
        return ['#FEE2E2', '#FECACA'];
      case 'HIGH':
        return ['#FEF3C7', '#FDE68A'];
      case 'MEDIUM':
        return ['#E0E7FF', '#C7D2FE'];
      default:
        return ['#D1FAE5', '#A7F3D0'];
    }
  };

  const getButtonColor = () => {
    switch (repairPlan.priority) {
      case 'CRITICAL':
        return '#DC2626';
      case 'HIGH':
        return '#F59E0B';
      default:
        return '#3B82F6';
    }
  };

  const getPriorityEmoji = () => {
    switch (repairPlan.priority) {
      case 'CRITICAL':
        return '🚨';
      case 'HIGH':
        return '⚠️';
      case 'MEDIUM':
        return '💡';
      default:
        return '✓';
    }
  };

  return (
    <Animated.View
      style={[
        styles.repairShieldContainer,
        {
          transform: [
            {
              scale: scaleAnim,
            },
          ],
        },
      ]}
    >
      <LinearGradient colors={getBackgroundColor()} style={styles.repairCard}>
        {/* Header */}
        <View style={styles.repairHeader}>
          <Animated.Text
            style={[
              styles.repairHeadline,
              {
                transform: [{ scale: pulseAnim }],
              },
            ]}
          >
            {getPriorityEmoji()} {repairPlan.headline}
          </Animated.Text>
        </View>

        {/* Reason */}
        <Text style={styles.repairReason}>{repairPlan.reason}</Text>

        {/* Action Description */}
        <View style={styles.actionBox}>
          <Text style={styles.actionLabel}>Recommended Action:</Text>
          <Text style={styles.actionText}>{repairPlan.actionDescription}</Text>
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Current Max Loss</Text>
            <Text style={styles.statValue}>${repairPlan.currentMaxLoss.toFixed(0)}</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>After Repair</Text>
            <Text style={styles.statValueGreen}>${repairPlan.newMaxLoss.toFixed(0)}</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Credit Collected</Text>
            <Text style={styles.statValueGreen}>${repairPlan.repairCredit.toFixed(0)}</Text>
          </View>
        </View>

        {/* Buttons */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.acceptButton, { backgroundColor: getButtonColor() }]}
            onPress={onAccept}
            disabled={loading}
          >
            {loading ? (
              <Text style={styles.buttonText}>Processing...</Text>
            ) : (
              <Text style={styles.buttonText}>✓ ACCEPT & DEPLOY</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.rejectButton]}
            onPress={onReject}
            disabled={loading}
          >
            <Text style={styles.rejectButtonText}>Review Later</Text>
          </TouchableOpacity>
        </View>

        {/* Confidence Boost Badge */}
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>
            +{(repairPlan.confidenceBoost * 100).toFixed(0)}% Edge Boost
          </Text>
        </View>
      </LinearGradient>
    </Animated.View>
  );
};

/**
 * Enhanced Position Card with Repair Indicator
 */
export const PositionCardWithRepair: React.FC<{
  position: any;
  repairPlan?: RepairPlan;
  onShowRepair?: () => void;
}> = ({ position, repairPlan, onShowRepair }) => {
  const hasRepair = repairPlan !== undefined;

  return (
    <View style={styles.positionCard}>
      {/* Header */}
      <View style={styles.positionHeader}>
        <View>
          <Text style={styles.positionTicker}>{position.ticker}</Text>
          <Text style={styles.positionStrategy}>{position.strategyType}</Text>
        </View>
        <View style={styles.positionPrice}>
          <Text
            style={[
              styles.positionPnL,
              {
                color: position.unrealizedPnl >= 0 ? '#10B981' : '#EF4444',
              },
            ]}
          >
            {position.unrealizedPnl >= 0 ? '+' : ''}${position.unrealizedPnl.toFixed(0)}
          </Text>
          <Text style={styles.positionDTE}>{position.daysToExpiration}dte</Text>
        </View>
      </View>

      {/* Greeks Compact View */}
      <View style={styles.greeksCompact}>
        <View style={styles.greekItem}>
          <Text style={styles.greekLabel}>Δ</Text>
          <Text
            style={[
              styles.greekValue,
              {
                color: Math.abs(position.greeks.delta) > 0.35 ? '#EF4444' : '#10B981',
              },
            ]}
          >
            {position.greeks.delta.toFixed(2)}
          </Text>
        </View>
        <View style={styles.greekItem}>
          <Text style={styles.greekLabel}>Θ</Text>
          <Text
            style={[
              styles.greekValue,
              {
                color: position.greeks.theta > 0 ? '#10B981' : '#EF4444',
              },
            ]}
          >
            {position.greeks.theta.toFixed(2)}
          </Text>
        </View>
        <View style={styles.greekItem}>
          <Text style={styles.greekLabel}>Γ</Text>
          <Text style={styles.greekValue}>{position.greeks.gamma.toFixed(3)}</Text>
        </View>
        <View style={styles.greekItem}>
          <Text style={styles.greekLabel}>Ν</Text>
          <Text style={styles.greekValue}>{position.greeks.vega.toFixed(2)}</Text>
        </View>
      </View>

      {/* Risk Metrics */}
      <View style={styles.riskMetrics}>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Max Loss</Text>
          <Text style={styles.metricValue}>${position.maxLoss.toFixed(0)}</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Probability of Profit</Text>
          <Text style={styles.metricValue}>
            {(position.probabilityOfProfit * 100).toFixed(0)}%
          </Text>
        </View>
      </View>

      {/* Repair Alert Badge */}
      {hasRepair && (
        <TouchableOpacity
          style={styles.repairBadge}
          onPress={onShowRepair}
        >
          <Text style={styles.repairBadgeEmoji}>🛡️</Text>
          <View style={styles.repairBadgeText}>
            <Text style={styles.repairBadgeTitle}>Repair Available</Text>
            <Text style={styles.repairBadgeSubtitle}>
              Reduce loss by ${repairPlan.repairCredit.toFixed(0)}
            </Text>
          </View>
          <Text style={styles.repairBadgeArrow}>›</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  // Status Bar Styles
  statusBarContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  priorityLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    marginLeft: 8,
  },
  boostLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    marginLeft: 8,
    fontWeight: '600',
  },

  // Radar Chart Styles
  radarContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  radarTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    color: '#1F2937',
  },
  radarLegend: {
    marginTop: 12,
    flexWrap: 'wrap',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 8,
    marginVertical: 4,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  legendLabel: {
    fontSize: 12,
    color: '#6B7280',
  },

  // Repair Shield Styles
  repairShieldContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  repairCard: {
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  repairHeader: {
    marginBottom: 12,
  },
  repairHeadline: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  repairReason: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 12,
  },
  actionBox: {
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 4,
  },
  actionText: {
    fontSize: 13,
    color: '#1F2937',
    fontWeight: '500',
  },

  // Stats Container
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: 8,
    padding: 8,
    marginBottom: 12,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  statValueGreen: {
    fontSize: 14,
    fontWeight: '600',
    color: '#10B981',
  },
  divider: {
    width: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    marginHorizontal: 4,
  },

  // Buttons
  buttonContainer: {
    marginBottom: 12,
  },
  button: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  acceptButton: {
    backgroundColor: '#3B82F6',
  },
  rejectButton: {
    backgroundColor: '#F3F4F6',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
  },
  rejectButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },

  // Confidence Badge
  confidenceBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    alignSelf: 'center',
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#047857',
  },

  // Position Card Styles
  positionCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  positionTicker: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  positionStrategy: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  positionPrice: {
    alignItems: 'flex-end',
  },
  positionPnL: {
    fontSize: 16,
    fontWeight: '700',
  },
  positionDTE: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 2,
  },

  // Greeks Compact
  greeksCompact: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    paddingVertical: 8,
    marginBottom: 12,
  },
  greekItem: {
    alignItems: 'center',
  },
  greekLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 2,
  },
  greekValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
  },

  // Risk Metrics
  riskMetrics: {
    marginBottom: 12,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  metricLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },

  // Repair Badge
  repairBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#DC2626',
  },
  repairBadgeEmoji: {
    fontSize: 20,
    marginRight: 8,
  },
  repairBadgeText: {
    flex: 1,
  },
  repairBadgeTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#DC2626',
  },
  repairBadgeSubtitle: {
    fontSize: 12,
    color: '#B91C1C',
    marginTop: 2,
  },
  repairBadgeArrow: {
    fontSize: 18,
    color: '#DC2626',
    marginLeft: 8,
  },
});
