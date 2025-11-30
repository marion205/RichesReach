import React from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions } from 'react-native';
import RustForexWidget from '../../components/rust/RustForexWidget';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

interface ForexScreenProps {
  navigation?: any;
}

export default function ForexScreen({ navigation }: ForexScreenProps) {
  const majorPairs = [
    { pair: 'EURUSD', label: 'Euro / US Dollar' },
    { pair: 'GBPUSD', label: 'British Pound / US Dollar' },
    { pair: 'USDJPY', label: 'US Dollar / Japanese Yen' },
    { pair: 'AUDUSD', label: 'Australian Dollar / US Dollar' },
    { pair: 'USDCAD', label: 'US Dollar / Canadian Dollar' },
    { pair: 'USDCHF', label: 'US Dollar / Swiss Franc' },
  ];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero Header */}
      <LinearGradient
        colors={['#FAFAFA', '#FFFFFF']}
        style={styles.hero}
      >
        <Text style={styles.title}>Forex Markets</Text>
        <Text style={styles.subtitle}>
          Real-time analysis • 24/7 liquidity • Institutional-grade edge
        </Text>
      </LinearGradient>

      {/* Featured Pair – EURUSD dominates the top */}
      <View style={styles.featuredCard}>
        <View style={styles.shadowContainer}>
          <View style={styles.featuredInner}>
            <View style={styles.featuredHeader}>
              <Text style={styles.featuredPair}>EUR/USD</Text>
              <View style={styles.liveBadge}>
                <View style={styles.liveDot} />
                <Text style={styles.liveText}>LIVE</Text>
              </View>
            </View>
            <Text style={styles.featuredLabel}>The World's Most Traded Pair</Text>
            <View style={{ marginTop: 16 }}>
              <RustForexWidget defaultPair="EURUSD" size="large" />
            </View>
          </View>
        </View>
      </View>

      {/* Major Pairs Grid */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Major Pairs</Text>
        <View style={styles.grid}>
          {majorPairs.map(({ pair, label }) => (
            <View key={pair} style={styles.cardWrapper}>
              <View style={styles.cardShadowContainer}>
                <View style={styles.card}>
                  <View style={styles.cardHeader}>
                    <Text style={styles.pairCode}>{pair}</Text>
                    <Text style={styles.pairLabel}>{label}</Text>
                  </View>
                  <View style={styles.widgetWrapper}>
                    <RustForexWidget defaultPair={pair} size="compact" />
                  </View>
                </View>
              </View>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FCFCFD',
  },
  contentContainer: {
    paddingBottom: 40,
  },
  hero: {
    paddingTop: 60,
    paddingHorizontal: 24,
    paddingBottom: 32,
  },
  title: {
    fontSize: 36,
    fontWeight: '800',
    color: '#000000',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 16,
    color: '#525252',
    marginTop: 8,
    lineHeight: 22,
    fontWeight: '500',
  },
  featuredCard: {
    marginHorizontal: 20,
    marginTop: -20,
    borderRadius: 24,
    overflow: 'visible',
  },
  shadowContainer: {
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 12,
  },
  featuredInner: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  featuredHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  featuredPair: {
    fontSize: 28,
    fontWeight: '800',
    color: '#000000',
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10B981',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFFFFF',
    marginRight: 6,
  },
  liveText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  featuredLabel: {
    fontSize: 15,
    color: '#6B7280',
    marginTop: 6,
    fontWeight: '500',
  },
  section: {
    marginTop: 40,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111111',
    marginBottom: 20,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  cardWrapper: {
    width: (width - 50) / 2,
    marginBottom: 16,
  },
  cardShadowContainer: {
    borderRadius: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 8,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F2F2F2',
    height: 180,
  },
  cardHeader: {
    marginBottom: 12,
  },
  pairCode: {
    fontSize: 18,
    fontWeight: '800',
    color: '#000000',
  },
  pairLabel: {
    fontSize: 12,
    color: '#71717A',
    marginTop: 2,
    fontWeight: '500',
  },
  widgetWrapper: {
    flex: 1,
    justifyContent: 'flex-end',
  },
});

