import React, { useMemo, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { connectWallet } from '../blockchain/wallet/walletConnect';
import { HybridTransactionService } from '../services/HybridTransactionService';
import { CHAIN } from '../blockchain/web3Service';

const AAVE_POOL_ADDRESS = '<AAVE_POOL_ADDRESS>'; // e.g., Polygon v3 Pool
const BACKEND_BASE = 'https://api.yourapp.com';  // your Django base URL

const ASSETS = {
  USDC: { address: '<USDC_ADDRESS>', decimals: 6 },
  WETH: { address: '<WETH_ADDRESS>', decimals: 18 },
  // add more as needed
};

export default function CryptoAAVEBorrowCard() {
  const [address, setAddress] = useState<string|null>(null);
  const [wc, setWc] = useState<{client:any, session:any}|null>(null);
  const [amount, setAmount] = useState('100');
  const [symbol, setSymbol] = useState<'USDC'|'WETH'>('USDC');
  const [loading, setLoading] = useState(false);
  const [hash, setHash] = useState<string|undefined>();
  const [status, setStatus] = useState<string|undefined>();

  const deps = useMemo(() => {
    if (!address || !wc) return null;
    return {
      wcClient: wc.client,
      wcSession: wc.session,
      chainIdWC: CHAIN.polygon.chainIdWC,
      userAddress: address,
      aavePool: AAVE_POOL_ADDRESS,
      assetMap: ASSETS,
      backendBaseUrl: BACKEND_BASE
    };
  }, [address, wc]);

  async function onConnect() {
    const { client, session, address } = await connectWallet(CHAIN.polygon.chainIdWC);
    setWc({ client, session });
    setAddress(address);
  }

  async function onSupplyAndBorrow() {
    if (!deps) return;
    setLoading(true); setStatus('Validating + approving…'); setHash(undefined);
    try {
      const svc = new HybridTransactionService(deps);
      const resApprove = await svc.approveIfNeeded(symbol, amount);
      if (!resApprove.skipped) setStatus(`Approve tx sent: ${resApprove.hash}`);

      setStatus('Depositing collateral…');
      const resDeposit = await svc.deposit(symbol, amount);
      setStatus(`Deposited. Tx: ${resDeposit.hash}`);

      // Example: borrow USDC after depositing WETH (or borrow WETH after USDC) — adjust for your UX
      setStatus('Borrowing asset…');
      const borrowSymbol = symbol === 'WETH' ? 'USDC' : 'WETH';
      const resBorrow = await svc.borrow(borrowSymbol, symbol === 'WETH' ? '50' : '0.05', 2);
      setHash(resBorrow.hash);
      setStatus('Done ✓');
    } catch (e: any) {
      setStatus(e?.message || 'Failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>AAVE Borrow (Hybrid)</Text>

      {!address ? (
        <TouchableOpacity style={styles.btn} onPress={onConnect}>
          <Text style={styles.btnText}>Connect Wallet</Text>
        </TouchableOpacity>
      ) : (
        <Text style={styles.addr}>Wallet: {address.slice(0,6)}…{address.slice(-4)}</Text>
      )}

      <View style={styles.row}>
        <Text style={styles.label}>Supply Asset</Text>
        <TouchableOpacity onPress={() => setSymbol(symbol === 'USDC' ? 'WETH' : 'USDC')}>
          <Text style={styles.selector}>{symbol} ▾</Text>
        </TouchableOpacity>
      </View>

      <TextInput
        value={amount}
        onChangeText={setAmount}
        keyboardType="decimal-pad"
        placeholder="Amount"
        style={styles.input}
      />

      <TouchableOpacity disabled={!address || loading} style={styles.btn} onPress={onSupplyAndBorrow}>
        {loading ? <ActivityIndicator/> : <Text style={styles.btnText}>Supply & Borrow</Text>}
      </TouchableOpacity>

      {status && <Text style={styles.status}>{status}</Text>}
      {hash && <Text style={styles.hash}>Tx: {hash}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16, borderRadius: 12, backgroundColor: '#111', gap: 12 },
  title: { color: '#fff', fontSize: 18, fontWeight: '600' },
  addr: { color: '#bbb' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { color: '#aaa' },
  selector: { color: '#fff', fontWeight: '600' },
  input: { backgroundColor: '#1a1a1a', color: '#fff', padding: 10, borderRadius: 8 },
  btn: { backgroundColor: '#0a84ff', padding: 12, borderRadius: 10, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '600' },
  status: { color: '#ddd' },
  hash: { color: '#7bdc86' }
});
