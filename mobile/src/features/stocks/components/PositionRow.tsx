import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useQuery } from '@apollo/client';
import SparkMini from '../../../components/charts/SparkMini';
import { GET_STOCK_CHART_DATA } from '../../../graphql/tradingQueries';

const C = {
  green: '#22C55E',
  red: '#EF4444',
  sub: '#6B7280',
  text: '#111827',
  primary: '#007AFF',
  line: '#E9EAF0',
};

interface PositionRowProps {
  position: {
    id?: string;
    symbol: string;
    quantity: number;
    marketValue?: number;
    costBasis?: number;
    unrealizedPl?: number;
    unrealizedpl?: number;
    unrealizedPL?: number;
    unrealizedPLPercent?: number;
    unrealizedPlpc?: number;
    currentPrice?: number;
    side?: string;
  };
}

export const PositionRow: React.FC<PositionRowProps> = React.memo(({ position }) => {
  const { data: chartData } = useQuery(GET_STOCK_CHART_DATA, {
    variables: { symbol: position.symbol, timeframe: '1D' },
    errorPolicy: 'all',
    fetchPolicy: 'cache-first',
  });

  const chartPrices = chartData?.stockChartData?.data?.map((d: any) => d.close) || [];

  // Normalize inconsistent server fields
  const plPct =
    Number(position.unrealizedPlpc ?? position.unrealizedPLPercent ?? 0);
  const unrealizedPl =
    Number(position.unrealizedPl ?? position.unrealizedpl ?? position.unrealizedPL ?? 0);
  const isUp = unrealizedPl >= 0;

  return (
    <View style={styles.positionRow}>
      <View style={styles.tickerAvatar}>
        <Text style={styles.tickerAvatarText}>{position.symbol?.[0]}</Text>
      </View>

      <View style={{ flex: 1, paddingRight: 8 }}>
        <View style={styles.rowBetween}>
          <Text style={styles.ticker}>{position.symbol}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <SparkMini
              data={chartPrices}
              width={70}
              height={18}
              upColor={C.green}
              downColor={C.red}
              neutralColor={C.sub}
            />
            <View
              style={[
                styles.chip,
                {
                  backgroundColor: isUp ? '#EAFBF1' : '#FEECEC',
                },
              ]}
            >
              <Text
                style={[
                  styles.chipText,
                  {
                    color: isUp ? C.green : C.red,
                  },
                ]}
              >
                {isUp ? '+' : ''}
                {plPct.toFixed(2)}%
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.sub}>
            {position.quantity} shares • @ ${position.currentPrice?.toFixed(2)}
          </Text>
          <Text style={[styles.value, { color: isUp ? C.green : C.red }]}>
            {isUp ? '+' : ''}${unrealizedPl.toFixed(2)}
          </Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.sub}>Value</Text>
          <Text style={styles.value}>
            ${position.marketValue?.toLocaleString()}
          </Text>
        </View>
      </View>
    </View>
  );
});

PositionRow.displayName = 'PositionRow';

const styles = StyleSheet.create({
  positionRow: {
    flexDirection: 'row',
    gap: 12,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: C.line,
  },
  tickerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: '#EEF2FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  tickerAvatarText: {
    fontWeight: '800',
    color: C.primary,
  },
  ticker: {
    fontSize: 16,
    fontWeight: '800',
    color: C.text,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  sub: {
    fontSize: 13,
    color: C.sub,
  },
  value: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    alignSelf: 'flex-start',
  },
  chipText: {
    fontSize: 11,
    fontWeight: '700',
  },
});

