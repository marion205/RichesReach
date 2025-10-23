import React, { useMemo } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Dimensions,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';

interface Factor {
  name: string;
  weight: number;   // 0..1
  value: number;    // 0..1 (z or normalized)
  contrib: number;  // contribution in 0..100 scale from backend
  detail: string;
}

interface BudgetImpactModalProps {
  visible: boolean;
  onClose: () => void;
  stockSymbol: string;
  stockName: string;
  score: number;          // 0..100
  factors?: Factor[];     // optional & safe by default
  notes?: string[];       // optional
  /** NEW: make budget and price dynamic */
  budget?: number;        // e.g., 1000
  price?: number;         // current price
  currency?: string;      // e.g., 'USD'
}

const { width } = Dimensions.get('window');

const CURRENCY = 'USD'; // fallback

const formatCurrency = (n?: number, currency = CURRENCY) => {
  if (typeof n !== 'number' || !isFinite(n)) return '—';
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
  } catch {
    // minimal fallback
    return `$${(n || 0).toFixed(2)}`;
  }
};

const getFactorColor = (name: string) => {
  switch (name) {
    case 'Affordability': return '#FF6B35';
    case 'Size': return '#4CAF50';
    case 'Sector': return '#2196F3';
    case 'Value(PE)': return '#FF9800';
    case 'Dividend': return '#9C27B0';
    case 'Volatility': return '#F44336';
    case 'Beta': return '#E91E63';
    case 'Liquidity': return '#00BCD4';
    case 'Quality': return '#8BC34A';
    case 'Leverage': return '#795548';
    case 'Fame': return '#FFC107';
    default: return '#666';
  }
};

const getScoreColor = (score: number) => {
  if (score >= 80) return '#4CAF50';
  if (score >= 60) return '#FF9800';
  return '#F44336';
};

