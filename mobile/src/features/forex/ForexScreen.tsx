import React, { useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import RustForexWidget from '../../components/rust/RustForexWidget';

const { width } = Dimensions.get('window');
const COLUMN_WIDTH = (width - 56) / 2;

interface Pair {
  pair: string;
  label: string;
  flag: string;
}

const PAIRS: Pair[] = [
  { pair: 'EURUSD', label: 'Euro / US Dollar', flag: '🇪🇺🇺🇸' },
  { pair: 'GBPUSD', label: 'British Pound / US Dollar', flag: '🇬🇧🇺🇸' },
  { pair: 'USDJPY', label: 'US Dollar / Japanese Yen', flag: '🇺🇸🇯🇵' },
  { pair: 'AUDUSD', label: 'Australian Dollar / US Dollar', flag: '🇦🇺🇺🇸' },
  { pair: 'USDCAD', label: 'US Dollar / Canadian Dollar', flag: '🇺🇸🇨🇦' },
  { pair: 'USDCHF', label: 'US Dollar / Swiss Franc', flag: '🇺🇸🇨🇭' },
];

// --- Sub-components ---

const GridCard = ({ pair, label, flag }: Pair) => {
  const formattedPair = `${pair.slice(0, 3)}/${pair.slice(3)}`;
  return (
    <View style={styles.gridCard}>
      <View style={styles.gridCardTop}>
        <Text style={styles.gridFlag}>{flag}</Text>
        <View style={styles.gridLiveDot} />
      </View>
      <Text style={styles.gridPairText}>{formattedPair}</Text>
      <Text style={styles.gridLabelText} numberOfLines={1}>{label}</Text>
      <View style={styles.gridWidget}>
        <RustForexWidget defaultPair={pair} size="compact" />
      </View>
    </View>
  );
};

// --- Main Screen ---

export default function ForexScreen() {
  const gridPairs = useMemo(() => PAIRS, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero */}
      <LinearGradient
        colors={['#0B0B0F', '#1A1A2E', '#16213E']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.hero}
      >
        <View style={styles.heroContent}>
          <View style={styles.heroEyebrow}>
            <View style={styles.liveChip}>
              <View style={styles.livePulse} />
              <Text style={styles.liveChipText}>LIVE</Text>
            </View>
            <Text style={styles.heroEyebrowText}>Global Currency Markets</Text>
          </View>
          <Text style={styles.heroTitle}>Forex</Text>
          <Text style={styles.heroSubtitle}>One clear read. One smart move.</Text>
        </View>

        {/* Decorative blur orbs */}
        <View style={styles.orb1} />
        <View style={styles.orb2} />
      </LinearGradient>

      <View style={styles.body}>
        {/* Featured EUR/USD */}
        <View style={styles.featuredCard}>
          <LinearGradient
            colors={['#00cc9910', '#6366F110']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.featuredGradientStrip}
          />
          <View style={styles.featuredHeader}>
            <View style={styles.featuredHeaderLeft}>
              <Text style={styles.featuredFlag}>🇪🇺🇺🇸</Text>
              <View>
                <Text style={styles.featuredPairText}>EUR/USD</Text>
                <Text style={styles.featuredLabelText}>World's most traded pair</Text>
              </View>
            </View>
            <View style={styles.featuredBadge}>
              <View style={styles.featuredBadgeDot} />
              <Text style={styles.featuredBadgeText}>LIVE</Text>
            </View>
          </View>
          <View style={styles.featuredWidget}>
            <RustForexWidget defaultPair="EURUSD" size="large" />
          </View>
        </View>

        {/* Major Pairs Grid */}
        <View style={styles.gridSection}>
          <View style={styles.sectionRow}>
            <Text style={styles.sectionTitle}>Major Pairs</Text>
            <Text style={styles.sectionCount}>{gridPairs.length} pairs</Text>
          </View>
          <View style={styles.grid}>
            {gridPairs.map((item) => (
              <GridCard key={item.pair} {...item} />
            ))}
          </View>
        </View>

        <View style={styles.footer}>
          <View style={styles.footerDivider} />
          <Text style={styles.footerText}>Educational insights — not financial advice.</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FB',
  },
  scrollContent: {
    paddingBottom: 80,
  },

  // Hero
  hero: {
    paddingTop: 64,
    paddingBottom: 40,
    paddingHorizontal: 24,
    overflow: 'hidden',
    position: 'relative',
  },
  heroContent: {
    zIndex: 2,
  },
  heroEyebrow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  heroEyebrowText: {
    fontSize: 13,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.55)',
    letterSpacing: 0.3,
  },
  heroTitle: {
    fontSize: 46,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -1.5,
    lineHeight: 50,
  },
  heroSubtitle: {
    marginTop: 6,
    fontSize: 16,
    color: 'rgba(255,255,255,0.5)',
    fontWeight: '500',
  },

  // Live chip in hero
  liveChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,204,153,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(0,204,153,0.3)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    gap: 5,
  },
  livePulse: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00cc99',
  },
  liveChipText: {
    color: '#00cc99',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },

  // Decorative orbs
  orb1: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(99,102,241,0.15)',
    right: -60,
    top: -40,
    zIndex: 1,
  },
  orb2: {
    position: 'absolute',
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: 'rgba(0,204,153,0.1)',
    right: 40,
    bottom: -30,
    zIndex: 1,
  },

  body: {
    paddingHorizontal: 20,
    paddingTop: 24,
  },

  // Featured Card
  featuredCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 4,
    marginBottom: 28,
  },
  featuredGradientStrip: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 80,
  },
  featuredHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 12,
  },
  featuredHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  featuredFlag: {
    fontSize: 28,
  },
  featuredPairText: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: -0.5,
  },
  featuredLabelText: {
    fontSize: 13,
    color: '#8E8E93',
    marginTop: 2,
    fontWeight: '500',
  },
  featuredBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#00cc9918',
    borderWidth: 1,
    borderColor: '#00cc9930',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  featuredBadgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00cc99',
  },
  featuredBadgeText: {
    color: '#00cc99',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  featuredWidget: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },

  // Grid Section
  gridSection: {
    marginTop: 4,
  },
  sectionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0B0B0F',
    letterSpacing: -0.3,
  },
  sectionCount: {
    fontSize: 13,
    fontWeight: '600',
    color: '#AEAEB2',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 14,
  },

  // Grid Card
  gridCard: {
    width: COLUMN_WIDTH,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#EBEBF0',
    padding: 16,
    minHeight: 168,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  gridCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  gridFlag: {
    fontSize: 20,
  },
  gridLiveDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#00cc99',
  },
  gridPairText: {
    fontSize: 17,
    fontWeight: '800',
    color: '#0B0B0F',
    letterSpacing: -0.2,
  },
  gridLabelText: {
    fontSize: 11,
    color: '#AEAEB2',
    marginTop: 2,
    fontWeight: '500',
    marginBottom: 10,
  },
  gridWidget: {
    flex: 1,
    justifyContent: 'flex-end',
  },

  // Footer
  footer: {
    marginTop: 40,
    alignItems: 'center',
    gap: 12,
  },
  footerDivider: {
    width: 40,
    height: 2,
    borderRadius: 1,
    backgroundColor: '#EBEBF0',
  },
  footerText: {
    fontSize: 12,
    color: '#AEAEB2',
    fontWeight: '500',
  },
});
