/**
 * Private Markets — Learn (deal-context education)
 * How to read the score, key terms, and what to do next.
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { COLORS } from '../theme/privateMarketsTheme';
import type { Deal } from '../types/privateMarketsTypes';

type LearnParams = { dealId?: string; deal?: Deal };

const SECTIONS = [
  {
    title: 'How to read the score',
    items: [
      'The AI Deal Score is built from four pillars: unit economics, team, market & traction, and risk.',
      'Higher scores mean the deal ranks better on our methodology—but always check confidence. A 75 with high confidence is more reliable than an 85 with limited data.',
      'Use "What feeds this score" to see the inputs. Use "What would change this score?" to see what’s missing and track your diligence.',
    ],
  },
  {
    title: 'What confidence means',
    items: [
      'High: Full or near-full diligence; score and fit are well supported.',
      'Moderate: Partial diligence; consider requesting more data before deciding.',
      'Limited: Few data points; score is indicative only. Use the diligence checklist to request and track what you need.',
    ],
  },
  {
    title: 'Key terms',
    items: [
      'Diligence: The process of verifying a deal (financials, legal, cap table, etc.). More complete diligence usually means higher confidence.',
      'Portfolio fit: Whether this deal diversifies your holdings or overlaps with what you already have.',
      'Concentration: Keeping no single deal too large relative to your private allocation (e.g. under 10%).',
      'Illiquidity: Private deals often have 5–8+ year holds; no guarantee of early exit.',
    ],
  },
  {
    title: 'What to do next',
    items: [
      'Compare this deal with others using the Compare action so you see strengths and weaknesses side by side.',
      'Use the diligence checklist to request missing items from the issuer/GP and mark them Received and Reviewed as you go.',
      'Read the decision guidance (allocation, concentration, tradeoffs) and only invest via a licensed partner when you’re comfortable.',
    ],
  },
];

export default function PrivateMarketsLearnScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<RouteProp<{ params: LearnParams }, 'params'>>();
  const params = route.params ?? {};
  const deal = params.deal as Deal | undefined;
  const dealName = deal?.name ?? 'this deal';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <Pressable style={({ pressed }) => [styles.backRow, pressed && styles.backRowPressed]} onPress={() => navigation.goBack()}>
        <Feather name="chevron-left" size={24} color={COLORS.primary} />
        <Text style={styles.backLabel}>Back</Text>
      </Pressable>

      <View style={styles.header}>
        <Feather name="book-open" size={32} color={COLORS.accent} />
        <Text style={styles.title}>Learn about {dealName}</Text>
        <Text style={styles.subtitle}>How to read the score, judge confidence, and use the diligence workflow.</Text>
      </View>

      {SECTIONS.map((section, i) => (
        <View key={i} style={styles.section}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          {section.items.map((item, j) => (
            <View key={j} style={styles.bulletRow}>
              <Text style={styles.bullet}>•</Text>
              <Text style={styles.bulletText}>{item}</Text>
            </View>
          ))}
        </View>
      ))}

      <View style={styles.bottomPad} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 40 },
  backRow: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 4, marginBottom: 20 },
  backRowPressed: { opacity: 0.7 },
  backLabel: { fontSize: 16, fontWeight: '600', color: COLORS.primary },
  header: { marginBottom: 28 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.primary, marginTop: 8, lineHeight: 28 },
  subtitle: { fontSize: 15, color: COLORS.textSecondary, marginTop: 8, lineHeight: 22 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.primary, marginBottom: 10 },
  bulletRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 },
  bullet: { fontSize: 14, color: COLORS.accent, marginRight: 8, lineHeight: 20 },
  bulletText: { flex: 1, fontSize: 14, color: COLORS.textSecondary, lineHeight: 20 },
  bottomPad: { height: 40 },
});
