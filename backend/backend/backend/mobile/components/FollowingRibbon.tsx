import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Quotes = Record<string, { price?: number; chg?: number }>;

type Props = {
  symbols: string[];
  liveQuotes?: Quotes; // optional
  onPressSymbol?: (symbol: string) => void;
  onManagePress?: () => void;
};

const FollowingRibbon: React.FC<Props> = ({ symbols, liveQuotes = {}, onPressSymbol, onManagePress }) => {
  if (!symbols?.length) return null;

  return (
    <View style={styles.wrap}>
      <View style={styles.header}>
        <Text style={styles.title}>Following</Text>
        <TouchableOpacity onPress={onManagePress} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <View style={styles.manageBtn}>
            <Icon name="settings" size={14} color="#0EA5E9" />
            <Text style={styles.manageTxt}>Manage</Text>
          </View>
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scroller}
      >
        {symbols.map((sym) => {
          const q = liveQuotes[sym] || {};
          const chg = Number.isFinite(q.chg) ? (q.chg as number) : undefined; // % change
          const price = Number.isFinite(q.price) ? (q.price as number) : undefined;

          const isUp = (chg ?? 0) >= 0;
          const pctStr = chg == null ? '—' : `${chg.toFixed(2)}%`;
          const arrow = chg == null ? 'minus' : isUp ? 'trending-up' : 'trending-down';

          return (
            <TouchableOpacity
              key={sym}
              onPress={() => onPressSymbol?.(sym)}
              activeOpacity={0.85}
            >
              <View style={styles.chip}>
                <View style={styles.left}>
                  <Text style={styles.sym} numberOfLines={1}>{sym}</Text>
                  <Text style={styles.price} numberOfLines={1}>
                    {price == null ? '—' : price.toFixed(2)}
                  </Text>
                </View>

                <View style={styles.rightSection}>
                  <View style={[styles.badge, isUp ? styles.badgeUp : styles.badgeDown]}>
                    <Icon
                      name={arrow as any}
                      size={12}
                      color={isUp ? '#065F46' : '#7F1D1D'}
                      style={{ marginRight: 4 }}
                    />
                    <Text style={[styles.badgeTxt, isUp ? styles.badgeTxtUp : styles.badgeTxtDown]}>
                      {pctStr}
                    </Text>
                  </View>

                  <View style={styles.followPill}>
                    <Icon name="check" size={12} color="#10B981" />
                    <Text style={styles.followTxt}>Following</Text>
                  </View>
                </View>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  wrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  title: { fontSize: 14, fontWeight: '700', color: '#334155' },
  manageBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F9FF',
    borderWidth: 1,
    borderColor: '#BAE6FD',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  manageTxt: { marginLeft: 6, fontSize: 12, fontWeight: '700', color: '#0EA5E9' },

  scroller: { paddingRight: 8 },

  chip: {
    width: 160,
    height: 70,
    marginRight: 10,
    borderRadius: 14,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 10,
    flexDirection: 'row',
    alignItems: 'flex-start',

    // subtle elevation
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  left: { flex: 1, justifyContent: 'center' },
  rightSection: {
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: '100%',
  },
  sym: { fontSize: 16, fontWeight: '800', color: '#111827', letterSpacing: 0.3 },
  price: { marginTop: 2, fontSize: 12, color: '#6B7280' },

  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 1,
  },
  badgeUp: { backgroundColor: '#ECFDF5', borderColor: '#D1FAE5' },
  badgeDown: { backgroundColor: '#FEF2F2', borderColor: '#FECACA' },
  badgeTxt: { fontSize: 12, fontWeight: '700' },
  badgeTxtUp: { color: '#065F46' },
  badgeTxtDown: { color: '#7F1D1D' },

  followPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 999,
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    marginTop: 4,
  },
  followTxt: { marginLeft: 4, fontSize: 11, fontWeight: '700', color: '#047857' },
});

export default FollowingRibbon;
