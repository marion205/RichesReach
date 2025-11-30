import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

interface StrategyLeg {
  optionType: 'call' | 'put';
  action: 'buy' | 'sell';
  strike: number;
  quantity: number;
  premium?: number;
}

interface StrategyPayoffChartProps {
  legs: StrategyLeg[];
  underlyingPrice: number;
  expirationDays: number;
}

const screenWidth = Dimensions.get('window').width;

export default function StrategyPayoffChart({
  legs,
  underlyingPrice,
  expirationDays,
}: StrategyPayoffChartProps) {
  // Calculate payoff at different underlying prices
  const payoffData = useMemo(() => {
    const priceRange = underlyingPrice * 0.3; // ±30% range
    const minPrice = underlyingPrice - priceRange;
    const maxPrice = underlyingPrice + priceRange;
    const steps = 50;
    const stepSize = (maxPrice - minPrice) / steps;

    const prices: number[] = [];
    const payoffs: number[] = [];

    for (let i = 0; i <= steps; i++) {
      const price = minPrice + i * stepSize;
      prices.push(price);

      let totalPayoff = 0;

      // Calculate payoff for each leg
      for (const leg of legs) {
        const isCall = leg.optionType === 'call';
        const isBuy = leg.action === 'buy';
        const qty = leg.quantity;
        const strike = leg.strike;
        const premium = leg.premium || 0;

        let legPayoff = 0;

        if (isCall) {
          // Call option payoff
          const intrinsic = Math.max(0, price - strike);
          legPayoff = intrinsic - premium;
        } else {
          // Put option payoff
          const intrinsic = Math.max(0, strike - price);
          legPayoff = intrinsic - premium;
        }

        // If selling, reverse the payoff
        if (!isBuy) {
          legPayoff = -legPayoff;
        }

        totalPayoff += legPayoff * qty * 100; // Options are for 100 shares
      }

      payoffs.push(totalPayoff);
    }

    return { prices, payoffs };
  }, [legs, underlyingPrice]);

  // Find key points
  const maxProfit = Math.max(...payoffData.payoffs);
  const maxLoss = Math.min(...payoffData.payoffs);
  const breakevenPoints = payoffData.prices.filter((price, i) => {
    const prevPayoff = i > 0 ? payoffData.payoffs[i - 1] : null;
    const currPayoff = payoffData.payoffs[i];
    return prevPayoff !== null && prevPayoff <= 0 && currPayoff >= 0;
  });

  const chartData = {
    labels: payoffData.prices
      .filter((_, i) => i % 10 === 0) // Show every 10th label
      .map(p => `$${p.toFixed(0)}`),
    datasets: [
      {
        data: payoffData.payoffs,
        color: (opacity = 1) => {
          // Color based on profit/loss
          const avgPayoff = payoffData.payoffs.reduce((a, b) => a + b, 0) / payoffData.payoffs.length;
          return avgPayoff >= 0 ? `rgba(5, 150, 105, ${opacity})` : `rgba(220, 38, 38, ${opacity})`;
        },
        strokeWidth: 2,
      },
    ],
  };

  const chartConfig = {
    backgroundColor: '#FFFFFF',
    backgroundGradientFrom: '#FFFFFF',
    backgroundGradientTo: '#FFFFFF',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '0',
      strokeWidth: '0',
    },
    propsForBackgroundLines: {
      strokeDasharray: '',
    },
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Strategy Payoff</Text>
      <Text style={styles.subtitle}>Profit/Loss at expiration (${expirationDays} days)</Text>

      <View style={styles.chartContainer}>
        <LineChart
          data={chartData}
          width={screenWidth - 64}
          height={220}
          chartConfig={chartConfig}
          bezier
          withInnerLines={true}
          withOuterLines={false}
          withVerticalLabels={true}
          withHorizontalLabels={true}
          fromZero={false}
          style={styles.chart}
        />
      </View>

      {/* Key Metrics */}
      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Max Profit</Text>
          <Text style={[styles.metricValue, styles.metricValueProfit]}>
            ${maxProfit.toFixed(2)}
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Max Loss</Text>
          <Text style={[styles.metricValue, styles.metricValueLoss]}>
            ${maxLoss.toFixed(2)}
          </Text>
        </View>
        {breakevenPoints.length > 0 && (
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Breakeven</Text>
            <Text style={styles.metricValue}>
              ${breakevenPoints[0].toFixed(2)}
              {breakevenPoints.length > 1 && ` / $${breakevenPoints[1].toFixed(2)}`}
            </Text>
          </View>
        )}
      </View>

      {/* Current Price Indicator */}
      <View style={styles.currentPriceIndicator}>
        <View style={styles.currentPriceLine} />
        <Text style={styles.currentPriceText}>Current: ${underlyingPrice.toFixed(2)}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 16,
  },
  chartContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  metricValueProfit: {
    color: '#059669',
  },
  metricValueLoss: {
    color: '#DC2626',
  },
  currentPriceIndicator: {
    marginTop: 12,
    alignItems: 'center',
  },
  currentPriceLine: {
    width: 2,
    height: 20,
    backgroundColor: '#007AFF',
    marginBottom: 4,
  },
  currentPriceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
  },
});

