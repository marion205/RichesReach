/**
 * AI Scans Screen (Institution-Grade)
 * RichesReach AI — Market Intelligence Dashboard
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
  Dimensions,
  FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, NetworkStatus } from '@apollo/client';
import { gql } from '@apollo/client';
import { AIScan, Playbook, ScanCategory, RiskLevel } from '../types/AIScansTypes';
import ScanCard from '../components/ScanCard';
import PlaybookCard from '../components/PlaybookCard';
import AIScansService from '../services/AIScansService';
import { logUX } from '../../../utils/telemetry';

const { width } = Dimensions.get('window');

// ⚙️ GraphQL Queries (with explicit field selections for type safety)
const GET_AI_SCANS = gql`
  query GetAIScans($filters: AIScanFilters) {
    aiScans(filters: $filters) {
      id
      name
      description
      category
      riskLevel
      timeHorizon
      isActive
      lastRun
      results {
        id
        symbol
        currentPrice
        changePercent
        confidence
      }
      playbook {
        id
        name
        performance {
          successRate
          averageReturn
        }
      }
    }
  }
`;

const GET_PLAYBOOKS = gql`
  query GetPlaybooks {
    playbooks {
      id
      name
      author
      riskLevel
      performance {
        successRate
        averageReturn
      }
      tags
    }
  }
`;

const AIScansScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [activeTab, setActiveTab] = useState<'scans' | 'playbooks'>('scans');
  const [selectedCategory, setSelectedCategory] = useState<ScanCategory | 'all'>('all');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<RiskLevel | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const renderEmpty = (label: string) => (
    <View style={{ padding: 24, alignItems: 'center' }}>
      <Text style={{ color: '#8E8E93' }}>No {label} yet.</Text>
    </View>
  );

  // 🧩 Apollo Queries with NetworkStatus awareness
  const {
    data: scansData,
    refetch: refetchScans,
    networkStatus: scansNetwork,
  } = useQuery(GET_AI_SCANS, {
    variables: {
      filters: {
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        riskLevel: selectedRiskLevel !== 'all' ? selectedRiskLevel : undefined,
      },
    },
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-and-network',
  });

  const {
    data: playbooksData,
    refetch: refetchPlaybooks,
    networkStatus: playbooksNetwork,
  } = useQuery(GET_PLAYBOOKS, {
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-first',
  });

  const isRefreshing =
    scansNetwork === NetworkStatus.refetch || playbooksNetwork === NetworkStatus.refetch;
  const scans: AIScan[] = scansData?.aiScans ?? [];
  const playbooks: Playbook[] = playbooksData?.playbooks ?? [];

  const handleRefresh = useCallback(async () => {
    await Promise.all([refetchScans(), refetchPlaybooks()]);
  }, [refetchScans, refetchPlaybooks]);

  // 📊 Analytics / Event Logging Hook
  const logEvent = useCallback((event: string, meta?: Record<string, any>) => {
    console.log(JSON.stringify({ event, meta, ts: Date.now() }));
  }, []);

  const handleRunScan = useCallback(
    async (scan: AIScan) => {
      try {
        logUX('ai_scans.run', { scanId: scan.id, category: scan.category });
        const results = await AIScansService.runScan({ scanId: scan.id });
        logUX('ai_scans.run.success', { scanId: scan.id, symbols: results.length });
        Alert.alert('Scan Complete', `Found ${results.length} opportunities`);
        await refetchScans();
      } catch (e) {
        logUX('ai_scans.run.error', { scanId: scan.id, error: e.message });
        Alert.alert('Error', 'Failed to run scan');
      }
    },
    [refetchScans]
  );

  const handleClonePlaybook = useCallback(
    async (pb: Playbook) => {
      try {
        await AIScansService.clonePlaybook({
          playbookId: pb.id,
          name: `${pb.name} (Clone)`,
          description: `Cloned from ${pb.name}`,
        });
        Alert.alert('Success', 'Playbook cloned successfully!');
        await refetchPlaybooks();
      } catch {
        Alert.alert('Error', 'Failed to clone playbook');
      }
    },
    [refetchPlaybooks]
  );

  const renderScans = useMemo(
    () =>
      scans.map((scan) => (
        <ScanCard
          key={scan.id}
          scan={scan}
          onPress={() => navigation.navigate('ScanPlaybook', { scan })}
          onRun={() => handleRunScan(scan)}
        />
      )),
    [scans, handleRunScan, navigation]
  );

  const renderPlaybooks = useMemo(
    () =>
      playbooks.map((pb) => (
        <PlaybookCard key={pb.id} playbook={pb} onPress={() => handleClonePlaybook(pb)} />
      )),
    [playbooks, handleClonePlaybook]
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.iconBtn}>
          <Icon name="arrow-left" size={22} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>AI Scans</Text>
        <TouchableOpacity onPress={() => setShowCreateModal(true)} style={styles.iconBtn}>
          <Icon name="plus" size={20} color="#00cc99" />
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['scans', 'playbooks'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Icon
              name={tab === 'scans' ? 'search' : 'book-open'}
              size={18}
              color={activeTab === tab ? '#00cc99' : '#8E8E93'}
            />
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab === 'scans' ? 'My Scans' : 'Playbooks'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />}
      >
        {activeTab === 'scans' ? renderScans : renderPlaybooks}
        {scansNetwork === NetworkStatus.loading && (
          <View style={styles.loading}>
            <ActivityIndicator size="large" color="#00cc99" />
            <Text style={styles.loadingText}>Loading market intelligence...</Text>
          </View>
        )}
      </ScrollView>

      {/* Create Modal */}
      <Modal visible={showCreateModal} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowCreateModal(false)}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowCreateModal(false)}>
              <Text style={styles.modalCancel}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Create New Scan</Text>
            <TouchableOpacity>
              <Text style={styles.modalSave}>Save</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalText}>
              Define parameters for your AI-driven scan. Market intelligence will adapt to your
              strategy automatically.
            </Text>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomColor: '#E5E5EA',
    borderBottomWidth: 1,
  },
  iconBtn: { padding: 6 },
  headerTitle: { fontSize: 18, fontWeight: '600', color: '#000' },
  tabs: {
    flexDirection: 'row',
    margin: 12,
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 4,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 8,
  },
  tabActive: { backgroundColor: '#fff', elevation: 2 },
  tabText: { marginLeft: 6, fontSize: 14, color: '#8E8E93', fontWeight: '500' },
  tabTextActive: { color: '#00cc99' },
  content: { flex: 1 },
  loading: { marginVertical: 40, alignItems: 'center' },
  loadingText: { marginTop: 10, color: '#8E8E93' },
  modalContainer: { flex: 1, backgroundColor: '#fff' },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomColor: '#E5E5EA',
    borderBottomWidth: 1,
  },
  modalTitle: { fontSize: 18, fontWeight: '600' },
  modalCancel: { color: '#8E8E93', fontSize: 16 },
  modalSave: { color: '#00cc99', fontWeight: '600', fontSize: 16 },
  modalContent: { padding: 16 },
  modalText: { fontSize: 15, color: '#8E8E93', lineHeight: 22 },
});

export default AIScansScreen;