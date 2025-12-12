/**
 * Example: Using Typed RAHA Hooks in a Component
 *
 * This shows how to use the typed hooks in a real component
 */

import React from 'react';
import { View, Text, FlatList, ActivityIndicator } from 'react-native';
import { useStrategies } from '../hooks/useStrategies.typed';
import { useRAHASignals, getTopConfidenceSignal } from '../hooks/useRAHASignals.typed';
import type { StrategyType, RahaSignalType } from '../../../generated/graphql';

/**
 * Example: Strategy List Component with Full Type Safety
 */
export function StrategyListExample() {
  const { strategies, loading, error } = useStrategies('STOCKS', 'MOMENTUM');

  if (loading) {
    return <ActivityIndicator />;
  }
  if (error) {
    return <Text>Error: {error.message}</Text>;
  }

  return (
    <FlatList
      data={strategies}
      keyExtractor={item => item.id}
      renderItem={({ item }) => <StrategyCard strategy={item} />}
    />
  );
}

/**
 * Strategy Card - Fully typed props
 */
function StrategyCard({ strategy }: { strategy: StrategyType }) {
  // ✅ TypeScript knows all fields on StrategyType
  return (
    <View>
      <Text>{strategy.name}</Text>
      <Text>{strategy.description}</Text>
      <Text>Category: {strategy.category}</Text>
      <Text>Market: {strategy.marketType}</Text>
      {/* TypeScript will error if you try to access non-existent fields */}
    </View>
  );
}

/**
 * Example: RAHA Signals Component
 */
export function RAHASignalsExample({ symbol }: { symbol: string }) {
  const { signals, loading, error } = useRAHASignals(symbol, '5m', 10);

  if (loading) {
    return <ActivityIndicator />;
  }
  if (error) {
    return <Text>Error: {error.message}</Text>;
  }

  // ✅ Get top signal using typed helper
  const topSignal = getTopConfidenceSignal(signals);

  return (
    <View>
      <Text>Signals for {symbol}</Text>
      {topSignal && (
        <Text>
          Top Signal: {topSignal.signalType} @ ${topSignal.price}
        </Text>
      )}
      <FlatList
        data={signals}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <SignalCard signal={item} />}
      />
    </View>
  );
}

/**
 * Signal Card - Fully typed props
 */
function SignalCard({ signal }: { signal: RahaSignalType }) {
  // ✅ All fields are typed - no runtime surprises!
  return (
    <View>
      <Text>{signal.symbol}</Text>
      <Text>Type: {signal.signalType}</Text>
      <Text>Price: ${signal.price}</Text>
      <Text>Confidence: {signal.confidenceScore}%</Text>
      {signal.stopLoss && <Text>Stop Loss: ${signal.stopLoss}</Text>}
      {signal.takeProfit && <Text>Take Profit: ${signal.takeProfit}</Text>}
    </View>
  );
}

/**
 * Example: Typed Business Logic Function
 *
 * This shows how to use generated types in helper functions
 */
export function calculateStrategyPerformance(strategies: StrategyType[]): {
  total: number;
  enabled: number;
  byCategory: Record<string, number>;
} {
  // ✅ TypeScript knows the exact shape of StrategyType
  const enabled = strategies.filter(s => s.enabled).length;

  const byCategory: Record<string, number> = {};
  strategies.forEach(strategy => {
    const category = strategy.category || 'Unknown';
    byCategory[category] = (byCategory[category] || 0) + 1;
  });

  return {
    total: strategies.length,
    enabled,
    byCategory,
  };
}
