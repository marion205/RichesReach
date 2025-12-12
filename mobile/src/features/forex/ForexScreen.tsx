import React from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import RustForexWidget from '../../components/rust/RustForexWidget';

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
      {/* Hero Header (Jobs-style: calm, minimal, human) */}
      <LinearGradient colors={['#FFFFFF', '#FAFAFA']} style={styles.hero}>
        <Text style={styles.title}>Forex</Text>
        <Text style={styles.subtitle}>
          One clear read. One smart move. No jargon.
        </Text>
      </LinearGradient>

      {/* Featured Pair – EURUSD */}
      <View style={styles.featuredSection}>
        <View style={styles.featuredCard}>
          <View style={styles.shadowContainer}>
            <View style={styles.featuredInner}>
              <View style={styles.featuredHeader}>
                <View>
                  <Text style={styles.featuredPair}>EUR/USD</Text>
                  <Text style={styles.featuredLabel}>The world's most traded pair</Text>
                </View>

                <View style={styles.liveBadge}>
                  <View style={styles.liveDot} />
                  <Text style={styles.liveText}>LIVE</Text>
                </View>
              </View>

              <View style={{ marginTop: 14 }}>
                <RustForexWidget defaultPair="EURUSD" size="large" />
              </View>
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
                    <Text style={styles.pairCode}>
                      {pair.slice(0, 3)}/{pair.slice(3)}
                    </Text>
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

        <View style={styles.footerNote}>
          <Text style={styles.footerNoteText}>
            Educational insights — not financial advice.
          </Text>
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
    paddingBottom: 28,
  },
  title: {
    fontSize: 38,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: -0.6,
  },
  subtitle: {
    fontSize: 16,
    color: '#52525B',
    marginTop: 8,
    lineHeight: 22,
    fontWeight: '500',
  },

  featuredSection: {
    paddingHorizontal: 20,
    marginTop: 8,
  },
  featuredCard: {
    borderRadius: 24,
    overflow: 'visible',
  },
  shadowContainer: {
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.10,
    shadowRadius: 14,
    elevation: 12,
  },
  featuredInner: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: '#F1F1F4',
  },
  featuredHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  featuredPair: {
    fontSize: 28,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: -0.3,
  },
  featuredLabel: {
    fontSize: 13,
    color: '#71717A',
    marginTop: 4,
    fontWeight: '600',
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10B981',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
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
    fontWeight: '800',
    letterSpacing: 0.6,
  },

  section: {
    marginTop: 34,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#111111',
    marginBottom: 18,
    letterSpacing: -0.2,
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
    shadowRadius: 10,
    elevation: 8,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F2F2F6',
    height: 168,
  },
  cardHeader: {
    marginBottom: 10,
  },
  pairCode: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0B0B0F',
    letterSpacing: -0.2,
  },
  pairLabel: {
    fontSize: 12,
    color: '#71717A',
    marginTop: 2,
    fontWeight: '600',
  },
  widgetWrapper: {
    flex: 1,
    justifyContent: 'flex-end',
  },

  footerNote: {
    marginTop: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  footerNoteText: {
    fontSize: 12,
    color: '#A1A1AA',
    fontWeight: '600',
  },
});
