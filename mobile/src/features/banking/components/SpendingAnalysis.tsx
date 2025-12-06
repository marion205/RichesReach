import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Dimensions,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import { PieChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

const GET_SPENDING_ANALYSIS = gql`
  query GetSpendingAnalysis($period: String!) {
    spendingAnalysis(period: $period) {
      totalSpent
      categories {
        name
        amount
        percentage
        transactions
        trend
      }
      topMerchants {
        name
        amount
        count
      }
      trends {
        period
        amount
        change
      }
    }
  }
`;

interface SpendingCategory {
  name: string;
  amount: number;
  percentage: number;
  transactions: number;
  trend: 'up' | 'down' | 'stable';
}

interface TopMerchant {
  name: string;
  amount: number;
  count: number;
}

interface SpendingAnalysis {
  totalSpent: number;
  categories: SpendingCategory[];
  topMerchants: TopMerchant[];
  trends: Array<{
    period: string;
    amount: number;
    change: number;
  }>;
}

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  text: '#111827',
  sub: '#6B7280',
  primary: '#0E7AFE',
  success: '#22C55E',
  danger: '#EF4444',
  border: '#E5E7EB',
};

const COLORS = ['#0E7AFE', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];

export default function SpendingAnalysis({ period = 'month' }: { period?: string }) {
  const { data, loading, error } = useQuery<{ spendingAnalysis: SpendingAnalysis }>(
    GET_SPENDING_ANALYSIS,
    {
      variables: { period },
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    }
  );

  const analysis = data?.spendingAnalysis;

  // Mock data fallback
  const mockAnalysis: SpendingAnalysis = {
    totalSpent: 3500,
    categories: [
      { name: 'Housing', amount: 1450, percentage: 41.4, transactions: 2, trend: 'stable' },
      { name: 'Food', amount: 580, percentage: 16.6, transactions: 45, trend: 'up' },
      { name: 'Transportation', amount: 420, percentage: 12, transactions: 12, trend: 'down' },
      { name: 'Entertainment', amount: 250, percentage: 7.1, transactions: 8, trend: 'up' },
      { name: 'Utilities', amount: 180, percentage: 5.1, transactions: 4, trend: 'stable' },
      { name: 'Other', amount: 620, percentage: 17.7, transactions: 23, trend: 'up' },
    ],
    topMerchants: [
      { name: 'Amazon', amount: 320, count: 15 },
      { name: 'Whole Foods', amount: 280, count: 12 },
      { name: 'Uber', amount: 180, count: 25 },
      { name: 'Netflix', amount: 15, count: 1 },
    ],
    trends: [
      { period: 'Jan', amount: 3200, change: 0 },
      { period: 'Feb', amount: 3400, change: 6.25 },
      { period: 'Mar', amount: 3500, change: 2.94 },
    ],
  };

  // Use real data if available, otherwise use mock (even on error)
  const spendingData = analysis || mockAnalysis;
  
  // Show warning banner if using mock data due to error
  const showErrorBanner = error && !analysis;

  const chartData = useMemo(() => {
    return spendingData.categories.map((cat, index) => ({
      name: cat.name,
      amount: cat.amount,
      color: COLORS[index % COLORS.length],
      legendFontColor: C.text,
      legendFontSize: 12,
    }));
  }, [spendingData.categories]);

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading spending analysis...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Error Banner (if using mock data) */}
      {showErrorBanner && (
        <View style={[styles.card, { borderLeftColor: C.danger, marginBottom: 16 }]}>
          <Icon name="alert-circle" size={20} color={C.danger} />
          <Text style={[styles.errorText, { color: C.danger }]}>
            Using sample data - {error?.message || 'Backend connection failed'}
          </Text>
        </View>
      )}
      {/* Total Spent */}
      <View style={[styles.totalCard, { backgroundColor: C.card }]}>
        <Text style={[styles.totalLabel, { color: C.sub }]}>Total Spent</Text>
        <Text style={[styles.totalAmount, { color: C.text }]}>
          ${spendingData.totalSpent.toLocaleString()}
        </Text>
      </View>

      {/* Pie Chart */}
      <View style={[styles.chartCard, { backgroundColor: C.card }]}>
        <Text style={[styles.chartTitle, { color: C.text }]}>Spending by Category</Text>
        <PieChart
          data={chartData}
          width={width - 64}
          height={220}
          chartConfig={{
            color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
          }}
          accessor="amount"
          backgroundColor="transparent"
          paddingLeft="15"
          absolute
        />
      </View>

      {/* Category List */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: C.text }]}>Category Details</Text>
        {spendingData.categories.map((category, index) => (
          <View key={index} style={[styles.categoryRow, { backgroundColor: C.card }]}>
            <View style={styles.categoryInfo}>
              <View
                style={[
                  styles.colorIndicator,
                  { backgroundColor: COLORS[index % COLORS.length] },
                ]}
              />
              <View style={styles.categoryText}>
                <Text style={[styles.categoryName, { color: C.text }]}>{category.name}</Text>
                <Text style={[styles.categoryMeta, { color: C.sub }]}>
                  {category.transactions} transactions
                </Text>
              </View>
            </View>
            <View style={styles.categoryAmount}>
              <Text style={[styles.categoryValue, { color: C.text }]}>
                ${category.amount.toLocaleString()}
              </Text>
              <Text style={[styles.categoryPercent, { color: C.sub }]}>
                {category.percentage.toFixed(1)}%
              </Text>
            </View>
            <Icon
              name={
                category.trend === 'up'
                  ? 'trending-up'
                  : category.trend === 'down'
                  ? 'trending-down'
                  : 'minus'
              }
              size={16}
              color={
                category.trend === 'up'
                  ? C.danger
                  : category.trend === 'down'
                  ? C.success
                  : C.sub
              }
            />
          </View>
        ))}
      </View>

      {/* Top Merchants */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: C.text }]}>Top Merchants</Text>
        {spendingData.topMerchants.map((merchant, index) => (
          <View key={index} style={[styles.merchantRow, { backgroundColor: C.card }]}>
            <View style={styles.merchantInfo}>
              <Text style={[styles.merchantName, { color: C.text }]}>{merchant.name}</Text>
              <Text style={[styles.merchantCount, { color: C.sub }]}>
                {merchant.count} transactions
              </Text>
            </View>
            <Text style={[styles.merchantAmount, { color: C.text }]}>
              ${merchant.amount.toLocaleString()}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  content: {
    padding: 16,
  },
  totalCard: {
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 16,
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  totalAmount: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  chartCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 16,
    alignItems: 'center',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 8,
  },
  categoryInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  colorIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  categoryText: {
    flex: 1,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  categoryMeta: {
    fontSize: 12,
  },
  categoryAmount: {
    alignItems: 'flex-end',
    marginRight: 12,
  },
  categoryValue: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  categoryPercent: {
    fontSize: 12,
  },
  merchantRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 8,
  },
  merchantInfo: {
    flex: 1,
  },
  merchantName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  merchantCount: {
    fontSize: 12,
  },
  merchantAmount: {
    fontSize: 18,
    fontWeight: '600',
  },
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: C.sub,
    textAlign: 'center',
    padding: 20,
  },
});

