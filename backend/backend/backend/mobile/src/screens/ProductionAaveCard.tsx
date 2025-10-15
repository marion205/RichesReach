import React, { useMemo, useState, useEffect } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, ActivityIndicator, 
  StyleSheet, Alert, ScrollView, Linking 
} from 'react-native';
import { connectWallet } from '../blockchain/wallet/walletConnect';
import { HybridTransactionService } from '../services/hybridTransactionService';
import { CHAIN } from '../blockchain/web3Service';
import { SEPOLIA_CONFIG } from '../config/testnetConfig';
import { getAAVEPoolAddressWithCache } from '../blockchain/aaveResolver';
import Toast from 'react-native-toast-message';

// Sepolia Testnet Configuration
const BACKEND_BASE = 'http://127.0.0.1:8000';  // Your Django base URL

// Helper function to open explorer
const openExplorer = (hash: string) =>
  Linking.openURL(`https://sepolia.etherscan.io/tx/${hash}`);

interface TransactionStep {
  id: string;
  title: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  txHash?: string;
  error?: string;
}

export default function ProductionAAVECard() {
  const [address, setAddress] = useState<string|null>(null);
  const [wc, setWc] = useState<{client:any, session:any}|null>(null);
  const [supplyAmount, setSupplyAmount] = useState('100');
  const [borrowAmount, setBorrowAmount] = useState('50');
  const [supplySymbol, setSupplySymbol] = useState<'USDC'|'AAVE-USDC'|'WETH'>('USDC');
  const [borrowSymbol, setBorrowSymbol] = useState<'USDC'|'AAVE-USDC'|'WETH'>('WETH');
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<TransactionStep[]>([]);
  const [aavePoolAddress, setAAVEPoolAddress] = useState<string>('');

  // Resolve AAVE Pool address dynamically
  useEffect(() => {
    const resolvePoolAddress = async () => {
      try {
        const poolAddr = await getAAVEPoolAddressWithCache(SEPOLIA_CONFIG.rpcUrl);
        setAAVEPoolAddress(poolAddr);
      } catch (error) {
        console.error('Failed to resolve AAVE Pool address:', error);
        setAAVEPoolAddress(SEPOLIA_CONFIG.poolAddress);
      }
    };
    resolvePoolAddress();
  }, []);

  const deps = useMemo(() => {
    if (!address || !wc || !aavePoolAddress) return null;
    return {
      wcClient: wc.client,
      wcSession: wc.session,
      chainIdWC: CHAIN.sepolia.chainIdWC,
      userAddress: address,
      aavePool: aavePoolAddress,
      assetMap: SEPOLIA_CONFIG.assets,
      backendBaseUrl: BACKEND_BASE
    };
  }, [address, wc, aavePoolAddress]);

  const updateStep = (id: string, updates: Partial<TransactionStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === id ? { ...step, ...updates } : step
    ));
  };

  async function onConnect() {
    try {
      const { client, session, address } = await connectWallet(CHAIN.sepolia.chainIdWC);
      setWc({ client, session });
      setAddress(address);
      Alert.alert('Success', `Connected to ${address.slice(0,6)}...${address.slice(-4)}`);
    } catch (error: any) {
      Alert.alert('Connection Failed', error.message);
    }
  }

  async function onDisconnect() {
    setWc(null);
    setAddress(null);
    setSteps([]);
  }

  async function onSupplyAndBorrow() {
    if (!deps) return;

    // Initialize transaction steps
    const initialSteps: TransactionStep[] = [
      { id: 'approve', title: 'Approve Token', status: 'pending' },
      { id: 'supply', title: 'Supply Collateral', status: 'pending' },
      { id: 'borrow', title: 'Borrow Asset', status: 'pending' },
    ];
    setSteps(initialSteps);
    setLoading(true);

    try {
      const svc = new HybridTransactionService(deps);

      // Step 1: Approve
      updateStep('approve', { status: 'loading' });
      Toast.show({ type: 'info', text1: 'Approving token…' });
      const resApprove = await svc.approveIfNeeded(supplySymbol, supplyAmount);
      if (resApprove.skipped) {
        updateStep('approve', { status: 'success' });
        Toast.show({ type: 'info', text1: 'Approval not needed' });
      } else {
        updateStep('approve', { status: 'success', txHash: resApprove.hash });
        Toast.show({
          type: 'success',
          text1: 'Approve sent',
          text2: 'Tap to view on Polygonscan',
          onPress: () => openExplorer(resApprove.hash)
        });
      }

      // Step 2: Supply
      updateStep('supply', { status: 'loading' });
      Toast.show({ type: 'info', text1: 'Depositing collateral…' });
      const resSupply = await svc.deposit(supplySymbol, supplyAmount);
      updateStep('supply', { status: 'success', txHash: resSupply.hash });
      Toast.show({
        type: 'success',
        text1: 'Deposit submitted',
        text2: 'View on Polygonscan',
        onPress: () => openExplorer(resSupply.hash)
      });

      // Step 3: Borrow
      updateStep('borrow', { status: 'loading' });
      Toast.show({ type: 'info', text1: 'Borrowing…' });
      const resBorrow = await svc.borrow(borrowSymbol, borrowAmount, 2);
      updateStep('borrow', { status: 'success', txHash: resBorrow.hash });
      Toast.show({
        type: 'success',
        text1: 'Borrow submitted',
        text2: 'View on Polygonscan',
        onPress: () => openExplorer(resBorrow.hash)
      });

      Toast.show({ type: 'success', text1: 'All transactions completed!', text2: 'Check your positions' });
    } catch (error: any) {
      console.error('Transaction failed:', error);
      
      // Find the current step and mark it as error
      const currentStep = steps.find(step => step.status === 'loading');
      if (currentStep) {
        updateStep(currentStep.id, { 
          status: 'error', 
          error: error.message 
        });
      }
      
      Toast.show({ 
        type: 'error', 
        text1: 'Transaction failed', 
        text2: error?.message ?? 'Unknown error' 
      });
    } finally {
      setLoading(false);
    }
  }

  const canExecute = address && wc && !loading && supplyAmount && borrowAmount;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>🚀 AAVE Hybrid Integration</Text>
        <Text style={styles.subtitle}>Backend Risk + Blockchain Execution</Text>

        {/* Wallet Connection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Wallet</Text>
          {!address ? (
            <TouchableOpacity style={styles.connectBtn} onPress={onConnect}>
              <Text style={styles.btnText}>Connect Wallet</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.walletInfo}>
              <Text style={styles.address}>
                {address.slice(0,6)}...{address.slice(-4)}
              </Text>
              <TouchableOpacity style={styles.disconnectBtn} onPress={onDisconnect}>
                <Text style={styles.disconnectText}>Disconnect</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Supply Configuration */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Supply Collateral</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Asset</Text>
            <TouchableOpacity 
              style={styles.selector}
              onPress={() => {
                const options = ['USDC', 'WETH', 'WMATIC'];
                const currentIndex = options.indexOf(supplySymbol);
                const nextIndex = (currentIndex + 1) % options.length;
                setSupplySymbol(options[nextIndex] as any);
              }}
            >
              <Text style={styles.selectorText}>{supplySymbol} ▾</Text>
            </TouchableOpacity>
          </View>
          <TextInput
            value={supplyAmount}
            onChangeText={setSupplyAmount}
            keyboardType="decimal-pad"
            placeholder="Amount to supply"
            style={styles.input}
          />
        </View>

        {/* Borrow Configuration */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Borrow Asset</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Asset</Text>
            <TouchableOpacity 
              style={styles.selector}
              onPress={() => {
                const options = ['USDC', 'WETH', 'WMATIC'];
                const currentIndex = options.indexOf(borrowSymbol);
                const nextIndex = (currentIndex + 1) % options.length;
                setBorrowSymbol(options[nextIndex] as any);
              }}
            >
              <Text style={styles.selectorText}>{borrowSymbol} ▾</Text>
            </TouchableOpacity>
          </View>
          <TextInput
            value={borrowAmount}
            onChangeText={setBorrowAmount}
            keyboardType="decimal-pad"
            placeholder="Amount to borrow"
            style={styles.input}
          />
        </View>

        {/* Transaction Steps */}
        {steps.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Transaction Progress</Text>
            {steps.map((step) => (
              <View key={step.id} style={styles.step}>
                <View style={styles.stepHeader}>
                  <Text style={styles.stepTitle}>{step.title}</Text>
                  <View style={[
                    styles.statusBadge,
                    { backgroundColor: getStatusColor(step.status) }
                  ]}>
                    {step.status === 'loading' ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.statusText}>
                        {step.status === 'success' ? '✓' : 
                         step.status === 'error' ? '✗' : '○'}
                      </Text>
                    )}
                  </View>
                </View>
                {step.txHash && (
                  <Text style={styles.txHash}>Tx: {step.txHash}</Text>
                )}
                {step.error && (
                  <Text style={styles.errorText}>{step.error}</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {/* Execute Button */}
        <TouchableOpacity 
          disabled={!canExecute} 
          style={[styles.executeBtn, !canExecute && styles.disabledBtn]} 
          onPress={onSupplyAndBorrow}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.btnText}>Execute Hybrid Transaction</Text>
          )}
        </TouchableOpacity>

        {/* Info */}
        <View style={styles.info}>
          <Text style={styles.infoText}>
            🔒 Backend validates risk before blockchain execution
          </Text>
          <Text style={styles.infoText}>
            ⛓️ Real AAVE protocol interactions on Polygon
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'success': return '#10B981';
    case 'error': return '#EF4444';
    case 'loading': return '#3B82F6';
    default: return '#6B7280';
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  card: { 
    margin: 16, 
    padding: 20, 
    borderRadius: 16, 
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333'
  },
  title: { 
    color: '#fff', 
    fontSize: 24, 
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 4
  },
  subtitle: { 
    color: '#888', 
    fontSize: 14, 
    textAlign: 'center',
    marginBottom: 24
  },
  section: { marginBottom: 20 },
  sectionTitle: { 
    color: '#fff', 
    fontSize: 16, 
    fontWeight: '600',
    marginBottom: 12
  },
  row: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    marginBottom: 12
  },
  label: { color: '#aaa', fontSize: 14 },
  selector: { 
    backgroundColor: '#1a1a1a', 
    paddingHorizontal: 12, 
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333'
  },
  selectorText: { color: '#fff', fontWeight: '600' },
  input: { 
    backgroundColor: '#1a1a1a', 
    color: '#fff', 
    padding: 12, 
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
    fontSize: 16
  },
  connectBtn: { 
    backgroundColor: '#0a84ff', 
    padding: 16, 
    borderRadius: 12, 
    alignItems: 'center' 
  },
  walletInfo: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333'
  },
  address: { color: '#fff', fontWeight: '600' },
  disconnectBtn: { padding: 8 },
  disconnectText: { color: '#ef4444', fontSize: 12 },
  step: { 
    backgroundColor: '#1a1a1a', 
    padding: 12, 
    borderRadius: 8, 
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#333'
  },
  stepHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center' 
  },
  stepTitle: { color: '#fff', fontWeight: '500' },
  statusBadge: { 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  statusText: { color: '#fff', fontWeight: 'bold' },
  txHash: { 
    color: '#7bdc86', 
    fontSize: 12, 
    marginTop: 4,
    fontFamily: 'monospace'
  },
  errorText: { 
    color: '#ef4444', 
    fontSize: 12, 
    marginTop: 4 
  },
  executeBtn: { 
    backgroundColor: '#10B981', 
    padding: 16, 
    borderRadius: 12, 
    alignItems: 'center',
    marginTop: 8
  },
  disabledBtn: { backgroundColor: '#374151' },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  info: { 
    marginTop: 16, 
    padding: 12, 
    backgroundColor: '#1a1a1a', 
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333'
  },
  infoText: { 
    color: '#888', 
    fontSize: 12, 
    marginBottom: 4 
  }
});
