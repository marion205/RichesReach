import React, { useMemo } from 'react';
import { View, Text, Pressable, StyleSheet, FlatList } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import logger from '../../utils/logger';

type HubItem = {
  key: string;
  title: string;
  subtitle?: string;
  icon: keyof typeof Feather.glyphMap;
  to: string;
};

interface InvestHubScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
}

export default function InvestHubScreen({ navigateTo: navigateToProp }: InvestHubScreenProps = {}) {
  const navigation = useNavigation<any>();
  
  // Safe navigateTo - use prop if provided, otherwise use React Navigation
  // This prevents "navigateTo is not a function" errors
  const safeNavigateTo = navigateToProp || ((screen: string, params?: any) => {
    try {
      navigation.navigate(screen as never, params as never);
    } catch (error) {
      logger.warn('Navigation error:', error);
    }
  });

  const items: HubItem[] = useMemo(
    () => [
      { key: 'stocks', title: 'Stocks', subtitle: 'Browse & analyze', icon: 'trending-up', to: 'Stocks' },
      { key: 'crypto', title: 'Crypto', subtitle: 'Track & research', icon: 'zap', to: 'Crypto' },
      { key: 'ai', title: 'AI Portfolio', subtitle: 'Smart recs & rebalance', icon: 'cpu', to: 'AIPortfolio' },
      { key: 'tomorrow', title: 'Tomorrow', subtitle: 'Trade tomorrow\'s markets today', icon: 'calendar', to: 'Tomorrow' },
      { key: 'trade', title: 'Trading', subtitle: 'Live & options', icon: 'activity', to: 'trading' },
      { key: 'portfolio', title: 'Portfolio', subtitle: 'Positions & P/L', icon: 'pie-chart', to: 'Portfolio' },
      { key: 'forex', title: 'Forex', subtitle: '24/7 market coverage', icon: 'globe', to: 'Forex' },
    ],
    []
  );

  return (
    <View style={styles.container}>
      <Text style={styles.h1}>Invest</Text>
      <Text style={styles.caption}>All your money moves in one place</Text>

      <FlatList
        data={items}
        keyExtractor={(it) => it.key}
        contentContainerStyle={styles.list}
        numColumns={2}
        renderItem={({ item }) => (
          <Pressable
            style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
            onPress={() => navigation.navigate(item.to)}
          >
            <Feather name={item.icon} size={22} />
            <Text style={styles.cardTitle}>{item.title}</Text>
            {!!item.subtitle && <Text style={styles.cardSub}>{item.subtitle}</Text>}
          </Pressable>
        )}
      />

      <Pressable
        style={({ pressed }) => [styles.fab, pressed && { opacity: 0.8 }]}
        onPress={() => navigation.navigate('InvestAdvanced')}
      >
        <Feather name="sliders" size={22} color="#fff" />
        <Text style={styles.fabText}>Advanced</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  h1: { fontSize: 28, fontWeight: '700', marginBottom: 4 },
  caption: { opacity: 0.6, marginBottom: 16 },
  list: { gap: 12 },
  card: {
    flex: 1,
    minHeight: 110,
    margin: 6,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
    gap: 8,
    justifyContent: 'center',
  },
  cardPressed: { opacity: 0.7 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSub: { fontSize: 12, opacity: 0.6 },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 24,
    backgroundColor: '#007AFF',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 24,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    elevation: 3,
  },
  fabText: { color: '#fff', fontWeight: '700' },
});


