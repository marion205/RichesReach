import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Svg, { Line, Rect, Circle, Text as SvgText, Polygon } from 'react-native-svg';
import Icon from 'react-native-vector-icons/Feather';

const { width: screenWidth } = Dimensions.get('window');

interface RiskRewardDiagramProps {
  entryPrice: number;
  stopPrice: number;
  targetPrice: number;
  side?: 'LONG' | 'SHORT' | 'BUY' | 'SELL';
  showLabels?: boolean;
  height?: number;
  width?: number;
}

export const RiskRewardDiagram: React.FC<RiskRewardDiagramProps> = ({
  entryPrice,
  stopPrice,
  targetPrice,
  side = 'LONG',
  showLabels = true,
  height = 200,
  width = screenWidth - 40,
}) => {
  const isLong = side === 'LONG' || side === 'BUY';
  
  // Calculate price range
  const minPrice = Math.min(entryPrice, stopPrice, targetPrice);
  const maxPrice = Math.max(entryPrice, stopPrice, targetPrice);
  const priceRange = maxPrice - minPrice || 1; // Avoid division by zero
  
  // Add padding to range
  const paddedMin = minPrice - priceRange * 0.1;
  const paddedMax = maxPrice + priceRange * 0.1;
  const paddedRange = paddedMax - paddedMin;
  
  // Calculate Y positions (SVG coordinates: top is 0, bottom is height)
  const getY = (price: number) => {
    return height - ((price - paddedMin) / paddedRange) * height;
  };
  
  const entryY = getY(entryPrice);
  const stopY = getY(stopPrice);
  const targetY = getY(targetPrice);
  
  // Calculate risk and reward
  const risk = Math.abs(entryPrice - stopPrice);
  const reward = Math.abs(targetPrice - entryPrice);
  const riskRewardRatio = risk > 0 ? (reward / risk).toFixed(2) : '0.00';
  
  // Colors
  const entryColor = '#007AFF';
  const stopColor = '#EF4444';
  const targetColor = '#22C55E';
  const riskColor = '#FEE2E2';
  const rewardColor = '#DCFCE7';
  
  const centerX = width / 2;
  const lineStartX = width * 0.1;
  const lineEndX = width * 0.9;
  
  return (
    <View style={styles.container}>
      {showLabels && (
        <View style={styles.header}>
          <Text style={styles.title}>Risk/Reward Analysis</Text>
          <View style={styles.ratioBadge}>
            <Icon name="trending-up" size={14} color="#22C55E" />
            <Text style={styles.ratioText}>R:R {riskRewardRatio}:1</Text>
          </View>
        </View>
      )}
      
      <View style={[styles.chartContainer, { height, width }]}>
        <Svg width={width} height={height}>
          {/* Risk zone (red background) */}
          <Rect
            x={lineStartX}
            y={isLong ? entryY : stopY}
            width={lineEndX - lineStartX}
            height={Math.abs(entryY - stopY)}
            fill={riskColor}
            opacity={0.3}
          />
          
          {/* Reward zone (green background) */}
          <Rect
            x={lineStartX}
            y={isLong ? entryY : targetY}
            width={lineEndX - lineStartX}
            height={Math.abs(entryY - targetY)}
            fill={rewardColor}
            opacity={0.3}
          />
          
          {/* Price line */}
          <Line
            x1={lineStartX}
            y1={entryY}
            x2={lineEndX}
            y2={entryY}
            stroke="#E5E7EB"
            strokeWidth={1}
            strokeDasharray="4,4"
          />
          
          {/* Entry point */}
          <Circle
            cx={centerX}
            cy={entryY}
            r={8}
            fill={entryColor}
            stroke="#fff"
            strokeWidth={2}
          />
          <SvgText
            x={centerX}
            y={entryY - 12}
            fontSize="11"
            fill={entryColor}
            fontWeight="700"
            textAnchor="middle"
          >
            Entry
          </SvgText>
          <SvgText
            x={centerX}
            y={entryY + 20}
            fontSize="12"
            fill="#111827"
            fontWeight="600"
            textAnchor="middle"
          >
            ${entryPrice.toFixed(2)}
          </SvgText>
          
          {/* Stop loss point */}
          <Circle
            cx={centerX}
            cy={stopY}
            r={8}
            fill={stopColor}
            stroke="#fff"
            strokeWidth={2}
          />
          <SvgText
            x={centerX}
            y={stopY + (isLong ? 20 : -12)}
            fontSize="11"
            fill={stopColor}
            fontWeight="700"
            textAnchor="middle"
          >
            Stop
          </SvgText>
          <SvgText
            x={centerX}
            y={stopY + (isLong ? 32 : -24)}
            fontSize="12"
            fill="#111827"
            fontWeight="600"
            textAnchor="middle"
          >
            ${stopPrice.toFixed(2)}
          </SvgText>
          
          {/* Target point */}
          <Circle
            cx={centerX}
            cy={targetY}
            r={8}
            fill={targetColor}
            stroke="#fff"
            strokeWidth={2}
          />
          <SvgText
            x={centerX}
            y={targetY + (isLong ? -12 : 20)}
            fontSize="11"
            fill={targetColor}
            fontWeight="700"
            textAnchor="middle"
          >
            Target
          </SvgText>
          <SvgText
            x={centerX}
            y={targetY + (isLong ? -24 : 32)}
            fontSize="12"
            fill="#111827"
            fontWeight="600"
            textAnchor="middle"
          >
            ${targetPrice.toFixed(2)}
          </SvgText>
          
          {/* Risk arrow */}
          <Line
            x1={lineEndX + 10}
            y1={entryY}
            x2={lineEndX + 10}
            y2={stopY}
            stroke={stopColor}
            strokeWidth={2}
          />
          <Polygon
            points={`${lineEndX + 10},${stopY} ${lineEndX + 5},${stopY - 5} ${lineEndX + 15},${stopY - 5}`}
            fill={stopColor}
          />
          <SvgText
            x={lineEndX + 20}
            y={(entryY + stopY) / 2 + 4}
            fontSize="10"
            fill={stopColor}
            fontWeight="600"
          >
            Risk: ${risk.toFixed(2)}
          </SvgText>
          
          {/* Reward arrow */}
          <Line
            x1={lineEndX + 10}
            y1={entryY}
            x2={lineEndX + 10}
            y2={targetY}
            stroke={targetColor}
            strokeWidth={2}
          />
          <Polygon
            points={`${lineEndX + 10},${targetY} ${lineEndX + 5},${targetY + (isLong ? -5 : 5)} ${lineEndX + 15},${targetY + (isLong ? -5 : 5)}`}
            fill={targetColor}
          />
          <SvgText
            x={lineEndX + 20}
            y={(entryY + targetY) / 2 + 4}
            fontSize="10"
            fill={targetColor}
            fontWeight="600"
          >
            Reward: ${reward.toFixed(2)}
          </SvgText>
        </Svg>
      </View>
      
      {showLabels && (
        <View style={styles.stats}>
          <View style={styles.statItem}>
            <View style={[styles.statDot, { backgroundColor: stopColor }]} />
            <Text style={styles.statLabel}>Risk</Text>
            <Text style={[styles.statValue, { color: stopColor }]}>${risk.toFixed(2)}</Text>
          </View>
          <View style={styles.statItem}>
            <View style={[styles.statDot, { backgroundColor: targetColor }]} />
            <Text style={styles.statLabel}>Reward</Text>
            <Text style={[styles.statValue, { color: targetColor }]}>${reward.toFixed(2)}</Text>
          </View>
          <View style={styles.statItem}>
            <Icon name="trending-up" size={16} color="#007AFF" />
            <Text style={styles.statLabel}>R:R</Text>
            <Text style={[styles.statValue, { color: '#007AFF' }]}>{riskRewardRatio}:1</Text>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  ratioBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  ratioText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  chartContainer: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 12,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  statValue: {
    fontSize: 14,
    fontWeight: '700',
  },
});