export default function BudgetImpactModal({
  visible,
  onClose,
  stockSymbol,
  stockName,
  score,
  factors = [],
  notes = [],
  budget = 1000,
  price,
  currency = CURRENCY,
}: BudgetImpactModalProps) {

  // Derived budget math (safe)
  const budgetInfo = useMemo(() => {
    const p = typeof price === 'number' && isFinite(price) && price > 0 ? price : undefined;
    const b = typeof budget === 'number' && isFinite(budget) && budget > 0 ? budget : undefined;
    if (!p || !b) {
      return {
        shares: 0,
        spend: 0,
        spendPct: 0,
        valid: false,
      };
    }
    const shares = Math.floor(b / p);
    const spend = shares * p;
    const spendPct = Math.min(100, Math.max(0, (spend / b) * 100));
    return { shares, spend, spendPct, valid: true };
  }, [price, budget]);

  // Find Affordability factor if backend provides it; otherwise we'll still show Budget section
  const affordabilityFactor = useMemo(
    () => factors.find(f => f.name === 'Affordability'),
    [factors]
  );

  // Sort factors by contribution magnitude (desc) for readability
  const sortedFactors = useMemo(() => {
    return [...factors].sort((a, b) => Math.abs(b.contrib) - Math.abs(a.contrib));
  }, [factors]);

  const renderFactor = ({ item }: { item: Factor }) => {
    const color = getFactorColor(item.name);
    const contribSign = item.contrib >= 0 ? '+' : '−';
    const contribAbs = Math.abs(item.contrib || 0).toFixed(1);

    return (
      <View style={styles.factorCard}>
        <View style={styles.factorHeader}>
          <View style={[styles.factorIcon, { backgroundColor: color }]}>
            <Text style={styles.factorIconText}>{item.name.charAt(0)}</Text>
          </View>

          <View style={styles.factorInfo}>
            <Text style={styles.factorName}>{item.name}</Text>
            <Text style={styles.factorDetail}>
              {item.detail}{' '}
              <Text style={styles.factorMeta}>
                (w={(item.weight || 0).toFixed(2)} • v={((item.value || 0) * 100).toFixed(0)})
              </Text>
            </Text>
          </View>

          <View
            style={[
              styles.factorScore,
              { backgroundColor: item.contrib >= 0 ? '#E8F5E9' : '#FFEBEE' },
            ]}
          >
            <Text
              style={[
                styles.factorScoreText,
                { color: item.contrib >= 0 ? '#2E7D32' : '#C62828' },
              ]}
              accessibilityLabel={`Contribution ${contribSign}${contribAbs} points`}
            >
              {contribSign}{contribAbs}
            </Text>
          </View>
        </View>

        {item.name === 'Affordability' && (
          <View style={styles.budgetExplanation}>
            <Text style={styles.budgetTitle}>💰 Budget Impact</Text>

            {budgetInfo.valid ? (
              <>
                <Text style={styles.budgetText}>
                  With a budget of {formatCurrency(budget, currency)} and a price of {formatCurrency(price, currency)},
                  you can buy <Text style={styles.bold}>{budgetInfo.shares}</Text> share{budgetInfo.shares === 1 ? '' : 's'}.
                </Text>
                <Text style={styles.budgetText}>
                  That would spend {formatCurrency(budgetInfo.spend, currency)} (
                  {(budgetInfo.spendPct || 0).toFixed(0)}% of your budget).
                </Text>
                <Text style={styles.budgetText}>
                  {item.value < 0.5
                    ? 'This stock is expensive relative to your budget, which reduces the beginner-friendly score.'
                    : 'This stock is reasonably affordable for your budget, which supports the beginner-friendly score.'}
                </Text>
              </>
            ) : (
              <Text style={styles.budgetText}>
                Add a valid price and budget to see personalized affordability details.
              </Text>
            )}
          </View>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.title} accessibilityRole="header">
              Budget Impact Analysis
            </Text>
            <TouchableOpacity
              onPress={onClose}
              style={styles.closeButton}
              accessibilityLabel="Close"
              accessibilityRole="button"
            >
              <Icon name="x" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <View style={styles.stockInfo}>
            <Text style={styles.stockSymbol}>{stockSymbol}</Text>
            <Text style={styles.stockName}>{stockName}</Text>
          </View>

          <View
            style={[
              styles.scoreContainer,
              { backgroundColor: getScoreColor(score) },
            ]}
            accessibilityLabel={`Beginner score ${score} out of 100`}
          >
            <Text style={styles.scoreText}>Score: {score}</Text>
          </View>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <Text style={styles.sectionTitle}>
            How Your {formatCurrency(budget, currency)} Budget Affects This Stock
          </Text>

          {/* If backend didn't send Affordability, still show budget block */}
          {!affordabilityFactor && (
            <View style={styles.factorCard}>
              <View style={styles.factorHeader}>
                <View style={[styles.factorIcon, { backgroundColor: getFactorColor('Affordability') }]}>
                  <Text style={styles.factorIconText}>A</Text>
                </View>
                <View style={styles.factorInfo}>
                  <Text style={styles.factorName}>Affordability</Text>
                  <Text style={styles.factorDetail}>
                    Based on your budget and current price.
                  </Text>
                </View>
              </View>

              <View style={styles.budgetExplanation}>
                <Text style={styles.budgetTitle}>💰 Budget Impact</Text>
                {budgetInfo.valid ? (
                  <>
                    <Text style={styles.budgetText}>
                      With a budget of {formatCurrency(budget, currency)} and a price of {formatCurrency(price, currency)},
                      you can buy <Text style={styles.bold}>{budgetInfo.shares}</Text> share{budgetInfo.shares === 1 ? '' : 's'}.
                    </Text>
                    <Text style={styles.budgetText}>
                      That would spend {formatCurrency(budgetInfo.spend, currency)} (
                      {(budgetInfo.spendPct || 0).toFixed(0)}% of your budget).
                    </Text>
                  </>
                ) : (
                  <Text style={styles.budgetText}>
                    Add a valid price and budget to see personalized affordability details.
                  </Text>
                )}
              </View>
            </View>
          )}

          <FlatList
            data={sortedFactors}
            keyExtractor={(f) => `${f.name}`}
            renderItem={renderFactor}
            scrollEnabled={false}
            ListEmptyComponent={
              <Text style={styles.emptyText}>
                No factor breakdown available for this stock.
              </Text>
            }
          />

          {!!notes?.length && (
            <View style={styles.notesSection}>
              <Text style={styles.sectionTitle}>Notes</Text>
              {notes.map((note, i) => (
                <Text key={`${i}-${note}`} style={styles.noteText}>• {note}</Text>
              ))}
            </View>
          )}

          <View style={styles.summarySection}>
            <Text style={styles.sectionTitle}>Summary</Text>
            <Text style={styles.summaryText}>
              This score blends fundamentals, risk, liquidity, and sector comfort, with your budget as a key consideration.
            </Text>
            <Text style={styles.summaryText}>
              Higher scores mean the stock is more suitable for beginners with your budget and risk profile.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: {
    backgroundColor: '#fff',
    paddingTop: 8,
    paddingBottom: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  headerContent: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12,
  },
  title: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  closeButton: { padding: 8 },
  stockInfo: { marginBottom: 12 },
  stockSymbol: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  stockName: { fontSize: 16, color: '#666', marginTop: 4 },
  scoreContainer: { alignSelf: 'flex-start', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20 },
  scoreText: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  content: { flex: 1, padding: 20 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 16 },
  factorCard: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2,
  },
  factorHeader: { flexDirection: 'row', alignItems: 'center' },
  factorIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  factorIconText: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  factorInfo: { flex: 1 },
  factorName: { fontSize: 16, fontWeight: '600', color: '#333' },
  factorDetail: { fontSize: 12, color: '#666', marginTop: 2 },
  factorMeta: { fontSize: 12, color: '#999' },
  factorScore: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  factorScoreText: { fontSize: 14, fontWeight: 'bold' },
  budgetExplanation: {
    marginTop: 12, padding: 12, backgroundColor: '#FFF5F0', borderRadius: 8, borderLeftWidth: 4, borderLeftColor: '#FF6B35',
  },
  budgetTitle: { fontSize: 14, fontWeight: 'bold', color: '#FF6B35', marginBottom: 8 },
  budgetText: { fontSize: 13, color: '#666', lineHeight: 18, marginBottom: 4 },
  bold: { fontWeight: '700', color: '#333' },
  notesSection: { marginTop: 20 },
  noteText: { fontSize: 14, color: '#666', marginBottom: 4, lineHeight: 20 },
  summarySection: { marginTop: 20, marginBottom: 40 },
  summaryText: { fontSize: 14, color: '#666', lineHeight: 20, marginBottom: 12 },
  emptyText: { color: '#777', fontSize: 14, marginBottom: 10 },
});

