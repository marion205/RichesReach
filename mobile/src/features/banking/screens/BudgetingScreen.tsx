import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const GET_BUDGET_DATA = gql`
  query GetBudgetData {
    budgetData {
      monthlyIncome
      monthlyExpenses
      categories {
        name
        budgeted
        spent
        percentage
      }
      remaining
      savingsRate
    }
  }
`;

interface BudgetCategory {
  name: string;
  budgeted: number;
  spent: number;
  percentage: number;
}

interface BudgetData {
  monthlyIncome: number;
  monthlyExpenses: number;
  categories: BudgetCategory[];
  remaining: number;
  savingsRate: number;
}

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  text: '#111827',
  sub: '#6B7280',
  primary: '#0E7AFE',
  success: '#22C55E',
  danger: '#EF4444',
  warning: '#F59E0B',
  border: '#E5E7EB',
};

export default function BudgetingScreen() {
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('month');

  const { data, loading, error, refetch } = useQuery<{ budgetData: BudgetData }>(GET_BUDGET_DATA, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    onError: (err) => {
      console.error('Budget query error:', err);
      console.error('Error details:', JSON.stringify(err, null, 2));
    },
  });

  const budgetData = data?.budgetData;

  // Mock data fallback
  const mockBudget: BudgetData = {
    monthlyIncome: 5000,
    monthlyExpenses: 3500,
    categories: [
      { name: 'Housing', budgeted: 1500, spent: 1450, percentage: 96.7 },
      { name: 'Food', budgeted: 600, spent: 580, percentage: 96.7 },
      { name: 'Transportation', budgeted: 400, spent: 420, percentage: 105 },
      { name: 'Entertainment', budgeted: 300, spent: 250, percentage: 83.3 },
      { name: 'Utilities', budgeted: 200, spent: 180, percentage: 90 },
      { name: 'Other', budgeted: 500, spent: 620, percentage: 124 },
    ],
    remaining: 1500,
    savingsRate: 30,
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={C.primary} />
      </View>
    );
  }

  // Use real data if available, otherwise use mock (even on error)
  const budget = budgetData || mockBudget;
  
  // Show warning banner if using mock data due to error
  const showErrorBanner = error && !budgetData;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Error Banner (if using mock data) */}
      {showErrorBanner && (
        <View style={[styles.card, { borderLeftColor: C.danger, marginBottom: 16 }]}>
          <Icon name="alert-circle" size={20} color={C.danger} />
          <Text style={[styles.errorText, { color: C.danger }]}>
            Using sample data - {error?.message || 'Backend connection failed'}
          </Text>
          <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Budget Management</Text>
        <View style={styles.periodSelector}>
          {(['week', 'month', 'year'] as const).map(period => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                { backgroundColor: selectedPeriod === period ? C.primary : C.card },
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text
                style={[
                  styles.periodText,
                  { color: selectedPeriod === period ? '#FFFFFF' : C.sub },
                ]}
              >
                {period.charAt(0).toUpperCase() + period.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Summary Cards */}
      <View style={styles.summaryGrid}>
        <View style={[styles.summaryCard, { backgroundColor: C.card }]}>
          <Text style={[styles.summaryLabel, { color: C.sub }]}>Monthly Income</Text>
          <Text style={[styles.summaryValue, { color: C.text }]}>
            ${budget.monthlyIncome.toLocaleString()}
          </Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: C.card }]}>
          <Text style={[styles.summaryLabel, { color: C.sub }]}>Monthly Expenses</Text>
          <Text style={[styles.summaryValue, { color: C.danger }]}>
            ${budget.monthlyExpenses.toLocaleString()}
          </Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: C.card }]}>
          <Text style={[styles.summaryLabel, { color: C.sub }]}>Remaining</Text>
          <Text style={[styles.summaryValue, { color: C.success }]}>
            ${budget.remaining.toLocaleString()}
          </Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: C.card }]}>
          <Text style={[styles.summaryLabel, { color: C.sub }]}>Savings Rate</Text>
          <Text style={[styles.summaryValue, { color: C.primary }]}>
            {budget.savingsRate}%
          </Text>
        </View>
      </View>

      {/* Category Breakdown */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Category Breakdown</Text>
        {budget.categories.map((category, index) => {
          const isOverBudget = category.percentage > 100;
          const color = isOverBudget ? C.danger : category.percentage > 90 ? C.warning : C.success;

          return (
            <View key={index} style={[styles.categoryCard, { backgroundColor: C.card }]}>
              <View style={styles.categoryHeader}>
                <Text style={[styles.categoryName, { color: C.text }]}>{category.name}</Text>
                <View style={styles.categoryAmounts}>
                  <Text style={[styles.categorySpent, { color }]}>
                    ${category.spent.toLocaleString()}
                  </Text>
                  <Text style={[styles.categoryBudgeted, { color: C.sub }]}>
                    / ${category.budgeted.toLocaleString()}
                  </Text>
                </View>
              </View>
              <View style={styles.progressBar}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(category.percentage, 100)}%`,
                      backgroundColor: color,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.categoryPercentage, { color: C.sub }]}>
                {category.percentage.toFixed(1)}% of budget
              </Text>
            </View>
          );
        })}
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
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: C.text,
    marginBottom: 16,
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  periodButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  periodText: {
    fontSize: 14,
    fontWeight: '600',
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  summaryCard: {
    width: '47%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
  },
  summaryLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: C.text,
    marginBottom: 16,
  },
  categoryCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 12,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
  },
  categoryAmounts: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  categorySpent: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  categoryBudgeted: {
    fontSize: 14,
  },
  progressBar: {
    height: 8,
    backgroundColor: C.border,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  categoryPercentage: {
    fontSize: 12,
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
  retryButton: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: C.primary,
    borderRadius: 6,
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
});

