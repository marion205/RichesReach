import React, { FC, useMemo } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Svg, { Line, Circle, Text as SvgText, Rect } from 'react-native-svg';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type RiskRewardDiagramProps = {
  entryPrice: number;
  stopPrice: number;
  targetPrice: number;
  riskAmount: number;
  rewardAmount: number;
};

export const RiskRewardDiagram: FC<RiskRewardDiagramProps> = ({
  entryPrice,
  stopPrice,
  targetPrice,
  riskAmount,
  rewardAmount,
}) => {
  // Full-bleed responsive size
  const CHART_WIDTH = SCREEN_WIDTH - 48;   // generous side margins
  const CHART_HEIGHT = 420;                // tall & confident

  const PADDING_H = 24;
  const PADDING_TOP = 32;
  const PADDING_BOTTOM = 40;

  const { entryY, stopY, targetY } = useMemo(() => {
    const prices = [stopPrice, entryPrice, targetPrice];
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice || 1;
    const usable = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM;

    const priceToY = (p: number) =>
      PADDING_TOP + ((maxPrice - p) / range) * usable;

    return {
      entryY: priceToY(entryPrice),
      stopY: priceToY(stopPrice),
      targetY: priceToY(targetPrice),
    };
  }, [entryPrice, stopPrice, targetPrice]);

  const centerX = CHART_WIDTH * 0.15;  // Move much further left to make room for Risk/Reward labels
  const arrowX = CHART_WIDTH - PADDING_H - 40;  // Move arrow further left for more label space

  const mid = (a: number, b: number) => (a + b) / 2;

  return (
    <View style={styles.container}>
      <Svg width="100%" height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}>
        {/* Light background */}
        <Rect
          x={0}
          y={0}
          width={CHART_WIDTH}
          height={CHART_HEIGHT}
          fill="#F8FAFC"
          rx={24}
        />

        {/* Reward Arrow (big & proud) */}
        <Line x1={arrowX} y1={targetY} x2={arrowX} y2={entryY} stroke="#16a34a" strokeWidth={6} />
        <Line x1={arrowX-12} y1={targetY+18} x2={arrowX} y2={targetY} stroke="#16a34a" strokeWidth={6} />
        <Line x1={arrowX+12} y1={targetY+18} x2={arrowX} y2={targetY} stroke="#16a34a" strokeWidth={6} />

        {/* Reward label completely to the LEFT of the arrow */}
        <SvgText x={arrowX-185} y={mid(entryY, targetY)-12} fill="#16a34a" fontSize={18} fontWeight="700" textAnchor="start">
          Reward: ${rewardAmount.toFixed(2)}
        </SvgText>

        {/* Risk Arrow */}
        <Line x1={arrowX} y1={entryY} x2={arrowX} y2={stopY} stroke="#ef4444" strokeWidth={6} />
        <Line x1={arrowX-12} y1={stopY-18} x2={arrowX} y2={stopY} stroke="#ef4444" strokeWidth={6} />
        <Line x1={arrowX+12} y1={stopY-18} x2={arrowX} y2={stopY} stroke="#ef4444" strokeWidth={6} />

        {/* Risk label on the LEFT side of the arrow */}
        <SvgText x={arrowX-140} y={stopY + 50} fill="#ef4444" fontSize={18} fontWeight="700" textAnchor="start">
          Risk: ${riskAmount.toFixed(2)}
        </SvgText>

        {/* Target */}
        <Circle cx={centerX} cy={targetY} r={12} fill="#16a34a" />
        <SvgText x={centerX} y={targetY-48} fill="#16a34a" fontSize={16} fontWeight="800" textAnchor="middle">Target</SvgText>
        <SvgText x={centerX} y={targetY-24} fill="#1f2937" fontSize={20} fontWeight="700" textAnchor="middle">
          {targetPrice.toFixed(2)}
        </SvgText>

        {/* Entry */}
        <Circle cx={centerX} cy={entryY} r={12} fill="#2563eb" />
        <SvgText x={centerX} y={entryY-48} fill="#2563eb" fontSize={16} fontWeight="800" textAnchor="middle">Entry</SvgText>
        <SvgText x={centerX} y={entryY-24} fill="#1f2937" fontSize={20} fontWeight="700" textAnchor="middle">
          {entryPrice.toFixed(2)}
        </SvgText>

        {/* Stop */}
        <Circle cx={centerX} cy={stopY} r={12} fill="#ef4444" />
        <SvgText x={centerX} y={stopY+36} fill="#ef4444" fontSize={16} fontWeight="800" textAnchor="middle">Stop</SvgText>
        <SvgText x={centerX} y={stopY+60} fill="#1f2937" fontSize={20} fontWeight="700" textAnchor="middle">
          {stopPrice.toFixed(2)}
        </SvgText>
      </Svg>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    height: 480,                    // gives room + shadow margin
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderRadius: 28,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 6,
  },
});
