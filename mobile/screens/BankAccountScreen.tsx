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
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

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

  const renderBankAccount = (account: any) => (
    <View key={account.id} style={styles.bankCard}>
      <View style={styles.bankHeader}>
        <View style={styles.bankIcon}>
          <Icon name="credit-card" size={24} color="#007AFF" />
        </View>
        <View style={styles.bankInfo}>
          <Text style={styles.bankName}>{account.bankName}</Text>
          <Text style={styles.accountType}>
            {account.accountType.charAt(0).toUpperCase() + account.accountType.slice(1)} •••• {account.lastFour}
          </Text>
        </View>
        <View style={styles.bankStatus}>
          {account.isVerified ? (
            <Icon name="check-circle" size={20} color="#34C759" />
          ) : (
            <Icon name="clock" size={20} color="#FF9500" />
          )}
        </View>
      </View>
      <View style={styles.bankFooter}>
        <Text style={styles.linkedDate}>
          Linked {new Date(account.linkedAt).toLocaleDateString()}
        </Text>
        {account.isPrimary && (
          <View style={styles.primaryBadge}>
            <Text style={styles.primaryText}>Primary</Text>
          </View>
        )}
      </View>
    </View>
  );

  const renderFundingHistory = (funding: any) => (
    <View key={funding.id} style={styles.fundingCard}>
      <View style={styles.fundingHeader}>
        <Text style={styles.fundingAmount}>${funding.amount.toLocaleString()}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(funding.status) }]}>
          <Text style={styles.statusText}>{funding.status.toUpperCase()}</Text>
        </View>
      </View>
      <Text style={styles.fundingDate}>
        {new Date(funding.initiatedAt).toLocaleString()}
      </Text>
    </View>
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#34C759';
      case 'pending': return '#FF9500';
      case 'failed': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  return (
    <View style={styles.container}>
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
        {/* Bank Accounts Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Linked Accounts</Text>
          {bankLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.loadingText}>Loading bank accounts...</Text>
            </View>
          ) : bankData?.bankAccounts?.length > 0 ? (
            bankData.bankAccounts.map(renderBankAccount)
          ) : (
            <View style={styles.emptyState}>
              <Icon name="credit-card" size={48} color="#C7C7CC" />
              <Text style={styles.emptyTitle}>No Bank Accounts</Text>
              <Text style={styles.emptySubtitle}>Link your first bank account to start funding</Text>
            </View>
          )}
        </View>

        {/* Funding Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Quick Funding</Text>
            <TouchableOpacity 
              onPress={() => setShowFundingModal(true)}
              style={styles.fundingButton}
            >
              <Icon name="plus" size={16} color="#007AFF" />
              <Text style={styles.fundingButtonText}>Add Funds</Text>
            </TouchableOpacity>
          </View>

          {fundingData?.fundingHistory?.length > 0 && (
            <View style={styles.fundingHistory}>
              <Text style={styles.historyTitle}>Recent Funding</Text>
              {fundingData.fundingHistory.slice(0, 3).map(renderFundingHistory)}
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
    </View>
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
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000000',
  },
  bankCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  bankHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
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
});

export default BankAccountScreen;