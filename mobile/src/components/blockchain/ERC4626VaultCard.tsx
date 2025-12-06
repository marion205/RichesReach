/**
 * ERC-4626 Vault Card Component
 * Auto-compounding DeFi vaults with standardized interface
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ActivityIndicator, ScrollView } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import * as Haptics from 'expo-haptics';

interface Vault {
  id: string;
  name: string;
  asset: string;
  apy: number;
  tvl: number;
  strategy: string;
  address: string;
  totalAssets: number;
  sharePrice: number;
}

export default function ERC4626VaultCard() {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [selectedVault, setSelectedVault] = useState<Vault | null>(null);
  const [depositAmount, setDepositAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVaults();
  }, []);

  const loadVaults = async () => {
    // Mock vaults - in production, fetch from backend/GraphQL
    setVaults([
      {
        id: '1',
        name: 'USDC Yield Vault',
        asset: 'USDC',
        apy: 4.2,
        tvl: 1250000,
        strategy: 'AAVE + Compound Optimizer',
        address: '0x...',
        totalAssets: 1250000,
        sharePrice: 1.042,
      },
      {
        id: '2',
        name: 'ETH Staking Vault',
        asset: 'ETH',
        apy: 5.8,
        tvl: 2500000,
        strategy: 'Lido + Auto-compound',
        address: '0x...',
        totalAssets: 2500000,
        sharePrice: 1.058,
      },
      {
        id: '3',
        name: 'Multi-Asset Vault',
        asset: 'USDC/ETH',
        apy: 6.5,
        tvl: 500000,
        strategy: 'Balanced Portfolio',
        address: '0x...',
        totalAssets: 500000,
        sharePrice: 1.065,
      },
    ]);
  };

  const handleDeposit = async () => {
    if (!selectedVault) {
      Alert.alert('Error', 'Please select a vault');
      return;
    }

    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    try {
      setLoading(true);
      
      // In production, would call vault contract
      // await vaultContract.deposit(parseFloat(depositAmount), userAddress);
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert(
        'Deposit Successful',
        `Deposited ${depositAmount} ${selectedVault.asset} to ${selectedVault.name}\n\nYou received ${(parseFloat(depositAmount) / selectedVault.sharePrice).toFixed(4)} vault shares.`,
        [{ text: 'OK', onPress: () => {
          setDepositAmount('');
          setSelectedVault(null);
        }}]
      );
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Error', error.message || 'Failed to deposit');
    } finally {
      setLoading(false);
    }
  };

  const handleHarvest = async (vault: Vault) => {
    try {
      setLoading(true);
      
      // In production, would call vault.harvest()
      // await vaultContract.harvest();
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Harvest Complete', `Rewards harvested and auto-compounded for ${vault.name}`);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to harvest');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="layers" size={20} color="#667eea" />
        <Text style={styles.title}>ERC-4626 Vaults</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Auto-Compound</Text>
        </View>
      </View>

      <Text style={styles.description}>
        Standardized vaults with auto-compounding. Deposit once, earn yield automatically.
      </Text>

      {/* Vault List */}
      <ScrollView style={styles.vaultList} showsVerticalScrollIndicator={false}>
        {vaults.map((vault) => (
          <TouchableOpacity
            key={vault.id}
            style={[
              styles.vaultCard,
              selectedVault?.id === vault.id && styles.vaultCardSelected,
            ]}
            onPress={() => setSelectedVault(vault)}
          >
            <View style={styles.vaultHeader}>
              <View style={styles.vaultInfo}>
                <Text style={styles.vaultName}>{vault.name}</Text>
                <Text style={styles.vaultStrategy}>{vault.strategy}</Text>
              </View>
              <View style={styles.apyBadge}>
                <Text style={styles.apyValue}>{vault.apy}%</Text>
                <Text style={styles.apyLabel}>APY</Text>
              </View>
            </View>

            <View style={styles.vaultStats}>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>TVL</Text>
                <Text style={styles.statValue}>${(vault.tvl / 1000).toFixed(0)}K</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>Share Price</Text>
                <Text style={styles.statValue}>${vault.sharePrice.toFixed(4)}</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>Asset</Text>
                <Text style={styles.statValue}>{vault.asset}</Text>
              </View>
            </View>

            {selectedVault?.id === vault.id && (
              <View style={styles.depositSection}>
                <TextInput
                  style={styles.depositInput}
                  placeholder="Amount to deposit"
                  value={depositAmount}
                  onChangeText={setDepositAmount}
                  keyboardType="decimal-pad"
                />
                <View style={styles.depositActions}>
                  <TouchableOpacity
                    style={styles.depositButton}
                    onPress={handleDeposit}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Icon name="arrow-down-circle" size={16} color="#FFFFFF" />
                        <Text style={styles.depositButtonText}>Deposit</Text>
                      </>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.harvestButton}
                    onPress={() => handleHarvest(vault)}
                    disabled={loading}
                  >
                    <Icon name="refresh-cw" size={16} color="#667eea" />
                    <Text style={styles.harvestButtonText}>Harvest</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Info */}
      <View style={styles.infoBox}>
        <Icon name="info" size={14} color="#666" />
        <Text style={styles.infoText}>
          ERC-4626 vaults auto-compound rewards. No manual harvesting needed. Standardized interface for maximum compatibility.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    maxHeight: 600,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginLeft: 8,
    flex: 1,
  },
  badge: {
    backgroundColor: '#667eea15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    color: '#667eea',
    fontSize: 11,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  vaultList: {
    maxHeight: 400,
  },
  vaultCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  vaultCardSelected: {
    borderColor: '#667eea',
    borderWidth: 2,
  },
  vaultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  vaultInfo: {
    flex: 1,
  },
  vaultName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  vaultStrategy: {
    fontSize: 12,
    color: '#666',
  },
  apyBadge: {
    backgroundColor: '#34C75915',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  apyValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#34C759',
  },
  apyLabel: {
    fontSize: 10,
    color: '#34C759',
    marginTop: 2,
  },
  vaultStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  stat: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  depositSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  depositInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  depositActions: {
    flexDirection: 'row',
    gap: 8,
  },
  depositButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#667eea',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  depositButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  harvestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F2F2F7',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  harvestButtonText: {
    color: '#667eea',
    fontSize: 14,
    fontWeight: '600',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  infoText: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
    flex: 1,
  },
});

