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

interface SecurityEvent {
  id: string;
  type: string;
  threatLevel: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: string;
  resolved: boolean;
}

interface BiometricSettings {
  faceId: boolean;
  voiceId: boolean;
  behavioralId: boolean;
  deviceFingerprint: boolean;
  locationTracking: boolean;
}

interface SecurityFortressProps {
  onBiometricSetup: () => void;
  onSecurityEventPress: (event: SecurityEvent) => void;
}

export default function SecurityFortress({ onBiometricSetup, onSecurityEventPress }: SecurityFortressProps) {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<'overview' | 'biometrics' | 'events' | 'compliance'>('overview');
  const [securityScore, setSecurityScore] = useState(85);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [biometricSettings, setBiometricSettings] = useState<BiometricSettings>({
    faceId: true,
    voiceId: false,
    behavioralId: true,
    deviceFingerprint: true,
    locationTracking: false,
  });
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
      const mockSecurityEvents: SecurityEvent[] = [
        {
          id: '1',
          type: 'suspicious_login',
          threatLevel: 'medium',
          description: 'Login attempt from new device in different location',
          timestamp: '2 hours ago',
          resolved: false,
        },
        {
          id: '2',
          type: 'fraud_detection',
          threatLevel: 'high',
          description: 'Unusual trading pattern detected - large position size',
          timestamp: '1 day ago',
          resolved: true,
        },
        {
          id: '3',
          type: 'biometric_failure',
          threatLevel: 'low',
          description: 'Face ID authentication failed multiple times',
          timestamp: '3 days ago',
          resolved: true,
        },
      ];
      
      setSecurityEvents(mockSecurityEvents);
    } catch (error) {
      console.error('Error loading security data:', error);
      Alert.alert('Error', 'Failed to load security data');
    } finally {
      setLoading(false);
    }
  };

  const getSecurityScoreColor = (score: number) => {
    if (score >= 90) return '#34C759';
    if (score >= 70) return '#FF9500';
    if (score >= 50) return '#FF3B30';
    return '#8E8E93';
  };

  const getSecurityScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'low': return '#34C759';
      case 'medium': return '#FF9500';
      case 'high': return '#FF3B30';
      case 'critical': return '#8E8E93';
      default: return '#8E8E93';
    }
  };

  const getThreatLevelIcon = (level: string) => {
    switch (level) {
      case 'low': return '🟢';
      case 'medium': return '🟡';
      case 'high': return '🟠';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  const toggleBiometricSetting = (setting: keyof BiometricSettings) => {
    setBiometricSettings(prev => ({
      ...prev,
      [setting]: !prev[setting]
    }));
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator
          size="large"
          color="#EF4444"
          style={styles.loadingAnimation}
        />
        <Text style={styles.loadingText}>Loading security fortress...</Text>
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
        <Text style={styles.headerTitle}>Security Fortress</Text>
        <Text style={styles.headerSubtitle}>Your digital wealth protection</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        {[
          { id: 'overview', name: 'Overview', icon: '🛡️' },
          { id: 'biometrics', name: 'Biometrics', icon: '👤' },
          { id: 'events', name: 'Events', icon: '🚨' },
          { id: 'compliance', name: 'Compliance', icon: '📋' },
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
            {/* Security Score */}
            <View style={styles.securityScoreCard}>
              <View intensity={20} style={styles.securityScoreBlur}>
                <View style={styles.securityScoreHeader}>
                  <Text style={styles.securityScoreTitle}>Security Score</Text>
                  <Animated.View
                    style={[
                      styles.securityScoreIcon,
                      {
                        transform: [{ scale: pulseAnim }],
                      },
                    ]}
                  >
                    <Text style={styles.securityScoreEmoji}>🛡️</Text>
                  </Animated.View>
                </View>
                
                <View style={styles.securityScoreDisplay}>
                  <Text style={[styles.securityScoreValue, { color: getSecurityScoreColor(securityScore) }]}>
                    {securityScore}
                  </Text>
                  <Text style={styles.securityScoreLabel}>/ 100</Text>
                </View>
                
                <Text style={[styles.securityScoreStatus, { color: getSecurityScoreColor(securityScore) }]}>
                  {getSecurityScoreLabel(securityScore)}
                </Text>
                
                <View style={styles.securityScoreBar}>
                  <View
                    style={[
                      styles.securityScoreFill,
                      {
                        width: `${securityScore}%`,
                        backgroundColor: getSecurityScoreColor(securityScore),
                      },
                    ]}
                  />
                </View>
              </View>
            </View>

            {/* Security Features */}
            <View style={styles.securityFeatures}>
              <Text style={styles.featuresTitle}>Active Security Features</Text>
              {[
                { icon: '👤', name: 'Face ID', enabled: biometricSettings.faceId },
                { icon: '🎤', name: 'Voice ID', enabled: biometricSettings.voiceId },
                { icon: '🧠', name: 'Behavioral Analysis', enabled: biometricSettings.behavioralId },
                { icon: '📱', name: 'Device Fingerprint', enabled: biometricSettings.deviceFingerprint },
                { icon: '📍', name: 'Location Tracking', enabled: biometricSettings.locationTracking },
                { icon: '🔍', name: 'Fraud Detection', enabled: true },
                { icon: '🚨', name: 'Real-time Monitoring', enabled: true },
                { icon: '🔐', name: 'End-to-End Encryption', enabled: true },
              ].map((feature, index) => (
                <View key={index} style={styles.featureItem}>
                  <Text style={styles.featureIcon}>{feature.icon}</Text>
                  <Text style={styles.featureName}>{feature.name}</Text>
                  <View style={[
                    styles.featureStatus,
                    { backgroundColor: feature.enabled ? '#34C759' : '#8E8E93' }
                  ]}>
                    <Text style={styles.featureStatusText}>
                      {feature.enabled ? '✓' : '✗'}
                    </Text>
                  </View>
                </View>
              ))}
            </View>

            {/* Recent Security Events */}
            <View style={styles.recentEvents}>
              <Text style={styles.recentEventsTitle}>Recent Security Events</Text>
              {securityEvents.slice(0, 3).map((event) => (
                <TouchableOpacity
                  key={event.id}
                  style={styles.eventItem}
                  onPress={() => onSecurityEventPress(event)}
                >
                  <Text style={styles.eventIcon}>{getThreatLevelIcon(event.threatLevel)}</Text>
                  <View style={styles.eventInfo}>
                    <Text style={styles.eventDescription} numberOfLines={1}>
                      {event.description}
                    </Text>
                    <Text style={styles.eventTimestamp}>{event.timestamp}</Text>
                  </View>
                  <View style={[
                    styles.eventStatus,
                    { backgroundColor: event.resolved ? '#34C759' : '#FF9500' }
                  ]}>
                    <Text style={styles.eventStatusText}>
                      {event.resolved ? 'Resolved' : 'Active'}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {activeTab === 'biometrics' && (
          <View style={styles.biometricsContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Biometric Authentication</Text>
              <Text style={styles.sectionSubtitle}>
                Secure your account with advanced biometrics
              </Text>
            </View>

            {/* Biometric Settings */}
            {[
              {
                key: 'faceId' as keyof BiometricSettings,
                title: 'Face ID',
                description: 'Use facial recognition for secure authentication',
                icon: '👤',
                color: '#007AFF',
              },
              {
                key: 'voiceId' as keyof BiometricSettings,
                title: 'Voice ID',
                description: 'Voice recognition for hands-free authentication',
                icon: '🎤',
                color: '#34C759',
              },
              {
                key: 'behavioralId' as keyof BiometricSettings,
                title: 'Behavioral Analysis',
                description: 'Learn your typing and interaction patterns',
                icon: '🧠',
                color: '#FF9500',
              },
              {
                key: 'deviceFingerprint' as keyof BiometricSettings,
                title: 'Device Fingerprint',
                description: 'Identify your device for additional security',
                icon: '📱',
                color: '#5856D6',
              },
              {
                key: 'locationTracking' as keyof BiometricSettings,
                title: 'Location Tracking',
                description: 'Monitor login locations for suspicious activity',
                icon: '📍',
                color: '#FF3B30',
              },
            ].map((setting) => (
              <View key={setting.key} style={styles.biometricSetting}>
                <View intensity={20} style={styles.biometricSettingBlur}>
                  <View style={styles.biometricSettingHeader}>
                    <View style={[styles.biometricIcon, { backgroundColor: setting.color }]}>
                      <Text style={styles.biometricIconText}>{setting.icon}</Text>
                    </View>
                    <View style={styles.biometricInfo}>
                      <Text style={styles.biometricTitle}>{setting.title}</Text>
                      <Text style={styles.biometricDescription}>{setting.description}</Text>
                    </View>
                    <Switch
                      value={biometricSettings[setting.key]}
                      onValueChange={() => toggleBiometricSetting(setting.key)}
                      trackColor={{ false: '#767577', true: setting.color }}
                      thumbColor={biometricSettings[setting.key] ? '#fff' : '#f4f3f4'}
                    />
                  </View>
                </View>
              </View>
            ))}

            <TouchableOpacity style={styles.setupBiometricsButton} onPress={onBiometricSetup}>
              <LinearGradient
                colors={['#667eea', '#764ba2']}
                style={styles.setupBiometricsGradient}
              >
                <Text style={styles.setupBiometricsText}>Setup Biometrics</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        )}

        {activeTab === 'events' && (
          <View style={styles.eventsContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Security Events</Text>
              <Text style={styles.sectionSubtitle}>
                Monitor and manage security alerts
              </Text>
            </View>

            {securityEvents.map((event) => (
              <SecurityEventCard
                key={event.id}
                event={event}
                onPress={() => onSecurityEventPress(event)}
                getThreatLevelColor={getThreatLevelColor}
                getThreatLevelIcon={getThreatLevelIcon}
              />
            ))}
          </View>
        )}

        {activeTab === 'compliance' && (
          <View style={styles.complianceContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Compliance Status</Text>
              <Text style={styles.sectionSubtitle}>
                Security standards and certifications
              </Text>
            </View>

            {[
              {
                standard: 'SOC 2 Type II',
                status: 'Compliant',
                score: 95,
                lastAudit: '2024-01-15',
                nextAudit: '2025-01-15',
                color: '#34C759',
              },
              {
                standard: 'PCI DSS',
                status: 'Compliant',
                score: 98,
                lastAudit: '2024-02-01',
                nextAudit: '2025-02-01',
                color: '#34C759',
              },
              {
                standard: 'GDPR',
                status: 'Compliant',
                score: 92,
                lastAudit: '2024-01-20',
                nextAudit: '2025-01-20',
                color: '#34C759',
              },
              {
                standard: 'CCPA',
                status: 'Compliant',
                score: 89,
                lastAudit: '2024-01-25',
                nextAudit: '2025-01-25',
                color: '#34C759',
              },
            ].map((compliance, index) => (
              <ComplianceCard key={index} compliance={compliance} />
            ))}
          </View>
        )}
      </ScrollView>
    </Animated.View>
  );
}

// Security Event Card Component
function SecurityEventCard({ event, onPress, getThreatLevelColor, getThreatLevelIcon }: any) {
  return (
    <TouchableOpacity style={styles.eventCard} onPress={onPress}>
      <View intensity={20} style={styles.eventBlur}>
        <View style={styles.eventHeader}>
          <Text style={styles.eventIcon}>{getThreatLevelIcon(event.threatLevel)}</Text>
          <View style={styles.eventInfo}>
            <Text style={styles.eventType}>{event.type.replace('_', ' ').toUpperCase()}</Text>
            <Text style={styles.eventDescription} numberOfLines={2}>
              {event.description}
            </Text>
          </View>
          <View style={[styles.threatLevelBadge, { backgroundColor: getThreatLevelColor(event.threatLevel) }]}>
            <Text style={styles.threatLevelText}>{event.threatLevel.toUpperCase()}</Text>
          </View>
        </View>

        <View style={styles.eventFooter}>
          <Text style={styles.eventTimestamp}>{event.timestamp}</Text>
          <View style={[styles.eventStatus, { backgroundColor: event.resolved ? '#34C759' : '#FF9500' }]}>
            <Text style={styles.eventStatusText}>
              {event.resolved ? 'Resolved' : 'Active'}
            </Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Compliance Card Component
function ComplianceCard({ compliance }: any) {
  return (
    <View style={styles.complianceCard}>
      <View intensity={20} style={styles.complianceBlur}>
        <View style={styles.complianceHeader}>
          <Text style={styles.complianceStandard}>{compliance.standard}</Text>
          <View style={[styles.complianceStatus, { backgroundColor: compliance.color }]}>
            <Text style={styles.complianceStatusText}>{compliance.status}</Text>
          </View>
        </View>

        <View style={styles.complianceScore}>
          <Text style={styles.complianceScoreValue}>{compliance.score}%</Text>
          <Text style={styles.complianceScoreLabel}>Compliance Score</Text>
        </View>

        <View style={styles.complianceDates}>
          <View style={styles.complianceDate}>
            <Text style={styles.complianceDateLabel}>Last Audit</Text>
            <Text style={styles.complianceDateValue}>{compliance.lastAudit}</Text>
          </View>
          <View style={styles.complianceDate}>
            <Text style={styles.complianceDateLabel}>Next Audit</Text>
            <Text style={styles.complianceDateValue}>{compliance.nextAudit}</Text>
          </View>
        </View>
      </View>
    </View>
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
  securityScoreCard: {
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  securityScoreBlur: {
    padding: 24,
    alignItems: 'center',
  },
  securityScoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 20,
  },
  securityScoreTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  securityScoreIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  securityScoreEmoji: {
    fontSize: 20,
  },
  securityScoreDisplay: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  securityScoreValue: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  securityScoreLabel: {
    fontSize: 24,
    color: '#666',
    marginLeft: 8,
  },
  securityScoreStatus: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 20,
  },
  securityScoreBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  securityScoreFill: {
    height: '100%',
    borderRadius: 4,
  },
  securityFeatures: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  featureName: {
    fontSize: 16,
    color: '#1a1a1a',
    flex: 1,
  },
  featureStatus: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  recentEvents: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  recentEventsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  eventItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  eventIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  eventInfo: {
    flex: 1,
  },
  eventDescription: {
    fontSize: 14,
    color: '#1a1a1a',
  },
  eventTimestamp: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  eventStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  eventStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
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
  biometricsContent: {
    padding: 16,
  },
  biometricSetting: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  biometricSettingBlur: {
    padding: 20,
  },
  biometricSettingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  biometricIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  biometricIconText: {
    fontSize: 24,
  },
  biometricInfo: {
    flex: 1,
  },
  biometricTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  biometricDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  setupBiometricsButton: {
    marginTop: 20,
    borderRadius: 20,
    overflow: 'hidden',
  },
  setupBiometricsGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  setupBiometricsText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  eventsContent: {
    padding: 16,
  },
  eventCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  eventBlur: {
    padding: 20,
  },
  eventHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  eventType: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 4,
  },
  threatLevelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  threatLevelText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  eventFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  complianceContent: {
    padding: 16,
  },
  complianceCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  complianceBlur: {
    padding: 20,
  },
  complianceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  complianceStandard: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  complianceStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  complianceStatusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  complianceScore: {
    alignItems: 'center',
    marginBottom: 16,
  },
  complianceScoreValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  complianceScoreLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  complianceDates: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  complianceDate: {
    alignItems: 'center',
  },
  complianceDateLabel: {
    fontSize: 12,
    color: '#666',
  },
  complianceDateValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginTop: 2,
  },
});
