import React, { useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions, Pressable } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import RustForexWidget from '../../components/rust/RustForexWidget';

const { width } = Dimensions.get('window');
const COLUMN_WIDTH = (width - 56) / 2; // Precise calculation for 2-column grid

interface Pair {
  pair: string;
  label: string;
}

// --- Sub-components ---

const SectionHeader = ({ title, subtitle }: { title: string; subtitle?: string }) => (
  <View style={styles.headerContainer}>
    <Text style={styles.title}>{title}</Text>
    {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
  </View>
);

const PairCard = ({ pair, label, size = 'compact' }: { pair: string; label: string; size?: 'compact' | 'large' }) => {
  const isLarge = size === 'large';
  const formattedPair = `${pair.slice(0, 3)}/${pair.slice(3)}`;

  return (
    <View style={[styles.cardBase, isLarge ? styles.featuredCard : styles.gridCard]}>
      <View style={styles.cardContent}>
        <View style={styles.cardHeader}>
          <View>
            <Text style={isLarge ? styles.featuredPairText : styles.pairText}>{formattedPair}</Text>
            <Text style={styles.labelText} numberOfLines={1}>{label}</Text>
          </View>
          
          {isLarge && (
            <View style={styles.liveBadge}>
              <View style={styles.liveDot} />
              <Text style={styles.liveText}>LIVE</Text>
            </View>
          )}
        </View>

        <View style={isLarge ? styles.largeWidget : styles.compactWidget}>
          <RustForexWidget defaultPair={pair} size={size} />
        </View>
      </View>
    </View>
  );
};

// --- Main Screen ---

export default function ForexScreen() {
  const majorPairs: Pair[] = useMemo(() => [
    { pair: 'EURUSD', label: 'Euro / US Dollar' },
    { pair: 'GBPUSD', label: 'British Pound / US Dollar' },
    { pair: 'USDJPY', label: 'US Dollar / Japanese Yen' },
    { pair: 'AUDUSD', label: 'Australian Dollar / US Dollar' },
    { pair: 'USDCAD', label: 'US Dollar / Canadian Dollar' },
    { pair: 'USDCHF', label: 'US Dollar / Swiss Franc' },
  ], []);

  return (
    <ScrollView 
      style={styles.container} 
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      <LinearGradient colors={['#FFFFFF', '#F9FAFB']} style={styles.hero}>
        <SectionHeader 
          title="Forex" 
          subtitle="One clear read. One smart move. No jargon." 
        />
      </LinearGradient>

      <View style={styles.body}>
        {/* Featured Section */}
        <PairCard 
          pair="EURUSD" 
          label="The world's most traded pair" 
          size="large" 
        />

        {/* Grid Section */}
        <View style={styles.gridSection}>
          <Text style={styles.sectionTitle}>Major Pairs</Text>
          <View style={styles.grid}>
            {majorPairs.map((item) => (
              <PairCard key={item.pair} {...item} />
            ))}
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Educational insights — not financial advice.</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    paddingBottom: 60,
  },
  hero: {
    paddingTop: 64,
    paddingBottom: 24,
    paddingHorizontal: 24,
  },
  body: {
    paddingHorizontal: 20,
  },
  headerContainer: {
    marginBottom: 8,
  },
  title: {
    fontSize: 40,
    fontWeight: '800',
    color: '#121217',
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: 17,
    color: '#636366',
    marginTop: 6,
    lineHeight: 24,
    fontWeight: '400',
  },
  
  // Card Styling
  cardBase: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#F2F2F7',
    // Soft Shadow
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 12,
    elevation: 3,
  },
  featuredCard: {
    padding: 20,
    marginBottom: 32,
  },
  gridCard: {
    width: COLUMN_WIDTH,
    padding: 16,
    height: 160,
  },
  cardContent: {
    flex: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  
  // Typography
  featuredPairText: {
    fontSize: 28,
    fontWeight: '800',
    color: '#1C1C1E',
    letterSpacing: -0.5,
  },
  pairText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  labelText: {
    fontSize: 13,
    color: '#8E8E93',
    marginTop: 2,
    fontWeight: '500',
  },

  // Widgets
  largeWidget: {
    marginTop: 10,
    minHeight: 80,
  },
  compactWidget: {
    flex: 1,
    justifyContent: 'flex-end',
  },

  // Grid
  gridSection: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
    letterSpacing: -0.3,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16, // Modern layout
  },

  // Badges
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#FFF',
    marginRight: 5,
  },
  liveText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: '900',
  },

  footer: {
    marginTop: 40,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 13,
    color: '#AEAEB2',
    fontWeight: '500',
  },
});
