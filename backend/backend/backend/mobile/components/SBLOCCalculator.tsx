import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  SafeAreaView,
  Dimensions,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface SBLOCCalculatorProps {
  visible: boolean;
  onClose: () => void;
  portfolioValue?: number;
  onApply?: () => void;
}

const SBLOCCalculator: React.FC<SBLOCCalculatorProps> = ({
  visible,
  onClose,
  portfolioValue = 0,
  onApply,
}) => {
  const [portfolioVal, setPortfolioVal] = useState(portfolioValue.toString());
  const [borrowAmount, setBorrowAmount] = useState('');
  const [interestRate, setInterestRate] = useState('7.5');
  const [termMonths, setTermMonths] = useState('12');
  const [monthlyPayment, setMonthlyPayment] = useState(0);
  const [totalInterest, setTotalInterest] = useState(0);
  const [borrowingPower, setBorrowingPower] = useState(0);

  useEffect(() => {
    if (portfolioValue > 0) {
      setPortfolioVal(portfolioValue.toString());
    }
  }, [portfolioValue]);

  useEffect(() => {
    calculateSBLOC();
  }, [portfolioVal, borrowAmount, interestRate, termMonths]);

  const calculateSBLOC = () => {
    const portfolio = parseFloat(portfolioVal) || 0;
    const borrow = parseFloat(borrowAmount) || 0;
    const rate = parseFloat(interestRate) || 0;
    const term = parseInt(termMonths) || 0;

    // Calculate borrowing power (up to 50% of portfolio value)
    const power = portfolio * 0.5;
    setBorrowingPower(power);

    if (borrow > 0 && rate > 0 && term > 0) {
      // Calculate monthly payment (interest-only for SBLOC)
      const monthlyRate = rate / 100 / 12;
      const payment = borrow * monthlyRate;
      const totalInt = payment * term;

      setMonthlyPayment(payment);
      setTotalInterest(totalInt);
    } else {
      setMonthlyPayment(0);
      setTotalInterest(0);
    }
  };

  const handleBorrowAmountChange = (value: string) => {
    const num = parseFloat(value) || 0;
    if (num <= borrowingPower) {
      setBorrowAmount(value);
    } else {
      Alert.alert(
        'Borrowing Limit Exceeded',
        `You can borrow up to $${borrowingPower.toLocaleString()} based on your portfolio value.`
      );
    }
  };

  const setBorrowPercentage = (percentage: number) => {
    const amount = (borrowingPower * percentage) / 100;
    setBorrowAmount(amount.toString());
  };

  const formatCurrency = (amount: number) => {
    return amount.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  };

  const formatPercentage = (rate: number) => {
    return `${rate}%`;
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
          <Text style={styles.title}>SBLOC Calculator</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Hero Section */}
          <View style={styles.hero}>
            <View style={styles.heroIcon}>
              <Icon name="calculator" size={32} color="#F59E0B" />
            </View>
            <Text style={styles.heroTitle}>Calculate Your SBLOC</Text>
            <Text style={styles.heroSubtitle}>
              See how much you can borrow and what it will cost
            </Text>
          </View>

          {/* Portfolio Value Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Portfolio Value</Text>
            <View style={styles.inputContainer}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.input}
                value={portfolioVal}
                onChangeText={setPortfolioVal}
                placeholder="Enter portfolio value"
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
            </View>
            <Text style={styles.inputHint}>
              Total value of your eligible securities
            </Text>
          </View>

          {/* Borrowing Power Display */}
          <View style={styles.powerCard}>
            <View style={styles.powerHeader}>
              <Icon name="trending-up" size={20} color="#10B981" />
              <Text style={styles.powerTitle}>Available Borrowing Power</Text>
            </View>
            <Text style={styles.powerAmount}>
              {formatCurrency(borrowingPower)}
            </Text>
            <Text style={styles.powerSubtext}>
              Up to 50% of your portfolio value
            </Text>
          </View>

          {/* Borrow Amount Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Borrow Amount</Text>
            <View style={styles.inputContainer}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.input}
                value={borrowAmount}
                onChangeText={handleBorrowAmountChange}
                placeholder="Enter amount to borrow"
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
            </View>
            
            {/* Quick Percentage Buttons */}
            <View style={styles.percentageButtons}>
              {[25, 50, 75, 100].map((pct) => (
                <TouchableOpacity
                  key={pct}
                  style={[
                    styles.percentageBtn,
                    parseFloat(borrowAmount) === (borrowingPower * pct) / 100 && styles.percentageBtnActive
                  ]}
                  onPress={() => setBorrowPercentage(pct)}
                >
                  <Text style={[
                    styles.percentageBtnText,
                    parseFloat(borrowAmount) === (borrowingPower * pct) / 100 && styles.percentageBtnTextActive
                  ]}>
                    {pct}%
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Interest Rate Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Interest Rate (Annual)</Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                value={interestRate}
                onChangeText={setInterestRate}
                placeholder="7.5"
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
              <Text style={styles.percentageSymbol}>%</Text>
            </View>
            <Text style={styles.inputHint}>
              Typical SBLOC rates range from 6.5% to 8.5%
            </Text>
          </View>

          {/* Term Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Term (Months)</Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                value={termMonths}
                onChangeText={setTermMonths}
                placeholder="12"
                keyboardType="numeric"
                placeholderTextColor="#8E8E93"
              />
              <Text style={styles.monthsSymbol}>months</Text>
            </View>
            <Text style={styles.inputHint}>
              Interest-only payments during the term
            </Text>
          </View>

          {/* Results */}
          {borrowAmount && parseFloat(borrowAmount) > 0 && (
            <View style={styles.resultsSection}>
              <Text style={styles.resultsTitle}>Your SBLOC Breakdown</Text>
              
              <View style={styles.resultCard}>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Monthly Payment</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(monthlyPayment)}
                  </Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Total Interest</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(totalInterest)}
                  </Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Interest Rate</Text>
                  <Text style={styles.resultValue}>
                    {formatPercentage(parseFloat(interestRate))}
                  </Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Borrow Amount</Text>
                  <Text style={styles.resultValue}>
                    {formatCurrency(parseFloat(borrowAmount))}
                  </Text>
                </View>
              </View>

              {/* Comparison */}
              <View style={styles.comparisonCard}>
                <Text style={styles.comparisonTitle}>vs. Other Options</Text>
                <View style={styles.comparisonRow}>
                  <Text style={styles.comparisonLabel}>SBLOC (Interest Only)</Text>
                  <Text style={styles.comparisonValue}>
                    {formatCurrency(monthlyPayment)}/month
                  </Text>
                </View>
                <View style={styles.comparisonRow}>
                  <Text style={styles.comparisonLabel}>Credit Card (18% APR)</Text>
                  <Text style={styles.comparisonValue}>
                    {formatCurrency((parseFloat(borrowAmount) * 0.18) / 12)}/month
                  </Text>
                </View>
                <View style={styles.comparisonRow}>
                  <Text style={styles.comparisonLabel}>Personal Loan (12% APR)</Text>
                  <Text style={styles.comparisonValue}>
                    {formatCurrency((parseFloat(borrowAmount) * 0.12) / 12)}/month
                  </Text>
                </View>
              </View>
            </View>
          )}

          {/* Important Notes */}
          <View style={styles.notesSection}>
            <Text style={styles.notesTitle}>Important Considerations</Text>
            <View style={styles.notesList}>
              <View style={styles.noteItem}>
                <Icon name="alert-triangle" size={16} color="#F59E0B" />
                <Text style={styles.noteText}>
                  Market volatility can affect your borrowing power
                </Text>
              </View>
              <View style={styles.noteItem}>
                <Icon name="alert-triangle" size={16} color="#F59E0B" />
                <Text style={styles.noteText}>
                  You may need to add collateral if portfolio value drops
                </Text>
              </View>
              <View style={styles.noteItem}>
                <Icon name="alert-triangle" size={16} color="#F59E0B" />
                <Text style={styles.noteText}>
                  Interest rates are variable and can change
                </Text>
              </View>
              <View style={styles.noteItem}>
                <Icon name="info" size={16} color="#3B82F6" />
                <Text style={styles.noteText}>
                  No monthly principal payments required
                </Text>
              </View>
            </View>
          </View>
        </ScrollView>

        {/* Footer Actions */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={onClose}
          >
            <Text style={styles.secondaryButtonText}>Close</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => {
              if (onApply) {
                onApply();
              } else {
                Alert.alert(
                  'SBLOC Application',
                  'This would open the SBLOC application flow with our partner banks.',
                  [{ text: 'OK' }]
                );
              }
            }}
          >
            <Icon name="external-link" size={20} color="#fff" />
            <Text style={styles.primaryButtonText}>Apply Now</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E2E8F0',
  },
  closeButton: {
    padding: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  hero: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  heroIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 16,
    color: '#64748B',
    textAlign: 'center',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#64748B',
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
  },
  percentageSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748B',
    marginLeft: 8,
  },
  monthsSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748B',
    marginLeft: 8,
  },
  inputHint: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 8,
  },
  powerCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  powerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  powerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#059669',
    marginLeft: 8,
  },
  powerAmount: {
    fontSize: 28,
    fontWeight: '700',
    color: '#059669',
    marginBottom: 4,
  },
  powerSubtext: {
    fontSize: 14,
    color: '#047857',
  },
  percentageButtons: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 8,
  },
  percentageBtn: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
  },
  percentageBtnActive: {
    backgroundColor: '#3B82F6',
  },
  percentageBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
  },
  percentageBtnTextActive: {
    color: '#fff',
  },
  resultsSection: {
    marginBottom: 24,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 16,
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  resultLabel: {
    fontSize: 16,
    color: '#64748B',
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
  },
  comparisonCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  comparisonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 12,
  },
  comparisonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  comparisonLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  comparisonValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E293B',
  },
  notesSection: {
    marginBottom: 24,
  },
  notesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 12,
  },
  notesList: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  noteItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  noteText: {
    flex: 1,
    fontSize: 14,
    color: '#64748B',
    marginLeft: 12,
    lineHeight: 20,
  },
  footer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E2E8F0',
    gap: 12,
  },
  secondaryButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748B',
  },
  primaryButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#3B82F6',
    gap: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});

export default SBLOCCalculator;
