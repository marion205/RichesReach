import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Modal,
  ActivityIndicator,
  Dimensions,
  SafeAreaView,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import SBLOCCalculator from '../components/SBLOCCalculator';
import SblocFundingCard from '../components/SblocFundingCard';
import SblocCalculatorModal from '../components/SblocCalculatorModal';
import { GET_SBLOC_OFFER } from '../graphql/sboclGql';

const { width } = Dimensions.get('window');

// Utils
const fmtMoney = (n?: number) =>
  typeof n === 'number' ? n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleDateString() : '');

// Mini components
const Chip = ({ label, tone = 'neutral', icon }: { label: string; tone?: 'neutral'|'success'|'warning'|'danger'|'info'; icon?: string }) => {
  const map = {
    neutral: { bg:'#EEF2F7', fg:'#445063' },
    success: { bg:'#E8F8EF', fg:'#1F9254' },
    warning: { bg:'#FFF5E5', fg:'#A45B00' },
    danger:  { bg:'#FDECEC', fg:'#C0352B' },
    info:    { bg:'#E8F2FF', fg:'#2457D6' },
  } as const;
  const { bg, fg } = map[tone];
  return (
    <View style={[styles.chip, { backgroundColor: bg }]}>
      {icon ? <Icon name={icon as any} size={12} color={fg} style={{ marginRight:6 }} /> : null}
      <Text style={[styles.chipText, { color: fg }]} numberOfLines={1}>{label}</Text>
    </View>
  );
};

const BankAvatar = ({ name }: { name: string }) => {
  const initials = name?.split(' ').map(s=>s[0]).slice(0,2).join('').toUpperCase() || 'BK';
  return (
    <View style={styles.bankAvatar}>
      <Text style={styles.bankAvatarText}>{initials}</Text>
    </View>
  );
};

const SectionHeader = ({ title, right }: { title: string; right?: React.ReactNode }) => (
  <View style={styles.sectionHeader}>
    <Text style={styles.sectionTitle}>{title}</Text>
    {right}
  </View>
);

// GraphQL Queries
const GET_BANK_ACCOUNTS = gql`
  query GetBankAccounts {
    bankAccounts {
      id
      bankName
      accountType
      lastFour
      isVerified
      isPrimary
      linkedAt
    }
  }
`;

const GET_FUNDING_HISTORY = gql`
  query GetFundingHistory {
    fundingHistory {
      id
      amount
      status
      bankAccountId
      initiatedAt
      completedAt
    }
  }
`;

// GraphQL Mutations
const LINK_BANK_ACCOUNT = gql`
  mutation LinkBankAccount($bankName: String!, $accountNumber: String!, $routingNumber: String!) {
    linkBankAccount(bankName: $bankName, accountNumber: $accountNumber, routingNumber: $routingNumber) {
      success
      message
      bankAccount {
        id
        bankName
        accountType
        status
      }
    }
  }
`;

const INITIATE_FUNDING = gql`
  mutation InitiateFunding($amount: Float!, $bankAccountId: String!) {
    initiateFunding(amount: $amount, bankAccountId: $bankAccountId) {
      success
      message
      funding {
        id
        amount
        status
        estimatedCompletion
      }
    }
  }
`;

