import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { useWallet } from '../wallet/WalletProvider';
import { ethers } from 'ethers';
import { 
  TOP_YIELDS_QUERY, 
  STAKE_INTENT_MUTATION, 
  RECORD_STAKE_TRANSACTION_MUTATION 
} from '../graphql/queries_actual_schema';

interface Pool {
  id: string;
  protocol: {
    name: string;
  };
  chain: {
    name: string;
    chainId: number;
  };
  symbol: string;
  poolAddress: string;
  apy: number;
  tvl: number;
  risk: number;
}

const CHAIN_IDS = {
  ethereum: 1,
  base: 8453,
  polygon: 137,
  arbitrum: 42161,
};

export default function DeFiStakingScreen() {
  const { evm, connect, disconnect, isConnected, address, chainId } = useWallet();
  const [selectedPool, setSelectedPool] = useState<Pool | null>(null);
  const [stakeAmount, setStakeAmount] = useState('');
  const [isStaking, setIsStaking] = useState(false);

  const { data: yieldsData, loading, refetch } = useQuery(TOP_YIELDS_QUERY, {
    variables: { limit: 20 },
    fetchPolicy: 'cache-and-network',
  });

  const [stakeIntent] = useMutation(STAKE_INTENT_MUTATION);
  const [recordStakeTx] = useMutation(RECORD_STAKE_TRANSACTION_MUTATION);

  const pools: Pool[] = yieldsData?.topYields || [];

  const handleConnectWallet = async () => {
    try {
      await connect();
    } catch (error) {
      Alert.alert('Connection Failed', 'Failed to connect wallet');
    }
  };

  const handleStake = async () => {
    if (!selectedPool || !stakeAmount || !evm) {
      Alert.alert('Error', 'Please select a pool, enter amount, and connect wallet');
      return;
    }

    setIsStaking(true);
    try {
      // 1. Get stake intent from backend
      const { data: intentData } = await stakeIntent({
        variables: {
          poolId: selectedPool.id,
          wallet: address,
          amount: parseFloat(stakeAmount),
        },
      });

      if (!intentData?.stakeIntent?.ok) {
        throw new Error(intentData?.stakeIntent?.message || 'Stake intent failed');
      }

      // 2. Approve LP token (if needed)
      const amountWei = ethers.utils.parseEther(stakeAmount);
      
      // Generic ERC20 approve
      const erc20Abi = ['function approve(address spender, uint256 amount) returns (bool)'];
      const lpToken = new ethers.Contract(
        selectedPool.poolAddress, // This would be the LP token address
        erc20Abi,
        evm.signer
      );

      const approveTx = await lpToken.approve(
        selectedPool.poolAddress, // Staking contract address
        amountWei
      );
      await approveTx.wait(1);

      // 3. Stake tokens
      const stakingAbi = ['function deposit(uint256 amount)'];
      const stakingContract = new ethers.Contract(
        selectedPool.poolAddress,
        stakingAbi,
        evm.signer
      );

      const stakeTx = await stakingContract.deposit(amountWei);
      const receipt = await stakeTx.wait(1);

      // 4. Record transaction on backend
      await recordStakeTx({
        variables: {
          poolId: selectedPool.id,
          chainId: selectedPool.chain.chainId,
          wallet: address,
          txHash: receipt.transactionHash,
          amount: parseFloat(stakeAmount),
        },
      });

      Alert.alert(
        'Stake Successful!',
        `Successfully staked ${stakeAmount} ${selectedPool.symbol} tokens`
      );

      // Reset form
      setStakeAmount('');
      setSelectedPool(null);
      refetch();

    } catch (error) {
      console.error('Staking error:', error);
      Alert.alert('Staking Failed', error.message || 'Unknown error occurred');
    } finally {
      setIsStaking(false);
    }
  };

  const formatAPY = (apy: number) => `${apy.toFixed(2)}%`;
  const formatTVL = (tvl: number) => `$${(tvl / 1e6).toFixed(1)}M`;
  const formatRisk = (risk: number) => {
    if (risk < 0.3) return 'Low';
    if (risk < 0.7) return 'Medium';
    return 'High';
  };

  const getRiskColor = (risk: number) => {
    if (risk < 0.3) return '#10B981';
    if (risk < 0.7) return '#F59E0B';
    return '#EF4444';
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading DeFi pools...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DeFi Yield Farming</Text>
        <Text style={styles.subtitle}>Stake tokens and earn yield</Text>
      </View>

      {/* Wallet Connection */}
      <View style={styles.walletSection}>
        {!isConnected ? (
          <TouchableOpacity style={styles.connectButton} onPress={handleConnectWallet}>
            <Text style={styles.connectButtonText}>Connect Wallet</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.walletInfo}>
            <Text style={styles.walletAddress}>
              {address?.slice(0, 6)}...{address?.slice(-4)}
            </Text>
            <TouchableOpacity style={styles.disconnectButton} onPress={disconnect}>
              <Text style={styles.disconnectButtonText}>Disconnect</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Pool Selection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Select Pool</Text>
        {pools.map((pool) => (
          <TouchableOpacity
            key={pool.id}
            style={[
              styles.poolCard,
              selectedPool?.id === pool.id && styles.selectedPoolCard
            ]}
            onPress={() => setSelectedPool(pool)}
          >
            <View style={styles.poolHeader}>
              <Text style={styles.poolSymbol}>{pool.symbol}</Text>
              <Text style={styles.poolProtocol}>{pool.protocol.name}</Text>
            </View>
            <View style={styles.poolMetrics}>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>APY</Text>
                <Text style={styles.metricValue}>{formatAPY(pool.apy)}</Text>
              </View>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>TVL</Text>
                <Text style={styles.metricValue}>{formatTVL(pool.tvl)}</Text>
              </View>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Risk</Text>
                <Text style={[styles.metricValue, { color: getRiskColor(pool.risk) }]}>
                  {formatRisk(pool.risk)}
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Stake Form */}
      {selectedPool && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Stake Amount</Text>
          <TextInput
            style={styles.input}
            value={stakeAmount}
            onChangeText={setStakeAmount}
            placeholder="Enter amount to stake"
            keyboardType="numeric"
          />
          <TouchableOpacity
            style={[styles.stakeButton, (!isConnected || !stakeAmount) && styles.disabledButton]}
            onPress={handleStake}
            disabled={!isConnected || !stakeAmount || isStaking}
          >
            {isStaking ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.stakeButtonText}>Stake {selectedPool.symbol}</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748B',
  },
  header: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E293B',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
    marginTop: 4,
  },
  walletSection: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    marginTop: 8,
  },
  connectButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  walletInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  walletAddress: {
    fontSize: 16,
    color: '#1E293B',
    fontFamily: 'monospace',
  },
  disconnectButton: {
    backgroundColor: '#EF4444',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
  },
  disconnectButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  section: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 16,
  },
  poolCard: {
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  selectedPoolCard: {
    borderColor: '#3B82F6',
    backgroundColor: '#EFF6FF',
  },
  poolHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  poolSymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
  },
  poolProtocol: {
    fontSize: 14,
    color: '#64748B',
  },
  poolMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
  },
  input: {
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  stakeButton: {
    backgroundColor: '#10B981',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#9CA3AF',
  },
  stakeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
