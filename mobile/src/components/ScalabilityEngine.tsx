import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  Alert,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';

const { width } = Dimensions.get('window');

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  networkLatency: number;
  activeUsers: number;
  responseTime: number;
  errorRate: number;
}

interface MicroserviceStatus {
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  instances: number;
  cpuUsage: number;
  memoryUsage: number;
  lastDeployment: string;
}

interface EdgeNode {
  id: string;
  location: string;
  status: 'active' | 'inactive' | 'maintenance';
  latency: number;
  users: number;
  carbonFootprint: number;
}

interface ScalabilityEngineProps {
  onMicroservicePress: (service: MicroserviceStatus) => void;
  onEdgeNodePress: (node: EdgeNode) => void;
}

export default function ScalabilityEngine({ onMicroservicePress, onEdgeNodePress }: ScalabilityEngineProps) {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'overview' | 'microservices' | 'edge' | 'sustainability'>('overview');
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpuUsage: 45,
    memoryUsage: 62,
    networkLatency: 23,
    activeUsers: 12500,
    responseTime: 89,
    errorRate: 0.02,
  });
  const [microservices, setMicroservices] = useState<MicroserviceStatus[]>([]);
  const [edgeNodes, setEdgeNodes] = useState<EdgeNode[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadData();
    startEntranceAnimation();
    startPulseAnimation();
  }, []);

  const startEntranceAnimation = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Simulate API calls
      const mockMicroservices: MicroserviceStatus[] = [
        {
          name: 'AI Trading Engine',
          status: 'healthy',
          instances: 8,
          cpuUsage: 35,
          memoryUsage: 45,
          lastDeployment: '2 hours ago',
        },
        {
          name: 'User Authentication',
          status: 'healthy',
          instances: 4,
          cpuUsage: 25,
          memoryUsage: 30,
          lastDeployment: '1 day ago',
        },
        {
          name: 'Market Data Service',
          status: 'warning',
          instances: 6,
          cpuUsage: 75,
          memoryUsage: 80,
          lastDeployment: '3 hours ago',
        },
        {
          name: 'Portfolio Analytics',
          status: 'healthy',
          instances: 3,
          cpuUsage: 40,
          memoryUsage: 55,
          lastDeployment: '6 hours ago',
        },
        {
          name: 'Notification Service',
          status: 'critical',
          instances: 2,
          cpuUsage: 90,
          memoryUsage: 95,
          lastDeployment: '1 hour ago',
        },
      ];
      
      const mockEdgeNodes: EdgeNode[] = [
        {
          id: 'us-east-1',
          location: 'Virginia, USA',
          status: 'active',
          latency: 12,
          users: 4500,
          carbonFootprint: 0.8,
        },
        {
          id: 'us-west-2',
          location: 'Oregon, USA',
          status: 'active',
          latency: 15,
          users: 3200,
          carbonFootprint: 0.7,
        },
        {
          id: 'eu-west-1',
          location: 'Ireland',
          status: 'active',
          latency: 18,
          users: 2800,
          carbonFootprint: 0.6,
        },
        {
          id: 'ap-southeast-1',
          location: 'Singapore',
          status: 'maintenance',
          latency: 25,
          users: 2000,
          carbonFootprint: 0.9,
        },
      ];
      
      setMicroservices(mockMicroservices);
      setEdgeNodes(mockEdgeNodes);
    } catch (error) {
      console.error('Error loading scalability data:', error);
      Alert.alert('Error', 'Failed to load scalability data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#34C759';
      case 'warning': return '#FF9500';
      case 'critical': return '#FF3B30';
      case 'active': return '#34C759';
      case 'inactive': return '#8E8E93';
      case 'maintenance': return '#FF9500';
      default: return '#8E8E93';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '🟢';
      case 'warning': return '🟡';
      case 'critical': return '🔴';
      case 'active': return '🟢';
      case 'inactive': return '⚪';
      case 'maintenance': return '🟡';
      default: return '⚪';
    }
  };

  const getUsageColor = (usage: number) => {
    if (usage >= 80) return '#FF3B30';
    if (usage >= 60) return '#FF9500';
    return '#34C759';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#10B981"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading scalability engine...</Text>
      </View>
    );
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Scalability Engine</Text>
        <Text style={styles.headerSubtitle}>Bulletproof infrastructure at scale</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'overview', name: 'Overview', icon: '📊' },
          { id: 'microservices', name: 'Microservices', icon: '🔧' },
          { id: 'edge', name: 'Edge AI', icon: '🌐' },
          { id: 'sustainability', name: 'Sustainability', icon: '🌱' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tabButton,
              activeTab === tab.id && styles.tabButtonActive,
            ]}
            onPress={() => setActiveTab(tab.id as any)}
          >
            <Text style={styles.tabIcon}>{tab.icon}</Text>
            <Text style={[
              styles.tabText,
              activeTab === tab.id && styles.tabTextActive,
            ]}>
              {tab.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'overview' && (
          <View style={styles.overviewContent}>
            {/* System Health */}
            <View style={styles.systemHealthCard}>
              <View intensity={20} style={styles.systemHealthBlur}>
                <View style={styles.systemHealthHeader}>
                  <Text style={styles.systemHealthTitle}>System Health</Text>
                  <Animated.View
                    style={[
                      styles.systemHealthIcon,
                      {
                        transform: [{ scale: pulseAnim }],
                      },
                    ]}
                  >
                    <Text style={styles.systemHealthEmoji}>⚡</Text>
                  </Animated.View>
                </View>
                
                <View style={styles.metricsGrid}>
                  <MetricCard
                    title="CPU Usage"
                    value={`${systemMetrics.cpuUsage}%`}
                    color={getUsageColor(systemMetrics.cpuUsage)}
                    icon="🖥️"
                  />
                  <MetricCard
                    title="Memory"
                    value={`${systemMetrics.memoryUsage}%`}
                    color={getUsageColor(systemMetrics.memoryUsage)}
                    icon="💾"
                  />
                  <MetricCard
                    title="Latency"
                    value={`${systemMetrics.networkLatency}ms`}
                    color={getUsageColor(systemMetrics.networkLatency * 2)}
                    icon="🌐"
                  />
                  <MetricCard
                    title="Active Users"
                    value={systemMetrics.activeUsers.toLocaleString()}
                    color="#34C759"
                    icon="👥"
                  />
                  <MetricCard
                    title="Response Time"
                    value={`${systemMetrics.responseTime}ms`}
                    color={getUsageColor(systemMetrics.responseTime)}
                    icon="⚡"
                  />
                  <MetricCard
                    title="Error Rate"
                    value={`${((systemMetrics.errorRate || 0) * 100).toFixed(2)}%`}
                    color={getUsageColor(systemMetrics.errorRate * 5000)}
                    icon="🚨"
                  />
                </View>
              </View>
            </View>

            {/* Auto-scaling Status */}
            <View style={styles.autoScalingCard}>
              <Text style={styles.autoScalingTitle}>Auto-scaling Status</Text>
              <View style={styles.autoScalingStatus}>
                <View style={[styles.autoScalingIndicator, { backgroundColor: '#34C759' }]} />
                <Text style={styles.autoScalingText}>Active - 23 instances running</Text>
              </View>
              <View style={styles.autoScalingMetrics}>
                <View style={styles.autoScalingMetric}>
                  <Text style={styles.autoScalingMetricLabel}>Min Instances</Text>
                  <Text style={styles.autoScalingMetricValue}>5</Text>
                </View>
                <View style={styles.autoScalingMetric}>
                  <Text style={styles.autoScalingMetricLabel}>Max Instances</Text>
                  <Text style={styles.autoScalingMetricValue}>50</Text>
                </View>
                <View style={styles.autoScalingMetric}>
                  <Text style={styles.autoScalingMetricLabel}>Target CPU</Text>
                  <Text style={styles.autoScalingMetricValue}>70%</Text>
                </View>
              </View>
            </View>

            {/* Performance Trends */}
            <View style={styles.performanceTrendsCard}>
              <Text style={styles.performanceTrendsTitle}>Performance Trends</Text>
              <View style={styles.performanceTrendsChart}>
                <ActivityIndicator
                  size="small"
                  color="#10B981"
                  style={styles.performanceChartAnimation}
                />
              </View>
            </View>
          </View>
        )}

        {activeTab === 'microservices' && (
          <View style={styles.microservicesContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Microservices</Text>
              <Text style={styles.sectionSubtitle}>
                Kubernetes-managed services
              </Text>
            </View>

            {microservices.map((service) => (
              <MicroserviceCard
                key={service.name}
                service={service}
                onPress={() => onMicroservicePress(service)}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
                getUsageColor={getUsageColor}
              />
            ))}
          </View>
        )}

        {activeTab === 'edge' && (
          <View style={styles.edgeContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Edge AI Nodes</Text>
              <Text style={styles.sectionSubtitle}>
                Distributed AI processing
              </Text>
            </View>

            {edgeNodes.map((node) => (
              <EdgeNodeCard
                key={node.id}
                node={node}
                onPress={() => onEdgeNodePress(node)}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            ))}
          </View>
        )}

        {activeTab === 'sustainability' && (
          <View style={styles.sustainabilityContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Sustainability Metrics</Text>
              <Text style={styles.sectionSubtitle}>
                Carbon-neutral hosting
              </Text>
            </View>

            <View style={styles.sustainabilityMetrics}>
              <View style={styles.sustainabilityMetric}>
                <Text style={styles.sustainabilityMetricValue}>0.7</Text>
                <Text style={styles.sustainabilityMetricLabel}>kg CO2/hour</Text>
                <Text style={styles.sustainabilityMetricDescription}>Carbon footprint</Text>
              </View>
              <View style={styles.sustainabilityMetric}>
                <Text style={styles.sustainabilityMetricValue}>85%</Text>
                <Text style={styles.sustainabilityMetricLabel}>Renewable energy</Text>
                <Text style={styles.sustainabilityMetricDescription}>Power source</Text>
              </View>
              <View style={styles.sustainabilityMetric}>
                <Text style={styles.sustainabilityMetricValue}>12</Text>
                <Text style={styles.sustainabilityMetricLabel}>Trees planted</Text>
                <Text style={styles.sustainabilityMetricDescription}>This month</Text>
              </View>
            </View>

            <View style={styles.sustainabilityChart}>
              <ActivityIndicator
                size="small"
                color="#10B981"
                style={styles.sustainabilityChartAnimation}
              />
            </View>
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Metric Card Component
function MetricCard({ title, value, color, icon }: any) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricIcon}>{icon}</Text>
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
    </View>
  );
}

// Microservice Card Component
function MicroserviceCard({ service, onPress, getStatusColor, getStatusIcon, getUsageColor }: any) {
  return (
    <TouchableOpacity style={styles.microserviceCard} onPress={onPress}>
      <View intensity={20} style={styles.microserviceBlur}>
        <View style={styles.microserviceHeader}>
          <Text style={styles.microserviceName}>{service.name}</Text>
          <View style={[styles.microserviceStatus, { backgroundColor: getStatusColor(service.status) }]}>
            <Text style={styles.microserviceStatusText}>{service.status.toUpperCase()}</Text>
          </View>
        </View>

        <View style={styles.microserviceMetrics}>
          <View style={styles.microserviceMetric}>
            <Text style={styles.microserviceMetricLabel}>Instances</Text>
            <Text style={styles.microserviceMetricValue}>{service.instances}</Text>
          </View>
          <View style={styles.microserviceMetric}>
            <Text style={styles.microserviceMetricLabel}>CPU</Text>
            <Text style={[styles.microserviceMetricValue, { color: getUsageColor(service.cpuUsage) }]}>
              {service.cpuUsage}%
            </Text>
          </View>
          <View style={styles.microserviceMetric}>
            <Text style={styles.microserviceMetricLabel}>Memory</Text>
            <Text style={[styles.microserviceMetricValue, { color: getUsageColor(service.memoryUsage) }]}>
              {service.memoryUsage}%
            </Text>
          </View>
        </View>

        <View style={styles.microserviceFooter}>
          <Text style={styles.microserviceDeployment}>Last deployment: {service.lastDeployment}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Edge Node Card Component
function EdgeNodeCard({ node, onPress, getStatusColor, getStatusIcon }: any) {
  return (
    <TouchableOpacity style={styles.edgeNodeCard} onPress={onPress}>
      <View intensity={20} style={styles.edgeNodeBlur}>
        <View style={styles.edgeNodeHeader}>
          <Text style={styles.edgeNodeLocation}>{node.location}</Text>
          <View style={[styles.edgeNodeStatus, { backgroundColor: getStatusColor(node.status) }]}>
            <Text style={styles.edgeNodeStatusText}>{node.status.toUpperCase()}</Text>
          </View>
        </View>

        <View style={styles.edgeNodeMetrics}>
          <View style={styles.edgeNodeMetric}>
            <Text style={styles.edgeNodeMetricLabel}>Latency</Text>
            <Text style={styles.edgeNodeMetricValue}>{node.latency}ms</Text>
          </View>
          <View style={styles.edgeNodeMetric}>
            <Text style={styles.edgeNodeMetricLabel}>Users</Text>
            <Text style={styles.edgeNodeMetricValue}>{node.users.toLocaleString()}</Text>
          </View>
          <View style={styles.edgeNodeMetric}>
            <Text style={styles.edgeNodeMetricLabel}>Carbon</Text>
            <Text style={styles.edgeNodeMetricValue}>{node.carbonFootprint}kg/h</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingAnimation: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabButtonActive: {
    borderBottomColor: '#667eea',
  },
  tabIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#667eea',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  overviewContent: {
    padding: 16,
  },
  systemHealthCard: {
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  systemHealthBlur: {
    padding: 24,
  },
  systemHealthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  systemHealthTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  systemHealthIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  systemHealthEmoji: {
    fontSize: 20,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  metricIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  metricTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  autoScalingCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  autoScalingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  autoScalingStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  autoScalingIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  autoScalingText: {
    fontSize: 16,
    color: '#1a1a1a',
  },
  autoScalingMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  autoScalingMetric: {
    alignItems: 'center',
  },
  autoScalingMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  autoScalingMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  performanceTrendsCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  performanceTrendsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  performanceTrendsChart: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  performanceChartAnimation: {
    width: 300,
    height: 150,
  },
  sectionHeader: {
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  microservicesContent: {
    padding: 16,
  },
  microserviceCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  microserviceBlur: {
    padding: 20,
  },
  microserviceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  microserviceName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  microserviceStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  microserviceStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  microserviceMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  microserviceMetric: {
    alignItems: 'center',
  },
  microserviceMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  microserviceMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  microserviceFooter: {
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  microserviceDeployment: {
    fontSize: 12,
    color: '#666',
  },
  edgeContent: {
    padding: 16,
  },
  edgeNodeCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  edgeNodeBlur: {
    padding: 20,
  },
  edgeNodeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  edgeNodeLocation: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  edgeNodeStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  edgeNodeStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  edgeNodeMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  edgeNodeMetric: {
    alignItems: 'center',
  },
  edgeNodeMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  edgeNodeMetricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  sustainabilityContent: {
    padding: 16,
  },
  sustainabilityMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  sustainabilityMetric: {
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    flex: 1,
    marginHorizontal: 4,
  },
  sustainabilityMetricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#34C759',
  },
  sustainabilityMetricLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  sustainabilityMetricDescription: {
    fontSize: 10,
    color: '#999',
    marginTop: 2,
  },
  sustainabilityChart: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sustainabilityChartAnimation: {
    width: 250,
    height: 150,
  },
});
