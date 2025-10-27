/**
 * Comprehensive Admin Dashboard
 * System monitoring, user management, and analytics
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
  Switch,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import { Ionicons } from '@expo/vector-icons';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Queries and Mutations
const GET_SYSTEM_METRICS = gql`
  query GetSystemMetrics {
    systemMetrics {
      totalUsers
      activeUsers
      totalTrades
      totalVolume
      systemUptime
      errorRate
      responseTime
      cpuUsage
      memoryUsage
      diskUsage
    }
  }
`;

const GET_USER_ANALYTICS = gql`
  query GetUserAnalytics {
    userAnalytics {
      totalUsers
      newUsersToday
      activeUsersToday
      userGrowth
      retentionRate
      averageSessionDuration
      topCountries
      userSegments
    }
  }
`;

const GET_TRADING_METRICS = gql`
  query GetTradingMetrics {
    tradingMetrics {
      totalTrades
      totalVolume
      averageTradeSize
      successRate
      topSymbols
      tradingHours
      userTradingStats
    }
  }
`;

const GET_SYSTEM_LOGS = gql`
  query GetSystemLogs($limit: Int, $level: String) {
    systemLogs(limit: $limit, level: $level) {
      id
      timestamp
      level
      message
      source
      userId
      details
    }
  }
`;

const GET_USER_LIST = gql`
  query GetUserList($limit: Int, $offset: Int) {
    users(limit: $limit, offset: $offset) {
      id
      username
      email
      status
      createdAt
      lastLogin
      totalTrades
      totalVolume
      accountValue
    }
  }
`;

const UPDATE_USER_STATUS = gql`
  mutation UpdateUserStatus($userId: ID!, $status: String!) {
    updateUserStatus(userId: $userId, status: $status) {
      success
      message
    }
  }
`;

const SEND_SYSTEM_ALERT = gql`
  mutation SendSystemAlert($message: String!, $level: String!) {
    sendSystemAlert(message: $message, level: $level) {
      success
      message
    }
  }
`;

const RESTART_SERVICE = gql`
  mutation RestartService($serviceName: String!) {
    restartService(serviceName: $serviceName) {
      success
      message
    }
  }
`;

interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalTrades: number;
  totalVolume: number;
  systemUptime: number;
  errorRate: number;
  responseTime: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}

interface UserAnalytics {
  totalUsers: number;
  newUsersToday: number;
  activeUsersToday: number;
  userGrowth: number[];
  retentionRate: number;
  averageSessionDuration: number;
  topCountries: { country: string; users: number }[];
  userSegments: { segment: string; count: number }[];
}

interface TradingMetrics {
  totalTrades: number;
  totalVolume: number;
  averageTradeSize: number;
  successRate: number;
  topSymbols: { symbol: string; volume: number }[];
  tradingHours: number[];
  userTradingStats: { userId: string; trades: number; volume: number }[];
}

interface SystemLog {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  message: string;
  source: string;
  userId?: string;
  details?: any;
}

interface User {
  id: string;
  username: string;
  email: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'BANNED';
  createdAt: string;
  lastLogin: string;
  totalTrades: number;
  totalVolume: number;
  accountValue: number;
}

interface AdminDashboardProps {
  adminId: string;
  onUserAction?: (action: string, userId: string) => void;
  onSystemAction?: (action: string, data: any) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({
  adminId,
  onUserAction,
  onSystemAction,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'trading' | 'system' | 'logs'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertLevel, setAlertLevel] = useState<'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'>('INFO');

  const { data: systemData, loading: systemLoading, refetch: refetchSystem } = useQuery(GET_SYSTEM_METRICS);
  const { data: userAnalyticsData, loading: userAnalyticsLoading, refetch: refetchUserAnalytics } = useQuery(GET_USER_ANALYTICS);
  const { data: tradingData, loading: tradingLoading, refetch: refetchTrading } = useQuery(GET_TRADING_METRICS);
  const { data: logsData, loading: logsLoading, refetch: refetchLogs } = useQuery(
    GET_SYSTEM_LOGS,
    { variables: { limit: 50, level: null } }
  );
  const { data: usersData, loading: usersLoading, refetch: refetchUsers } = useQuery(
    GET_USER_LIST,
    { variables: { limit: 100, offset: 0 } }
  );

  const [updateUserStatus] = useMutation(UPDATE_USER_STATUS);
  const [sendSystemAlert] = useMutation(SEND_SYSTEM_ALERT);
  const [restartService] = useMutation(RESTART_SERVICE);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchSystem(),
        refetchUserAnalytics(),
        refetchTrading(),
        refetchLogs(),
        refetchUsers(),
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleUserStatusUpdate = async (userId: string, status: string) => {
    try {
      const result = await updateUserStatus({ variables: { userId, status } });
      if (result.data?.updateUserStatus?.success) {
        Alert.alert('Success', 'User status updated successfully!');
        refetchUsers();
        onUserAction?.('status_update', userId);
      } else {
        Alert.alert('Error', result.data?.updateUserStatus?.message || 'Failed to update user status');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update user status');
    }
  };

  const handleSendAlert = async () => {
    try {
      const result = await sendSystemAlert({ variables: { message: alertMessage, level: alertLevel } });
      if (result.data?.sendSystemAlert?.success) {
        Alert.alert('Success', 'System alert sent successfully!');
        setShowAlertModal(false);
        setAlertMessage('');
        onSystemAction?.('alert_sent', { message: alertMessage, level: alertLevel });
      } else {
        Alert.alert('Error', result.data?.sendSystemAlert?.message || 'Failed to send alert');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to send alert');
    }
  };

  const handleRestartService = async (serviceName: string) => {
    try {
      const result = await restartService({ variables: { serviceName } });
      if (result.data?.restartService?.success) {
        Alert.alert('Success', `${serviceName} restarted successfully!`);
        onSystemAction?.('service_restart', serviceName);
      } else {
        Alert.alert('Error', result.data?.restartService?.message || 'Failed to restart service');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to restart service');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return '#00ff88';
      case 'SUSPENDED': return '#ffbb00';
      case 'BANNED': return '#ff4444';
      default: return '#888';
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return '#00ff88';
      case 'WARNING': return '#ffbb00';
      case 'ERROR': return '#ff4444';
      case 'CRITICAL': return '#ff0000';
      default: return '#888';
    }
  };

  const renderOverviewTab = () => {
    if (!systemData?.systemMetrics || !userAnalyticsData?.userAnalytics || !tradingData?.tradingMetrics) {
      return null;
    }

    const system = systemData.systemMetrics;
    const userAnalytics = userAnalyticsData.userAnalytics;
    const trading = tradingData.tradingMetrics;

    const chartConfig = {
      backgroundColor: '#000',
      backgroundGradientFrom: '#1a1a1a',
      backgroundGradientTo: '#333',
      decimalPlaces: 0,
      color: (opacity = 1) => `rgba(0, 255, 0, ${opacity})`,
      labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
      style: {
        borderRadius: 16,
      },
    };

    const userGrowthData = {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [
        {
          data: userAnalytics.userGrowth,
          color: (opacity = 1) => `rgba(0, 255, 0, ${opacity})`,
          strokeWidth: 2,
        },
      ],
    };

    const tradingHoursData = {
      labels: ['0', '4', '8', '12', '16', '20'],
      datasets: [
        {
          data: trading.tradingHours,
        },
      ],
    };

    const topSymbolsData = {
      labels: trading.topSymbols.map(s => s.symbol),
      data: trading.topSymbols.map(s => s.volume),
      colors: ['#00ff88', '#ff4444', '#ffbb00', '#007bff', '#ff8800'],
    };

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* System Metrics */}
        <View style={styles.metricsCard}>
          <Text style={styles.metricsTitle}>System Metrics</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Users</Text>
              <Text style={styles.metricValue}>{system.totalUsers.toLocaleString()}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Active Users</Text>
              <Text style={styles.metricValue}>{system.activeUsers.toLocaleString()}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Trades</Text>
              <Text style={styles.metricValue}>{system.totalTrades.toLocaleString()}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Volume</Text>
              <Text style={styles.metricValue}>{formatCurrency(system.totalVolume)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>System Uptime</Text>
              <Text style={styles.metricValue}>{system.systemUptime.toFixed(1)}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Error Rate</Text>
              <Text style={[styles.metricValue, { color: system.errorRate > 5 ? '#ff4444' : '#00ff88' }]}>
                {system.errorRate.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Response Time</Text>
              <Text style={styles.metricValue}>{system.responseTime.toFixed(0)}ms</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>CPU Usage</Text>
              <Text style={[styles.metricValue, { color: system.cpuUsage > 80 ? '#ff4444' : '#00ff88' }]}>
                {system.cpuUsage.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Memory Usage</Text>
              <Text style={[styles.metricValue, { color: system.memoryUsage > 80 ? '#ff4444' : '#00ff88' }]}>
                {system.memoryUsage.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Disk Usage</Text>
              <Text style={[styles.metricValue, { color: system.diskUsage > 80 ? '#ff4444' : '#00ff88' }]}>
                {system.diskUsage.toFixed(1)}%
              </Text>
            </View>
          </View>
        </View>

        {/* User Growth Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>User Growth (7 Days)</Text>
          <LineChart
            data={userGrowthData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        {/* Trading Hours Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Trading Activity by Hour</Text>
          <BarChart
            data={tradingHoursData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            style={styles.chart}
            showValuesOnTopOfBars={true}
          />
        </View>

        {/* Top Symbols Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>Top Trading Symbols</Text>
          <PieChart
            data={topSymbolsData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            accessor="data"
            backgroundColor="transparent"
            paddingLeft="15"
            center={[10, 0]}
            absolute
          />
        </View>

        {/* Quick Actions */}
        <View style={styles.actionsCard}>
          <Text style={styles.actionsTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => setShowAlertModal(true)}
            >
              <Ionicons name="warning-outline" size={24} color="#ffbb00" />
              <Text style={styles.actionButtonText}>Send Alert</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleRestartService('trading-engine')}
            >
              <Ionicons name="refresh-outline" size={24} color="#007bff" />
              <Text style={styles.actionButtonText}>Restart Trading</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleRestartService('api-server')}
            >
              <Ionicons name="server-outline" size={24} color="#00ff88" />
              <Text style={styles.actionButtonText}>Restart API</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleRestartService('database')}
            >
              <Ionicons name="database-outline" size={24} color="#ff4444" />
              <Text style={styles.actionButtonText}>Restart DB</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderUsersTab = () => {
    if (!usersData?.users) return null;

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {usersData.users.map((user: User) => (
          <TouchableOpacity
            key={user.id}
            style={styles.userCard}
            onPress={() => {
              setSelectedUser(user);
              setShowUserModal(true);
            }}
          >
            <View style={styles.userHeader}>
              <View style={styles.userInfo}>
                <Text style={styles.userName}>{user.username}</Text>
                <Text style={styles.userEmail}>{user.email}</Text>
              </View>
              <View style={[
                styles.userStatus,
                { backgroundColor: getStatusColor(user.status) }
              ]}>
                <Text style={styles.userStatusText}>{user.status}</Text>
              </View>
            </View>

            <View style={styles.userDetails}>
              <View style={styles.userDetailRow}>
                <Text style={styles.userDetailLabel}>Created</Text>
                <Text style={styles.userDetailValue}>{formatTimestamp(user.createdAt)}</Text>
              </View>
              <View style={styles.userDetailRow}>
                <Text style={styles.userDetailLabel}>Last Login</Text>
                <Text style={styles.userDetailValue}>{formatTimestamp(user.lastLogin)}</Text>
              </View>
              <View style={styles.userDetailRow}>
                <Text style={styles.userDetailLabel}>Total Trades</Text>
                <Text style={styles.userDetailValue}>{user.totalTrades}</Text>
              </View>
              <View style={styles.userDetailRow}>
                <Text style={styles.userDetailLabel}>Total Volume</Text>
                <Text style={styles.userDetailValue}>{formatCurrency(user.totalVolume)}</Text>
              </View>
              <View style={styles.userDetailRow}>
                <Text style={styles.userDetailLabel}>Account Value</Text>
                <Text style={styles.userDetailValue}>{formatCurrency(user.accountValue)}</Text>
              </View>
            </View>

            <View style={styles.userActions}>
              <TouchableOpacity
                style={styles.userActionButton}
                onPress={() => handleUserStatusUpdate(user.id, 'SUSPENDED')}
              >
                <Text style={styles.userActionButtonText}>Suspend</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.userActionButton}
                onPress={() => handleUserStatusUpdate(user.id, 'BANNED')}
              >
                <Text style={styles.userActionButtonText}>Ban</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.userActionButton}
                onPress={() => handleUserStatusUpdate(user.id, 'ACTIVE')}
              >
                <Text style={styles.userActionButtonText}>Activate</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  };

  const renderTradingTab = () => {
    if (!tradingData?.tradingMetrics) return null;

    const trading = tradingData.tradingMetrics;

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.tradingCard}>
          <Text style={styles.tradingTitle}>Trading Metrics</Text>
          
          <View style={styles.tradingMetrics}>
            <View style={styles.tradingMetric}>
              <Text style={styles.tradingMetricLabel}>Total Trades</Text>
              <Text style={styles.tradingMetricValue}>{trading.totalTrades.toLocaleString()}</Text>
            </View>
            <View style={styles.tradingMetric}>
              <Text style={styles.tradingMetricLabel}>Total Volume</Text>
              <Text style={styles.tradingMetricValue}>{formatCurrency(trading.totalVolume)}</Text>
            </View>
            <View style={styles.tradingMetric}>
              <Text style={styles.tradingMetricLabel}>Average Trade Size</Text>
              <Text style={styles.tradingMetricValue}>{formatCurrency(trading.averageTradeSize)}</Text>
            </View>
            <View style={styles.tradingMetric}>
              <Text style={styles.tradingMetricLabel}>Success Rate</Text>
              <Text style={styles.tradingMetricValue}>{trading.successRate.toFixed(1)}%</Text>
            </View>
          </View>
        </View>

        <View style={styles.topSymbolsCard}>
          <Text style={styles.topSymbolsTitle}>Top Trading Symbols</Text>
          {trading.topSymbols.map((symbol, index) => (
            <View key={index} style={styles.symbolRow}>
              <Text style={styles.symbolName}>{symbol.symbol}</Text>
              <Text style={styles.symbolVolume}>{formatCurrency(symbol.volume)}</Text>
            </View>
          ))}
        </View>

        <View style={styles.userTradingCard}>
          <Text style={styles.userTradingTitle}>Top Trading Users</Text>
          {trading.userTradingStats.slice(0, 10).map((user, index) => (
            <View key={index} style={styles.userTradingRow}>
              <Text style={styles.userTradingId}>{user.userId}</Text>
              <Text style={styles.userTradingTrades}>{user.trades} trades</Text>
              <Text style={styles.userTradingVolume}>{formatCurrency(user.volume)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderSystemTab = () => {
    if (!systemData?.systemMetrics) return null;

    const system = systemData.systemMetrics;

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.systemCard}>
          <Text style={styles.systemTitle}>System Health</Text>
          
          <View style={styles.systemMetrics}>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>System Uptime</Text>
              <Text style={styles.systemMetricValue}>{system.systemUptime.toFixed(1)}%</Text>
            </View>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>Error Rate</Text>
              <Text style={[
                styles.systemMetricValue,
                { color: system.errorRate > 5 ? '#ff4444' : '#00ff88' }
              ]}>
                {system.errorRate.toFixed(2)}%
              </Text>
            </View>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>Response Time</Text>
              <Text style={styles.systemMetricValue}>{system.responseTime.toFixed(0)}ms</Text>
            </View>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>CPU Usage</Text>
              <Text style={[
                styles.systemMetricValue,
                { color: system.cpuUsage > 80 ? '#ff4444' : '#00ff88' }
              ]}>
                {system.cpuUsage.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>Memory Usage</Text>
              <Text style={[
                styles.systemMetricValue,
                { color: system.memoryUsage > 80 ? '#ff4444' : '#00ff88' }
              ]}>
                {system.memoryUsage.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.systemMetric}>
              <Text style={styles.systemMetricLabel}>Disk Usage</Text>
              <Text style={[
                styles.systemMetricValue,
                { color: system.diskUsage > 80 ? '#ff4444' : '#00ff88' }
              ]}>
                {system.diskUsage.toFixed(1)}%
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.servicesCard}>
          <Text style={styles.servicesTitle}>Services</Text>
          
          <View style={styles.serviceList}>
            <View style={styles.serviceItem}>
              <Text style={styles.serviceName}>Trading Engine</Text>
              <View style={styles.serviceStatus}>
                <View style={[styles.serviceIndicator, { backgroundColor: '#00ff88' }]} />
                <Text style={styles.serviceStatusText}>Running</Text>
              </View>
              <TouchableOpacity
                style={styles.serviceAction}
                onPress={() => handleRestartService('trading-engine')}
              >
                <Text style={styles.serviceActionText}>Restart</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.serviceItem}>
              <Text style={styles.serviceName}>API Server</Text>
              <View style={styles.serviceStatus}>
                <View style={[styles.serviceIndicator, { backgroundColor: '#00ff88' }]} />
                <Text style={styles.serviceStatusText}>Running</Text>
              </View>
              <TouchableOpacity
                style={styles.serviceAction}
                onPress={() => handleRestartService('api-server')}
              >
                <Text style={styles.serviceActionText}>Restart</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.serviceItem}>
              <Text style={styles.serviceName}>Database</Text>
              <View style={styles.serviceStatus}>
                <View style={[styles.serviceIndicator, { backgroundColor: '#00ff88' }]} />
                <Text style={styles.serviceStatusText}>Running</Text>
              </View>
              <TouchableOpacity
                style={styles.serviceAction}
                onPress={() => handleRestartService('database')}
              >
                <Text style={styles.serviceActionText}>Restart</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.serviceItem}>
              <Text style={styles.serviceName}>WebSocket Server</Text>
              <View style={styles.serviceStatus}>
                <View style={[styles.serviceIndicator, { backgroundColor: '#00ff88' }]} />
                <Text style={styles.serviceStatusText}>Running</Text>
              </View>
              <TouchableOpacity
                style={styles.serviceAction}
                onPress={() => handleRestartService('websocket-server')}
              >
                <Text style={styles.serviceActionText}>Restart</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderLogsTab = () => {
    if (!logsData?.systemLogs) return null;

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {logsData.systemLogs.map((log: SystemLog) => (
          <View key={log.id} style={styles.logCard}>
            <View style={styles.logHeader}>
              <View style={[
                styles.logLevel,
                { backgroundColor: getLogLevelColor(log.level) }
              ]}>
                <Text style={styles.logLevelText}>{log.level}</Text>
              </View>
              <Text style={styles.logTimestamp}>{formatTimestamp(log.timestamp)}</Text>
            </View>
            
            <Text style={styles.logMessage}>{log.message}</Text>
            
            <View style={styles.logDetails}>
              <Text style={styles.logSource}>Source: {log.source}</Text>
              {log.userId && <Text style={styles.logUserId}>User: {log.userId}</Text>}
            </View>
          </View>
        ))}
      </ScrollView>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'users':
        return renderUsersTab();
      case 'trading':
        return renderTradingTab();
      case 'system':
        return renderSystemTab();
      case 'logs':
        return renderLogsTab();
      default:
        return null;
    }
  };

  if (systemLoading || userAnalyticsLoading || tradingLoading || logsLoading || usersLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0F0" />
        <Text style={styles.loadingText}>Loading admin dashboard...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Admin Dashboard</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="settings-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'overview', label: 'Overview', icon: 'home-outline' },
          { key: 'users', label: 'Users', icon: 'people-outline' },
          { key: 'trading', label: 'Trading', icon: 'trending-up-outline' },
          { key: 'system', label: 'System', icon: 'server-outline' },
          { key: 'logs', label: 'Logs', icon: 'document-text-outline' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabButton,
              activeTab === tab.key && styles.activeTabButton,
            ]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons
              name={tab.icon as any}
              size={20}
              color={activeTab === tab.key ? '#0F0' : '#888'}
            />
            <Text style={[
              styles.tabText,
              activeTab === tab.key && styles.activeTabText,
            ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      <View style={styles.content}>
        {renderTabContent()}
      </View>

      {/* User Details Modal */}
      <Modal
        visible={showUserModal}
        animationType="slide"
        onRequestClose={() => setShowUserModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>User Details</Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowUserModal(false)}
            >
              <Ionicons name="close" size={24} color="#fff" />
            </TouchableOpacity>
          </View>
          
          {selectedUser && (
            <ScrollView style={styles.modalContent}>
              <View style={styles.modalUserCard}>
                <Text style={styles.modalUserName}>{selectedUser.username}</Text>
                <Text style={styles.modalUserEmail}>{selectedUser.email}</Text>
                <Text style={styles.modalUserStatus}>Status: {selectedUser.status}</Text>
                <Text style={styles.modalUserCreated}>Created: {formatTimestamp(selectedUser.createdAt)}</Text>
                <Text style={styles.modalUserLastLogin}>Last Login: {formatTimestamp(selectedUser.lastLogin)}</Text>
                <Text style={styles.modalUserTrades}>Total Trades: {selectedUser.totalTrades}</Text>
                <Text style={styles.modalUserVolume}>Total Volume: {formatCurrency(selectedUser.totalVolume)}</Text>
                <Text style={styles.modalUserValue}>Account Value: {formatCurrency(selectedUser.accountValue)}</Text>
              </View>
            </ScrollView>
          )}
        </View>
      </Modal>

      {/* Alert Modal */}
      <Modal
        visible={showAlertModal}
        animationType="slide"
        onRequestClose={() => setShowAlertModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Send System Alert</Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowAlertModal(false)}
            >
              <Ionicons name="close" size={24} color="#fff" />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <View style={styles.alertForm}>
              <Text style={styles.alertFormLabel}>Alert Level</Text>
              <View style={styles.alertLevelSelector}>
                {(['INFO', 'WARNING', 'ERROR', 'CRITICAL'] as const).map((level) => (
                  <TouchableOpacity
                    key={level}
                    style={[
                      styles.alertLevelButton,
                      alertLevel === level && styles.activeAlertLevelButton,
                    ]}
                    onPress={() => setAlertLevel(level)}
                  >
                    <Text style={[
                      styles.alertLevelButtonText,
                      alertLevel === level && styles.activeAlertLevelButtonText,
                    ]}>
                      {level}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              
              <Text style={styles.alertFormLabel}>Message</Text>
              <TextInput
                style={styles.alertMessageInput}
                value={alertMessage}
                onChangeText={setAlertMessage}
                placeholder="Enter alert message..."
                placeholderTextColor="#888"
                multiline
                numberOfLines={4}
              />
              
              <TouchableOpacity
                style={styles.sendAlertButton}
                onPress={handleSendAlert}
              >
                <Text style={styles.sendAlertButtonText}>Send Alert</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingText: {
    color: '#0F0',
    marginTop: 10,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerButton: {
    padding: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 20,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    marginHorizontal: 5,
  },
  activeTabButton: {
    borderBottomWidth: 2,
    borderBottomColor: '#0F0',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#888',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#0F0',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
  },
  metricsCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  metricsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricItem: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  chartCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  chart: {
    borderRadius: 16,
  },
  actionsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  actionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionButton: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 5,
  },
  userCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  userHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: '#888',
  },
  userStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  userStatusText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000',
  },
  userDetails: {
    marginBottom: 15,
  },
  userDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  userDetailLabel: {
    fontSize: 14,
    color: '#888',
  },
  userDetailValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  userActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  userActionButton: {
    backgroundColor: '#007bff',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 6,
  },
  userActionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  tradingCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  tradingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  tradingMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  tradingMetric: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  tradingMetricLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  tradingMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  topSymbolsCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  topSymbolsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  symbolRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  symbolName: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  symbolVolume: {
    fontSize: 16,
    color: '#0F0',
    fontWeight: 'bold',
  },
  userTradingCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  userTradingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  userTradingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  userTradingId: {
    fontSize: 14,
    color: '#fff',
    flex: 1,
  },
  userTradingTrades: {
    fontSize: 14,
    color: '#888',
    marginRight: 10,
  },
  userTradingVolume: {
    fontSize: 14,
    color: '#0F0',
    fontWeight: 'bold',
  },
  systemCard: {
    backgroundColor: '#1a1a1a',
    margin: 20,
    borderRadius: 12,
    padding: 20,
  },
  systemTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  systemMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  systemMetric: {
    width: '48%',
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  systemMetricLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  systemMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  servicesCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  servicesTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  serviceList: {
    marginTop: 10,
  },
  serviceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  serviceName: {
    fontSize: 16,
    color: '#fff',
    flex: 1,
  },
  serviceStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 15,
  },
  serviceIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  serviceStatusText: {
    fontSize: 14,
    color: '#888',
  },
  serviceAction: {
    backgroundColor: '#007bff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  serviceActionText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  logCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 20,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  logLevel: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  logLevelText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000',
  },
  logTimestamp: {
    fontSize: 12,
    color: '#888',
  },
  logMessage: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 10,
  },
  logDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  logSource: {
    fontSize: 12,
    color: '#888',
  },
  logUserId: {
    fontSize: 12,
    color: '#888',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#1a1a1a',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  modalCloseButton: {
    padding: 5,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalUserCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 20,
  },
  modalUserName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  modalUserEmail: {
    fontSize: 16,
    color: '#888',
    marginBottom: 5,
  },
  modalUserStatus: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 5,
  },
  modalUserCreated: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 5,
  },
  modalUserLastLogin: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 5,
  },
  modalUserTrades: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 5,
  },
  modalUserVolume: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 5,
  },
  modalUserValue: {
    fontSize: 16,
    color: '#fff',
  },
  alertForm: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 20,
  },
  alertFormLabel: {
    fontSize: 16,
    color: '#ccc',
    marginBottom: 8,
  },
  alertLevelSelector: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  alertLevelButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#333',
  },
  activeAlertLevelButton: {
    backgroundColor: '#007bff',
  },
  alertLevelButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '500',
  },
  activeAlertLevelButtonText: {
    fontWeight: 'bold',
  },
  alertMessageInput: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#555',
    marginBottom: 20,
    textAlignVertical: 'top',
  },
  sendAlertButton: {
    backgroundColor: '#ff4444',
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  sendAlertButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default AdminDashboard;
