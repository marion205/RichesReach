import React, { useMemo, useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Dimensions } from 'react-native';
import Svg, { Path, Line, Defs, LinearGradient, Stop, Circle, G, Text as SvgText } from 'react-native-svg';

const { width: screenWidth } = Dimensions.get('window');

interface PNLRibbonOverlayProps {
  entryPrice: number;
  takeProfit: number;
  stopLoss: number;
  isLong: boolean;
  currentPrice: number;
  priceData: Array<{ timestamp: string; close: number }>;
  chartWidth: number;
  chartHeight: number;
  minPrice: number;
  maxPrice: number;
  riskAmount: number;
  visible: boolean;
  onToggle?: () => void;
}

export default function PNLRibbonOverlay({
  entryPrice,
  takeProfit,
  stopLoss,
  isLong,
  currentPrice,
  priceData,
  chartWidth,
  chartHeight,
  minPrice,
  maxPrice,
  riskAmount,
  visible,
  onToggle,
}: PNLRibbonOverlayProps) {
  const ribbonOpacity = useRef(new Animated.Value(0)).current;
  const ribbonProgress = useRef(new Animated.Value(0)).current;
  const finalNumberOpacity = useRef(new Animated.Value(0)).current;
  const finalNumberScale = useRef(new Animated.Value(0.8)).current;
  const glowIntensity = useRef(new Animated.Value(0.3)).current;
  const [progressValue, setProgressValue] = useState(0);
  const [showFinalNumber, setShowFinalNumber] = useState(false);

  // Calculate P&L at each price point
  const pnlData = useMemo(() => {
    if (!priceData || priceData.length === 0) return [];
    
    const risk = Math.abs(entryPrice - stopLoss);
    const reward = Math.abs(takeProfit - entryPrice);
    const rMultiple = reward / risk;
    
    return priceData.map((point, index) => {
      const price = point.close;
      let pnl = 0;
      
      if (isLong) {
        // Long position: profit if price goes up, loss if down
        if (price >= takeProfit) {
          // Hit take profit
          pnl = riskAmount * rMultiple;
        } else if (price <= stopLoss) {
          // Hit stop loss
          pnl = -riskAmount;
        } else {
          // Unrealized P&L
          const priceMove = price - entryPrice;
          const priceRange = takeProfit - entryPrice;
          pnl = (priceMove / priceRange) * (riskAmount * rMultiple);
        }
      } else {
        // Short position: profit if price goes down, loss if up
        if (price <= takeProfit) {
          // Hit take profit
          pnl = riskAmount * rMultiple;
        } else if (price >= stopLoss) {
          // Hit stop loss
          pnl = -riskAmount;
        } else {
          // Unrealized P&L
          const priceMove = entryPrice - price;
          const priceRange = entryPrice - takeProfit;
          pnl = (priceMove / priceRange) * (riskAmount * rMultiple);
        }
      }
      
      return {
        x: (index / (priceData.length - 1)) * chartWidth,
        pnl,
        price,
      };
    });
  }, [priceData, entryPrice, takeProfit, stopLoss, isLong, riskAmount, chartWidth]);

  // Calculate final P&L
  const finalPNL = useMemo(() => {
    if (pnlData.length === 0) return 0;
    return pnlData[pnlData.length - 1].pnl;
  }, [pnlData]);

  // Find entry point on chart
  const entryPoint = useMemo(() => {
    if (!priceData || priceData.length === 0) return { x: 0, y: chartHeight / 2 };
    
    // Find closest price point to entry
    let closestIndex = 0;
    let minDiff = Math.abs(priceData[0].close - entryPrice);
    
    for (let i = 1; i < priceData.length; i++) {
      const diff = Math.abs(priceData[i].close - entryPrice);
      if (diff < minDiff) {
        minDiff = diff;
        closestIndex = i;
      }
    }
    
    const x = (closestIndex / (priceData.length - 1)) * chartWidth;
    const priceY = chartHeight - ((entryPrice - minPrice) / (maxPrice - minPrice)) * chartHeight;
    
    return { x, y: priceY };
  }, [priceData, entryPrice, minPrice, maxPrice, chartWidth, chartHeight]);

  // Animate ribbon appearing
  useEffect(() => {
    if (visible && pnlData.length > 0) {
      // Start glow pulse
      Animated.loop(
        Animated.sequence([
          Animated.timing(glowIntensity, {
            toValue: 0.6,
            duration: 2000,
            useNativeDriver: false,
          }),
          Animated.timing(glowIntensity, {
            toValue: 0.3,
            duration: 2000,
            useNativeDriver: false,
          }),
        ])
      ).start();

      // Fade in ribbon with smoother easing
      Animated.timing(ribbonOpacity, {
        toValue: 1,
        duration: 900,
        easing: Easing.out(Easing.quad), // Smooth ease-out
        useNativeDriver: true,
      }).start(() => {
        // Animate ribbon drawing forward with smoother curve
        Animated.timing(ribbonProgress, {
          toValue: 1,
          duration: 1800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: false,
        }).start(({ finished }) => {
          if (finished) {
            setShowFinalNumber(true);
            // Final number appears with polished animation
            Animated.parallel([
              Animated.timing(finalNumberOpacity, {
                toValue: 1,
                duration: 700,
                easing: Easing.out(Easing.quad),
                useNativeDriver: true,
              }),
              Animated.spring(finalNumberScale, {
                toValue: 1,
                tension: 60,
                friction: 8,
                useNativeDriver: true,
              }),
            ]).start();
          }
        });
        
        // Track progress value for rendering
        const progressListener = ribbonProgress.addListener(({ value }) => {
          setProgressValue(value);
        });
        
        return () => {
          ribbonProgress.removeListener(progressListener);
        };
      });
    } else {
      // Reset animations when hidden
      ribbonOpacity.setValue(0);
      ribbonProgress.setValue(0);
      finalNumberOpacity.setValue(0);
      finalNumberScale.setValue(0.8);
      setProgressValue(0);
      setShowFinalNumber(false);
    }
  }, [visible, pnlData.length]);

  if (!visible || pnlData.length === 0) return null;

  // Calculate P&L range for Y-axis scaling
  const minPNL = Math.min(0, ...pnlData.map(d => d.pnl));
  const maxPNL = Math.max(0, ...pnlData.map(d => d.pnl));
  const pnlRange = maxPNL - minPNL || 1;
  
  // Zero line Y position (breakeven) - use middle of chart for better visibility
  const zeroY = chartHeight / 2;
  
  // Adjust P&L Y positions to be relative to zero line in center
  const pnlScale = Math.min(chartHeight / 2 / Math.max(Math.abs(maxPNL), Math.abs(minPNL)), chartHeight / 2 / 500); // Scale to fit, max $500 range
  
  // Build ribbon path - P&L relative to zero line in center
  const ribbonPath = useMemo(() => {
    const progress = progressValue;
    const visiblePoints = Math.floor(pnlData.length * progress);
    
    if (visiblePoints < 2) return '';
    
    // Start at entry point (on zero line)
    let path = `M ${entryPoint.x} ${zeroY}`;
    
    // Draw to each P&L point (positive goes up, negative goes down from center)
    for (let i = 0; i < visiblePoints; i++) {
      const point = pnlData[i];
      const y = zeroY - (point.pnl * pnlScale); // Negative because SVG Y increases downward
      path += ` L ${point.x} ${y}`;
    }
    
    // Close path back to zero line for gradient fill
    if (visiblePoints > 0) {
      const lastPoint = pnlData[visiblePoints - 1];
      path += ` L ${lastPoint.x} ${zeroY} Z`;
    }
    
    return path;
  }, [pnlData, entryPoint, zeroY, pnlScale, progressValue]);

  // Final P&L position (relative to zero line in center)
  const finalPNLPoint = pnlData[pnlData.length - 1];
  const finalPNLY = zeroY - (finalPNL * pnlScale);
  const finalPNLColor = finalPNL >= 0 ? '#10B981' : '#EF4444';

  return (
    <Animated.View
      style={[
        StyleSheet.absoluteFill,
        {
          opacity: ribbonOpacity,
        },
      ]}
      pointerEvents="none"
    >
      <Svg width={chartWidth} height={chartHeight} style={styles.ribbonSvg}>
        <Defs>
          {/* Glowing gradient for ribbon */}
          <LinearGradient id="pnlGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <Stop offset="0%" stopColor={finalPNLColor} stopOpacity="0.4" />
            <Stop offset="50%" stopColor={finalPNLColor} stopOpacity="0.25" />
            <Stop offset="100%" stopColor={finalPNLColor} stopOpacity="0.1" />
          </LinearGradient>
          
          {/* Glow filter effect */}
          <LinearGradient id="glowGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <Stop offset="0%" stopColor={finalPNLColor} stopOpacity="0.6" />
            <Stop offset="100%" stopColor={finalPNLColor} stopOpacity="0.0" />
          </LinearGradient>
        </Defs>

        {/* Subtle zero line (breakeven) */}
        <Line
          x1={0}
          y1={zeroY}
          x2={chartWidth}
          y2={zeroY}
          stroke="#9CA3AF"
          strokeWidth={1}
          strokeDasharray="4,4"
          opacity={0.4}
        />
        
        {/* Zero line label - more prominent */}
        <SvgText
          x={8}
          y={zeroY - 8}
          fontSize="12"
          fill="#6B7280"
          fontWeight="700"
        >
          $0 Breakeven
        </SvgText>
        
        {/* Y-axis P&L labels */}
        {maxPNL > 0 && (
          <SvgText
            x={8}
            y={20}
            fontSize="11"
            fill="#10B981"
            fontWeight="600"
          >
            +${Math.round(maxPNL)}
          </SvgText>
        )}
        {minPNL < 0 && (
          <SvgText
            x={8}
            y={chartHeight - 8}
            fontSize="11"
            fill="#EF4444"
            fontWeight="600"
          >
            {Math.round(minPNL)}
          </SvgText>
        )}

        {/* P&L Ribbon (area fill) */}
        {ribbonPath && (
          <Path
            d={ribbonPath}
            fill="url(#pnlGradient)"
            stroke="none"
          />
        )}

        {/* P&L Ribbon outline (glowing line) */}
        {ribbonPath && (
          <Path
            d={ribbonPath.split(' Z')[0]} // Remove close path for outline
            fill="none"
            stroke={finalPNLColor}
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.8}
          />
        )}

        {/* Entry point marker - on zero line */}
        <G transform={`translate(${entryPoint.x}, ${zeroY})`}>
          <Circle
            cx={0}
            cy={0}
            r={8}
            fill="#3B82F6"
            opacity={0.9}
          />
          <Circle
            cx={0}
            cy={0}
            r={4}
            fill="#FFFFFF"
          />
          <SvgText
            x={12}
            y={5}
            fontSize="11"
            fill="#3B82F6"
            fontWeight="700"
          >
            Entry ${entryPrice.toFixed(2)}
          </SvgText>
        </G>

        {/* Final P&L number marker */}
        {showFinalNumber && (
          <G
            opacity={finalNumberOpacity as any}
            transform={`translate(${finalPNLPoint.x}, ${finalPNLY}) scale(${(finalNumberScale as any).__getValue?.() || 0.8})`}
          >
            {/* Glow circle */}
            <Circle
              cx={0}
              cy={0}
              r={25}
              fill={finalPNLColor}
              opacity={0.2}
            />
            <Circle
              cx={0}
              cy={0}
              r={20}
              fill={finalPNLColor}
              opacity={0.3}
            />
            {/* Center dot */}
            <Circle
              cx={0}
              cy={0}
              r={4}
              fill={finalPNLColor}
            />
          </G>
        )}
        
        {/* P&L value labels along the ribbon (show multiple key points) */}
        {progressValue > 0.3 && pnlData.length > 0 && (
          <>
            {/* Show labels at 25%, 50%, 75% of progress */}
            {[0.25, 0.5, 0.75].map((ratio) => {
              if (progressValue < ratio) return null;
              const index = Math.floor(pnlData.length * ratio);
              if (index >= pnlData.length) return null;
              const point = pnlData[index];
              const y = zeroY - (point.pnl * pnlScale);
              return (
                <G key={ratio} transform={`translate(${point.x}, ${y})`}>
                  <Circle
                    cx={0}
                    cy={0}
                    r={3}
                    fill={point.pnl >= 0 ? '#10B981' : '#EF4444'}
                  />
                  <SvgText
                    x={point.pnl >= 0 ? -30 : -30}
                    y={point.pnl >= 0 ? -10 : 18}
                    fontSize="12"
                    fill={point.pnl >= 0 ? '#10B981' : '#EF4444'}
                    fontWeight="700"
                  >
                    {point.pnl >= 0 ? '+' : ''}${Math.round(point.pnl)}
                  </SvgText>
                </G>
              );
            })}
          </>
        )}
      </Svg>

      {/* Final P&L number text - HUGE and impossible to miss */}
      {showFinalNumber && (
        <Animated.View
          style={[
            styles.finalPNLContainer,
            {
              left: (chartWidth / 2) - 100,
              top: finalPNLY < zeroY ? finalPNLY - 90 : finalPNLY + 20, // Position above if profit, below if loss
              opacity: finalNumberOpacity,
              transform: [{ scale: finalNumberScale }],
            },
          ]}
        >
          <View style={[styles.finalPNLBadge, { backgroundColor: finalPNLColor + '20', borderColor: finalPNLColor, borderWidth: 2 }]}>
            <Text style={styles.finalPNLLabel}>PROJECTED PROFIT/LOSS</Text>
            <Text style={[styles.finalPNLText, { color: finalPNLColor }]}>
              {finalPNL >= 0 ? '+' : ''}${Math.round(Math.abs(finalPNL))}
            </Text>
            <Text style={styles.finalPNLSubtext}>
              {finalPNL >= 0 ? 'Profit' : 'Loss'} if price reaches target
            </Text>
          </View>
        </Animated.View>
      )}
      
      {/* Summary Card - Moved to bottom to avoid covering projected profit */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>P&L Breakdown</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Entry:</Text>
          <Text style={styles.summaryValue}>${entryPrice.toFixed(2)}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Take Profit:</Text>
          <Text style={[styles.summaryValue, { color: '#10B981' }]}>${takeProfit.toFixed(2)}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Stop Loss:</Text>
          <Text style={[styles.summaryValue, { color: '#EF4444' }]}>${stopLoss.toFixed(2)}</Text>
        </View>
        <View style={[styles.summaryRow, styles.summaryRowFinal]}>
          <Text style={styles.summaryLabel}>Projected P&L:</Text>
          <Text style={[styles.summaryValue, styles.summaryValueFinal, { color: finalPNLColor }]}>
            {finalPNL >= 0 ? '+' : ''}${Math.round(Math.abs(finalPNL))}
          </Text>
        </View>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  ribbonSvg: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  finalPNLContainer: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 120,
  },
  finalPNLBadge: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  finalPNLLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  finalPNLText: {
    fontSize: 20,
    fontWeight: '800',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  finalPNLSubtext: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
    marginTop: 4,
  },
  summaryCard: {
    position: 'absolute',
    bottom: 20, // Moved to bottom to avoid covering projected profit
    right: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    padding: 12,
    borderRadius: 12,
    minWidth: 140,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    zIndex: 10,
  },
  summaryTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  summaryRowFinal: {
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    marginBottom: 0,
  },
  summaryLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: '#6B7280',
  },
  summaryValue: {
    fontSize: 11,
    fontWeight: '600',
    color: '#111827',
  },
  summaryValueFinal: {
    fontSize: 14,
    fontWeight: '800',
  },
});

