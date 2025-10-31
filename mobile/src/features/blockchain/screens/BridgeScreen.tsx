/**
 * Cross-Chain Bridge Screen
 * Allows users to transfer assets between different blockchain networks
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';

interface Network {
  name: string;
  color: string;
  chainId: number;
}

const NETWORKS: Network[] = [
  { name: 'Ethereum', color: '#627EEA', chainId: 1 },
  { name: 'Polygon', color: '#8247E5', chainId: 137 },
  { name: 'Arbitrum', color: '#28A0F0', chainId: 42161 },
  { name: 'Optimism', color: '#FF0420', chainId: 10 },
  { name: 'Base', color: '#0052FF', chainId: 8453 },
];

export default function BridgeScreen() {
  const navigation = useNavigation<any>();
  const [fromNetwork, setFromNetwork] = useState<Network | null>(NETWORKS[0]);
  const [toNetwork, setToNetwork] = useState<Network | null>(NETWORKS[1]);
  const [amount, setAmount] = useState('');
  const [bridging, setBridging] = useState(false);

  const handleBridge = async () => {
    if (!fromNetwork || !toNetwork) {
      Alert.alert('Error', 'Please select both source and destination networks');
      return;
    }

    if (!amount || parseFloat(amount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    if (fromNetwork.chainId === toNetwork.chainId) {
      Alert.alert('Error', 'Source and destination networks must be different');
      return;
    }

    setBridging(true);

    try {
      // Simulate bridge transaction
      await new Promise(resolve => setTimeout(resolve, 2000));

      Alert.alert(
        'Bridge Initiated',
        `Bridging ${amount} tokens from ${fromNetwork.name} to ${toNetwork.name}. Transaction is being processed.`,
        [
          {
            text: 'OK',
            onPress: () => {
              setBridging(false);
              navigation.goBack();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Bridge transaction failed. Please try again.');
      setBridging(false);
    }
  };

  const swapNetworks = () => {
    const temp = fromNetwork;
    setFromNetwork(toNetwork);
    setToNetwork(temp);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-left" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Cross-Chain Bridge</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        <Text style={styles.description}>
          Transfer your assets between different blockchain networks with low fees and fast settlement.
        </Text>

        {/* From Network */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>From</Text>
          <View style={styles.networkSelector}>
            {NETWORKS.map((network) => (
              <TouchableOpacity
                key={network.chainId}
                style={[
                  styles.networkOption,
                  fromNetwork?.chainId === network.chainId && styles.networkOptionSelected,
                ]}
                onPress={() => setFromNetwork(network)}
              >
                <View style={[styles.networkDot, { backgroundColor: network.color }]} />
                <Text style={styles.networkName}>{network.name}</Text>
                {fromNetwork?.chainId === network.chainId && (
                  <Icon name="check" size={16} color="#10B981" style={{ marginLeft: 8 }} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Swap Button */}
        <TouchableOpacity style={styles.swapButton} onPress={swapNetworks}>
          <Icon name="arrow-down" size={20} color="#667EEA" />
        </TouchableOpacity>

        {/* To Network */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>To</Text>
          <View style={styles.networkSelector}>
            {NETWORKS.map((network) => (
              <TouchableOpacity
                key={network.chainId}
                style={[
                  styles.networkOption,
                  toNetwork?.chainId === network.chainId && styles.networkOptionSelected,
                ]}
                onPress={() => setToNetwork(network)}
              >
                <View style={[styles.networkDot, { backgroundColor: network.color }]} />
                <Text style={styles.networkName}>{network.name}</Text>
                {toNetwork?.chainId === network.chainId && (
                  <Icon name="check" size={16} color="#10B981" style={{ marginLeft: 8 }} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Amount Input */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Amount</Text>
          <View style={styles.amountContainer}>
            <TextInput
              style={styles.amountInput}
              placeholder="0.00"
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              placeholderTextColor="#9CA3AF"
            />
            <TouchableOpacity style={styles.maxButton}>
              <Text style={styles.maxButtonText}>MAX</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bridge Info */}
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Bridge Fee</Text>
            <Text style={styles.infoValue}>~0.1%</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Estimated Time</Text>
            <Text style={styles.infoValue}>2-5 minutes</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>You Will Receive</Text>
            <Text style={styles.infoValue}>
              {amount ? `${(parseFloat(amount) * 0.999).toFixed(4)}` : '0.00'} tokens
            </Text>
          </View>
        </View>

        {/* Bridge Button */}
        <TouchableOpacity
          style={[styles.bridgeButton, bridging && styles.bridgeButtonDisabled]}
          onPress={handleBridge}
          disabled={bridging}
        >
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.bridgeButtonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            {bridging ? (
              <View style={styles.bridgeButtonContent}>
                <ActivityIndicator size="small" color="#FFFFFF" />
                <Text style={styles.bridgeButtonText}>Bridging...</Text>
              </View>
            ) : (
              <Text style={styles.bridgeButtonText}>Start Bridge</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 24,
    lineHeight: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  networkSelector: {
    gap: 8,
  },
  networkOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
  },
  networkOptionSelected: {
    borderColor: '#667EEA',
    backgroundColor: '#F3F4F6',
  },
  networkDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  networkName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1F2937',
    flex: 1,
  },
  swapButton: {
    alignSelf: 'center',
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#E5E7EB',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 8,
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 16,
  },
  amountInput: {
    flex: 1,
    fontSize: 24,
    fontWeight: '600',
    color: '#1F2937',
    paddingVertical: 16,
  },
  maxButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#667EEA',
    borderRadius: 6,
  },
  maxButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  bridgeButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 24,
  },
  bridgeButtonDisabled: {
    opacity: 0.7,
  },
  bridgeButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bridgeButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  bridgeButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