const BankAccountScreen = ({ navigateTo }: { navigateTo?: (screen: string) => void }) => {
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [showFundingModal, setShowFundingModal] = useState(false);
  const [showSBLOCModal, setShowSBLOCModal] = useState(false);
  const [showSblocCalculator, setShowSblocCalculator] = useState(false);
  const [selectedBankId, setSelectedBankId] = useState('');
  const [fundingAmount, setFundingAmount] = useState('');

  // Form data for linking bank account
  const [bankName, setBankName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [routingNumber, setRoutingNumber] = useState('');

  // Queries
  const { data: bankData, loading: bankLoading, refetch: refetchBanks } = useQuery(
    GET_BANK_ACCOUNTS,
    { errorPolicy: 'all' }
  );

  const { data: fundingData, loading: fundingLoading } = useQuery(
    GET_FUNDING_HISTORY,
    { errorPolicy: 'all' }
  );

  const { data: sblocData } = useQuery(GET_SBLOC_OFFER, { errorPolicy: 'all' });

  // Mutations
  const [linkBankAccount, { loading: linkingBank }] = useMutation(LINK_BANK_ACCOUNT, {
    onCompleted: (data) => {
      if (data.linkBankAccount.success) {
        Alert.alert('Success', 'Bank account linked successfully!');
        setShowLinkModal(false);
        setBankName('');
        setAccountNumber('');
        setRoutingNumber('');
        refetchBanks();
      } else {
        Alert.alert('Error', data.linkBankAccount.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const [initiateFunding, { loading: fundingInProgress }] = useMutation(INITIATE_FUNDING, {
    onCompleted: (data) => {
      if (data.initiateFunding.success) {
        Alert.alert('Success', `Funding of $${fundingAmount} initiated successfully!`);
        setShowFundingModal(false);
        setFundingAmount('');
        setSelectedBankId('');
      } else {
        Alert.alert('Error', data.initiateFunding.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const handleLinkBank = () => {
    if (!bankName || !accountNumber || !routingNumber) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    linkBankAccount({
      variables: {
        bankName,
        accountNumber,
        routingNumber
      }
    });
  };

  const handleInitiateFunding = () => {
    if (!selectedBankId || !fundingAmount) {
      Alert.alert('Error', 'Please select a bank account and enter amount');
      return;
    }
    const amount = parseFloat(fundingAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }
    initiateFunding({
      variables: {
        amount,
        bankAccountId: selectedBankId
      }
    });
  };

  const renderBankAccount = (account: any) => {
    const accent = account.isPrimary ? '#1D4ED8' : account.isVerified ? '#16A34A' : '#9CA3AF';
    return (
      <View key={account.id} style={styles.bankCard}>
        <View style={[styles.leftAccent, { backgroundColor: accent }]} />
        <View style={{ flex:1 }}>
          <View style={styles.bankHeader}>
            <BankAvatar name={account.bankName} />
            <View style={styles.bankInfo}>
              <Text style={styles.bankName}>{account.bankName}</Text>
              <Text style={styles.accountType}>
                {account.accountType.charAt(0).toUpperCase() + account.accountType.slice(1)} •••• {account.lastFour}
              </Text>
            </View>

            <Chip
              label={account.isVerified ? 'Verified' : 'Pending'}
              tone={account.isVerified ? 'success' : 'warning'}
              icon={account.isVerified ? 'check-circle' : 'clock'}
            />
          </View>

          <View style={styles.bankFooter}>
            <Text style={styles.meta}>Linked {fmtDate(account.linkedAt)}</Text>
            {account.isPrimary ? <Chip label="Primary" tone="info" icon="star" /> : null}
          </View>
        </View>
      </View>
    );
  };

  const renderFundingHistory = (f: any) => {
    const tone =
      f.status === 'completed' ? 'success' :
      f.status === 'pending'   ? 'warning' :
      f.status === 'failed'    ? 'danger'  : 'neutral';

    return (
      <View key={f.id} style={styles.fundingRow}>
        <View style={styles.fundingLeft}>
          <View style={[styles.dot, tone==='success' && { backgroundColor:'#16A34A' },
                             tone==='warning' && { backgroundColor:'#F59E0B' },
                             tone==='danger'  && { backgroundColor:'#EF4444' }]} />
          <View style={{ marginLeft:10 }}>
            <Text style={styles.fundingAmount}>${fmtMoney(f.amount)}</Text>
            <Text style={styles.meta}>{fmtDate(f.initiatedAt)}</Text>
          </View>
        </View>
        <Chip
          label={String(f.status).toUpperCase()}
          tone={tone as any}
          icon={tone==='success' ? 'check' : tone==='warning' ? 'clock' : tone==='danger' ? 'x' : undefined}
        />
      </View>
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#34C759';
      case 'pending': return '#FF9500';
      case 'failed': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo?.('profile')} style={styles.backButton}>
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Bank Accounts</Text>
        <TouchableOpacity onPress={() => setShowLinkModal(true)} style={styles.addButton}>
          <Icon name="plus" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Linked Accounts */}
        <View style={styles.section}>
          <SectionHeader
            title="Linked Accounts"
            right={
              <View style={styles.actionRow}>
                <TouchableOpacity style={styles.ghostBtn} onPress={() => setShowLinkModal(true)}>
                  <Icon name="credit-card" size={16} color="#2457D6" />
                  <Text style={styles.ghostBtnText}>Link Bank</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ghostBtn} onPress={() => setShowFundingModal(true)}>
                  <Icon name="plus-circle" size={16} color="#2457D6" />
                  <Text style={styles.ghostBtnText}>Add Funds</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ghostBtn} onPress={() => setShowSBLOCModal(true)}>
                  <Icon name="trending-up" size={16} color="#F59E0B" />
                  <Text style={[styles.ghostBtnText, { color: '#F59E0B' }]}>SBLOC</Text>
                </TouchableOpacity>
              </View>
            }
          />

          {bankLoading ? (
            <View style={styles.skeletonBlock}>
              {[...Array(2)].map((_,i)=>(
                <View key={i} style={styles.bankCard}>
                  <View style={[styles.leftAccent, { backgroundColor:'#E5E7EB' }]} />
                  <View style={{ flex:1, paddingVertical:4 }}>
                    <View style={styles.skelLineWide} />
                    <View style={styles.skelLine} />
                    <View style={styles.skelLineShort} />
                  </View>
                </View>
              ))}
            </View>
          ) : bankData?.bankAccounts?.length ? (
            bankData.bankAccounts.map((account: any) => (
              <View key={account.id}>
                {renderBankAccount(account)}
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="credit-card" size={48} color="#C7C7CC" />
              <Text style={styles.emptyTitle}>No Bank Accounts</Text>
              <Text style={styles.emptySubtitle}>Link a bank to start funding your account.</Text>
              <TouchableOpacity style={styles.primaryBtn} onPress={() => setShowLinkModal(true)}>
                <Text style={styles.primaryBtnText}>Link Bank</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* SBLOC Funding Option */}
        {(() => {
          const ltv = sblocData?.sblocOffer?.ltv ?? 0.5;
          const apr = sblocData?.sblocOffer?.apr ?? 0.085;
          const eligibleEquity = sblocData?.sblocOffer?.eligibleEquity ?? 50000; // Mock equity
          const maxBorrow = Math.floor(eligibleEquity * ltv);
          
          return (
            <View style={styles.section}>
              <SectionHeader title="Quick Funding" />
              <SblocFundingCard
                maxBorrow={maxBorrow}
                aprPct={apr * 100}
                onPress={() => setShowSblocCalculator(true)}
              />
            </View>
          );
        })()}

        {/* Funding */}
        <View style={styles.section}>
          <SectionHeader title="Recent Funding" />
          {fundingLoading ? (
            <View style={styles.skeletonBlock}>
              {[...Array(3)].map((_,i)=>(
                <View key={i} style={styles.fundingRow}>
                  <View style={[styles.dot, { backgroundColor:'#E5E7EB' }]} />
                  <View style={{ flex:1, marginLeft:10 }}>
                    <View style={styles.skelLineWide} />
                    <View style={styles.skelLineShort} />
                  </View>
                  <View style={[styles.chip, { backgroundColor:'#EEF2F7', width:88 }]} />
                </View>
              ))}
            </View>
          ) : fundingData?.fundingHistory?.length ? (
            fundingData.fundingHistory.slice(0, 5).map((funding: any) => (
              <View key={funding.id}>
                {renderFundingHistory(funding)}
              </View>
            ))
          ) : (
            <View style={styles.emptyRow}>
              <Icon name="activity" size={18} color="#9CA3AF" />
              <Text style={styles.meta}>No funding yet</Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Link Bank Account Modal */}
      <Modal visible={showLinkModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowLinkModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Link Bank Account</Text>
            <TouchableOpacity onPress={handleLinkBank} disabled={linkingBank}>
              <Text style={[styles.saveButton, linkingBank && styles.disabledButton]}>
                {linkingBank ? 'Linking...' : 'Link'}
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Bank Name</Text>
              <TextInput
                style={styles.input}
                value={bankName}
                onChangeText={setBankName}
                placeholder="e.g., Chase Bank"
                autoCapitalize="words"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Account Number</Text>
              <TextInput
                style={styles.input}
                value={accountNumber}
                onChangeText={setAccountNumber}
                placeholder="Enter account number"
                keyboardType="numeric"
                secureTextEntry
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Routing Number</Text>
              <TextInput
                style={styles.input}
                value={routingNumber}
                onChangeText={setRoutingNumber}
                placeholder="Enter routing number"
                keyboardType="numeric"
              />
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Funding Modal */}
      <Modal visible={showFundingModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowFundingModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Add Funds</Text>
            <TouchableOpacity onPress={handleInitiateFunding} disabled={fundingInProgress}>
              <Text style={[styles.saveButton, fundingInProgress && styles.disabledButton]}>
                {fundingInProgress ? 'Processing...' : 'Add'}
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Select Bank Account</Text>
              {bankData?.bankAccounts?.map((account: any) => (
                <TouchableOpacity
                  key={account.id}
                  style={[
                    styles.bankOption,
                    selectedBankId === account.id && styles.selectedBankOption
                  ]}
                  onPress={() => setSelectedBankId(account.id)}
                >
                  <Text style={styles.bankOptionText}>
                    {account.bankName} •••• {account.lastFour}
                  </Text>
                  {selectedBankId === account.id && (
                    <Icon name="check" size={20} color="#007AFF" />
                  )}
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Amount</Text>
              <TextInput
                style={styles.input}
                value={fundingAmount}
                onChangeText={setFundingAmount}
                placeholder="Enter amount"
                keyboardType="numeric"
              />
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* SBLOC Calculator */}
      <SBLOCCalculator
        visible={showSBLOCModal}
        onClose={() => setShowSBLOCModal(false)}
        portfolioValue={0} // BankAccountScreen doesn't have portfolio value
        onApply={() => {
          setShowSBLOCModal(false);
          Alert.alert(
            'SBLOC Application',
            'This would open the SBLOC application flow with our partner banks.',
            [{ text: 'OK' }]
          );
        }}
      />

      {/* New SBLOC Calculator Modal */}
      <SblocCalculatorModal
        visible={showSblocCalculator}
        onClose={() => setShowSblocCalculator(false)}
        equity={sblocData?.sblocOffer?.eligibleEquity ?? 50000}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  addButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0F172A',
  },
  bankCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
    overflow: 'hidden',
    paddingLeft: 20,
  },
  bankHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  bankIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F0F8FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  bankInfo: {
    flex: 1,
  },
  bankName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
  },
  accountType: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 2,
  },
  bankStatus: {
    marginLeft: 8,
  },
  bankFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  linkedDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
  primaryBadge: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  primaryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  fundingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F8FF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  fundingButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 4,
  },
  fundingHistory: {
    marginTop: 16,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 12,
  },
  fundingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  fundingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  fundingAmount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  fundingDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
    textAlign: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  cancelButton: {
    fontSize: 16,
    color: '#007AFF',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  saveButton: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  disabledButton: {
    color: '#8E8E93',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  inputGroup: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  bankOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  selectedBankOption: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F8FF',
  },
  bankOptionText: {
    fontSize: 16,
    color: '#000000',
  },

  // New styles for upgraded UI
  // Badges / chips
  chip: { flexDirection:'row', alignItems:'center', paddingHorizontal:10, paddingVertical:4, borderRadius:999 },
  chipText: { fontSize:11, fontWeight:'700' },

  // Avatars
  bankAvatar: { width:40, height:40, borderRadius:20, backgroundColor:'#E8F2FF', alignItems:'center', justifyContent:'center', marginRight:12 },
  bankAvatarText: { color:'#2457D6', fontWeight:'800' },

  // Cards
  leftAccent: { position:'absolute', left:0, top:0, bottom:0, width:4, borderTopLeftRadius:12, borderBottomLeftRadius:12 },
  meta: { fontSize:12, color:'#8E8E93' },

  // Funding rows
  fundingRow: { flexDirection:'row', alignItems:'center', justifyContent:'space-between', backgroundColor:'#FFFFFF', borderRadius:10, padding:12, marginBottom:10 },
  fundingLeft: { flexDirection:'row', alignItems:'center' },
  dot: { width:10, height:10, borderRadius:5, backgroundColor:'#9CA3AF' },

  // Actions
  actionRow: { flexDirection:'row', gap:8 },
  ghostBtn: { flexDirection:'row', alignItems:'center', gap:6, backgroundColor:'#EFF6FF', paddingHorizontal:10, paddingVertical:6, borderRadius:8, minWidth: 80 },
  ghostBtnText: { color:'#2457D6', fontWeight:'700', fontSize: 12 },

  // Skeletons
  skeletonBlock: { marginTop:6 },
  skelLineWide: { height:12, backgroundColor:'#E5E7EB', borderRadius:6, marginBottom:8, width:'60%' },
  skelLine: { height:10, backgroundColor:'#E5E7EB', borderRadius:6, marginBottom:8, width:'40%' },
  skelLineShort: { height:10, backgroundColor:'#E5E7EB', borderRadius:6, width:'28%' },

  // Primary button (reuse in empty state)
  primaryBtn: { backgroundColor:'#2457D6', paddingVertical:12, paddingHorizontal:18, borderRadius:10, marginTop:14 },
  primaryBtnText: { color:'#fff', fontWeight:'700' },

  // Additional missing styles
  emptyRow: { flexDirection:'row', alignItems:'center', gap:8, paddingVertical:8 },

  // SBLOC Modal Styles
  sblocHero: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginVertical: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  sblocIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  sblocTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 8,
  },
  sblocSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  sblocCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  sblocCardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  benefitsList: {
    marginTop: 8,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  benefitText: {
    fontSize: 15,
    color: '#111827',
    marginLeft: 12,
    fontWeight: '500',
  },
  stepsList: {
    marginTop: 8,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F59E0B',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  stepNumberText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  rateComparison: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  rateItem: {
    alignItems: 'center',
    flex: 1,
  },
  rateType: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '600',
    marginBottom: 8,
  },
  rateValue: {
    fontSize: 18,
    fontWeight: '800',
  },
  considerationsList: {
    marginTop: 8,
  },
  considerationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  considerationText: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  sblocCalculatorBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#F59E0B',
    paddingVertical: 16,
    borderRadius: 12,
  },
  sblocCalculatorBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  sblocApplyBtn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#10B981',
    paddingVertical: 16,
    borderRadius: 12,
  },
  sblocApplyBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },

});

export default BankAccountScreen;