import React from 'react';
import { View, Text, StyleSheet, ScrollView, SafeAreaView, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Props = {
  navigateTo?: (screen: string) => void;
};

export default function LearnSblocScreen({ navigateTo }: Props) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo?.('profile')} style={styles.backBtn}>
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>How SBLOC Works</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.h1}>Securities-Based Line of Credit</Text>
        <Text style={styles.p}>
          A Securities-Based Line of Credit lets you borrow against your eligible portfolio
          without selling your investments. This can provide liquidity while potentially
          maintaining tax efficiency and keeping your investments growing.
        </Text>

        <View style={styles.callout}>
          <Text style={styles.calloutTitle}>Quick Facts</Text>
          <Text style={styles.li}>• No sale of securities → potential tax efficiency</Text>
          <Text style={styles.li}>• Collateral: eligible equity/ETF positions</Text>
          <Text style={styles.li}>• Risk: collateral value can drop → margin calls</Text>
          <Text style={styles.li}>• Interest rates vary with LTV and market conditions</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How It Works</Text>
          <Text style={styles.p}>
            1. Your eligible securities serve as collateral for the line of credit
          </Text>
          <Text style={styles.p}>
            2. You can borrow up to a percentage of your portfolio value (typically 50%)
          </Text>
          <Text style={styles.p}>
            3. Interest is charged only on the amount you actually borrow
          </Text>
          <Text style={styles.p}>
            4. You can pay down or increase your borrowing as needed
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Benefits</Text>
          <Text style={styles.p}>• Access to liquidity without selling investments</Text>
          <Text style={styles.p}>• Potentially lower rates than credit cards</Text>
          <Text style={styles.p}>• Interest may be tax deductible (consult your tax advisor)</Text>
          <Text style={styles.p}>• Flexible repayment terms</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risks</Text>
          <Text style={styles.p}>• Market volatility can affect borrowing power</Text>
          <Text style={styles.p}>• Margin calls if portfolio value drops significantly</Text>
          <Text style={styles.p}>• Variable interest rates can increase</Text>
          <Text style={styles.p}>• Not FDIC insured</Text>
        </View>

        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>
            This information is for educational purposes only and does not constitute financial advice. 
            Please consult with a qualified financial advisor before making any borrowing decisions.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F7FB' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  content: { padding: 20 },
  h1: { fontSize: 22, fontWeight: '800', color: '#111827', marginBottom: 8 },
  p: { color: '#6B7280', lineHeight: 20, marginBottom: 14 },
  callout: { backgroundColor: '#F8FAFC', borderRadius: 12, padding: 14, marginBottom: 20 },
  calloutTitle: { fontWeight: '800', marginBottom: 6, color: '#111827' },
  li: { color: '#374151', marginTop: 4 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#111827', marginBottom: 12 },
  disclaimer: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  disclaimerText: {
    fontSize: 12,
    color: '#92400E',
    lineHeight: 16,
    fontStyle: 'italic',
  },
});
