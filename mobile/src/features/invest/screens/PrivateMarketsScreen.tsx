/**
 * Private Markets — List (Deal Room)
 * Discover → Understand → Compare → Decide → (optionally) partner for execution.
 * V1: Deal cards with AI Deal Score; tap to detail. Saved tab shows watchlist.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { COLORS, CATEGORY_STRIPE } from '../theme/privateMarketsTheme';
import { getPrivateMarketsService } from '../services/privateMarketsService';
import type { Deal } from '../types/privateMarketsTypes';

const PROMISE = 'Understand the opportunity, the risk, and the fit before you invest.';

type Tab = 'deals' | 'saved';

export default function PrivateMarketsScreen() {
  const navigation = useNavigation<any>();
  const [tab, setTab] = useState<Tab>('deals');
  const [allDeals, setAllDeals] = useState<Deal[]>([]);
  const [savedIds, setSavedIds] = useState<string[]>([]);

  useEffect(() => {
    getPrivateMarketsService()
      .getDeals()
      .then(setAllDeals)
      .catch(() => {});
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      getPrivateMarketsService()
        .getSavedDealIds()
        .then(setSavedIds)
        .catch(() => {});
    }, [])
  );

  const deals = tab === 'saved' ? allDeals.filter((d) => savedIds.includes(d.id)) : allDeals;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Private Markets</Text>
        <Text style={styles.subtitle}>Get smart about private markets before you invest.</Text>
      </View>

      <View style={styles.promiseStrip}>
        <Feather name="info" size={18} color={COLORS.primary} />
        <Text style={styles.promiseText}>{PROMISE}</Text>
      </View>

      <View style={styles.tabRow}>
        <Pressable style={styles.tabTouch} onPress={() => setTab('deals')}>
          <View style={[styles.tab, tab === 'deals' && styles.tabActive]}>
            <Text style={[styles.tabInactiveText, tab === 'deals' && styles.tabActiveText]}>Deal Room</Text>
          </View>
        </Pressable>
        <Pressable style={styles.tabTouch} onPress={() => setTab('saved')}>
          <View style={[styles.tab, tab === 'saved' && styles.tabActive]}>
            <Text style={[styles.tabInactiveText, tab === 'saved' && styles.tabActiveText]}>Saved</Text>
          </View>
        </Pressable>
      </View>

      <Text style={styles.sectionLabel}>{tab === 'saved' ? 'Saved opportunities' : 'Opportunities'}</Text>
      {tab === 'saved' && deals.length === 0 ? (
        <View style={styles.emptyState}>
          <Feather name="bookmark" size={40} color="#94A3B8" />
          <Text style={styles.emptyTitle}>No saved deals yet</Text>
          <Text style={styles.emptySub}>Save deals from their detail screen to see them here.</Text>
        </View>
      ) : (
        deals.map((deal) => {
          const stripeColor = CATEGORY_STRIPE[deal.category as keyof typeof CATEGORY_STRIPE] ?? CATEGORY_STRIPE.default;
          return (
            <Pressable
              key={deal.id}
              style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
              onPress={() => navigation.navigate('PrivateMarketsDealDetail', { dealId: deal.id, deal })}
            >
              <View style={[styles.cardStripe, { backgroundColor: stripeColor }]} />
              <View style={styles.cardInner}>
                <View style={styles.cardTop}>
                  <Text style={styles.cardName}>{deal.name}</Text>
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreValue}>{deal.score}</Text>
                    <Text style={styles.scoreLabel}>Score</Text>
                  </View>
                </View>
                <Text style={styles.cardTagline}>{deal.tagline}</Text>
                <View style={styles.cardFooter}>
                  <Text style={styles.cardCta}>See score breakdown & fit →</Text>
                </View>
              </View>
            </Pressable>
          );
        })
      )}

      <View style={styles.bottomPad} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 40 },
  header: { marginBottom: 24 },
  title: { fontSize: 28, fontWeight: 'bold', color: COLORS.primary, letterSpacing: -0.3 },
  subtitle: { fontSize: 15, color: COLORS.textSecondary, marginTop: 6, lineHeight: 22 },
  promiseStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: COLORS.promiseBg,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 16,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  promiseText: { flex: 1, fontSize: 14, color: COLORS.textSecondary, lineHeight: 20 },
  tabRow: { flexDirection: 'row', marginBottom: 20, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  tabTouch: {},
  tab: { paddingVertical: 12, paddingHorizontal: 20 },
  tabActive: { borderBottomWidth: 3, borderBottomColor: COLORS.primary },
  tabActiveText: { fontSize: 16, fontWeight: '700', color: COLORS.primary },
  tabInactiveText: { fontSize: 16, fontWeight: '600', color: '#94A3B8' },
  emptyState: { alignItems: 'center', paddingVertical: 48, paddingHorizontal: 24 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginTop: 12 },
  emptySub: { fontSize: 14, color: COLORS.textSecondary, marginTop: 6, textAlign: 'center' },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  card: {
    backgroundColor: COLORS.bgCard,
    borderRadius: 20,
    padding: 0,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  cardPressed: {
    opacity: 0.92,
    transform: [{ scale: 0.98 }],
  },
  cardStripe: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    borderTopLeftRadius: 20,
    borderBottomLeftRadius: 20,
  },
  cardInner: { padding: 18, paddingLeft: 22 },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardName: {
    fontSize: 17,
    fontWeight: '700',
    color: COLORS.primary,
    flex: 1,
    letterSpacing: -0.2,
  },
  scoreBadge: {
    backgroundColor: COLORS.scoreBg,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    alignItems: 'center',
    minWidth: 62,
  },
  scoreValue: { fontSize: 20, fontWeight: '800', color: '#FFF' },
  scoreLabel: { fontSize: 11, color: 'rgba(255,255,255,0.75)', marginTop: 1 },
  cardTagline: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFooter: {},
  cardCta: {
    fontSize: 14,
    color: COLORS.accent,
    fontWeight: '600',
  },
  bottomPad: { height: 60 },
});
