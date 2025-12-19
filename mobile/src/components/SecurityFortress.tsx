import React, { useState, useEffect, useRef, useCallback } from 'react';
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
import { useQuery, useMutation } from '@apollo/client';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import { useTheme } from '../theme/PersonalizedThemes';
import {
  SECURITY_EVENTS,
  BIOMETRIC_SETTINGS,
  COMPLIANCE_STATUSES,
  SECURITY_SCORE,
  UPDATE_BIOMETRIC_SETTINGS,
  RESOLVE_SECURITY_EVENT,
} from '../graphql/queries_corrected';
import { connectSignal } from '../realtime/signal';
import { useAuth } from '../contexts/AuthContext';
import { SecurityInsights } from './SecurityInsights';
import { SecurityGamification } from './SecurityGamification';

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
  onNavigate?: (screen: string, params?: any) => void;
  onBiometricSetup?: () => void;
  onSecurityEventPress?: (event: SecurityEvent) => void;
}

export default function SecurityFortress({ onNavigate, onBiometricSetup, onSecurityEventPress }: SecurityFortressProps) {
  const handleBiometricSetup = onBiometricSetup || (() => {});
  const handleSecurityEventPress = onSecurityEventPress || (() => {});
  const theme = useTheme();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'insights' | 'gamification' | 'biometrics' | 'events' | 'compliance'>('overview');
  const [securityScore, setSecurityScore] = useState(85);
  const [socket, setSocket] = useState<any>(null);
  const refetchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  // GraphQL Queries
  const { data: eventsData, loading: eventsLoading, refetch: refetchEvents } = useQuery(SECURITY_EVENTS, {
    variables: { limit: 50, resolved: null },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  const { data: biometricData, loading: biometricLoading, refetch: refetchBiometric } = useQuery(BIOMETRIC_SETTINGS, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  const { data: complianceData, loading: complianceLoading } = useQuery(COMPLIANCE_STATUSES, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  const { data: scoreData, loading: scoreLoading, refetch: refetchScore } = useQuery(SECURITY_SCORE, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });
  
  // GraphQL Mutations
  const [updateBiometricSettings] = useMutation(UPDATE_BIOMETRIC_SETTINGS, {
    refetchQueries: [{ query: BIOMETRIC_SETTINGS }, { query: SECURITY_SCORE }],
  });
  
  const [resolveSecurityEvent] = useMutation(RESOLVE_SECURITY_EVENT, {
    refetchQueries: [{ query: SECURITY_EVENTS }, { query: SECURITY_SCORE }],
  });
  
  const loading = eventsLoading || biometricLoading || complianceLoading || scoreLoading;
  
  // Transform GraphQL data to component state
  const securityEvents: SecurityEvent[] = eventsData?.securityEvents?.map((e: any) => ({
    id: e.id,
    type: e.eventType,
    threatLevel: e.threatLevel,
    description: e.description,
    timestamp: e.timestamp || e.createdAt,
    resolved: e.resolved,
  })) || [];
  
  const biometricSettings: BiometricSettings = biometricData?.biometricSettings ? {
    faceId: biometricData.biometricSettings.faceId || false,
    voiceId: biometricData.biometricSettings.voiceId || false,
    behavioralId: biometricData.biometricSettings.behavioralId || true,
    deviceFingerprint: biometricData.biometricSettings.deviceFingerprint || true,
    locationTracking: biometricData.biometricSettings.locationTracking || false,
  } : {
    faceId: false,
    voiceId: false,
    behavioralId: true,
    deviceFingerprint: true,
    locationTracking: false,
  };
  
  const complianceStatuses = complianceData?.complianceStatuses || [];
  
  useEffect(() => {
    if (scoreData?.securityScore) {
      setSecurityScore(scoreData.securityScore.score || 85);
    }
  }, [scoreData]);
  
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    startEntranceAnimation();
    startPulseAnimation();
  }, []);
  
  // Debounced refetch to prevent hammering the API
  const debouncedRefetch = useCallback(() => {
    // Clear existing timeout
    if (refetchTimeoutRef.current) {
      clearTimeout(refetchTimeoutRef.current);
    }
    
    // Schedule a single refetch after 500ms
    refetchTimeoutRef.current = setTimeout(() => {
      console.log('[SecurityFortress] Debounced refetch triggered');
      refetchEvents();
      refetchScore();
      refetchTimeoutRef.current = null;
    }, 500);
  }, [refetchEvents, refetchScore]);

  // Real-time security event monitoring via WebSocket with resilience
  useEffect(() => {
    if (!user?.id) return;
    
    const setupWebSocket = async () => {
      try {
        const getJwt = async () => {
          // Get JWT token for authentication
          const { getJwt: getJwtToken } = await import('../auth/token');
          return await getJwtToken();
        };
        
        const ws = connectSignal(getJwt);
        let isSubscribed = false;
        
        const subscribe = async () => {
          if (!isSubscribed && ws.connected) {
            try {
              const token = await getJwt();
              ws.emit('subscribe-security-events', { 
                userId: user.id,
                token: token,
              });
              isSubscribed = true;
            } catch (error) {
              console.error('[SecurityFortress] Failed to get token for subscription:', error);
            }
          }
        };
        
        ws.on('connect', () => {
          const correlationId = Math.random().toString(36).substring(7);
          console.log(`[SecurityFortress] [${correlationId}] WebSocket connected`);
          reconnectAttemptsRef.current = 0;
          subscribe();
        });
        
        ws.on('disconnect', () => {
          console.log('[SecurityFortress] WebSocket disconnected');
          isSubscribed = false;
          
          // Auto-reconnect with exponential backoff
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectAttemptsRef.current++;
          console.log(`[SecurityFortress] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          
          setTimeout(() => {
            if (!ws.connected) {
              ws.connect();
            }
          }, delay);
        });
        
        ws.on('connect_error', (error: any) => {
          console.error('[SecurityFortress] WebSocket connection error:', error);
        });
        
        ws.on('security-events-subscribed', (data: any) => {
          console.log(`[SecurityFortress] [${data.correlationId || 'unknown'}] Subscribed to security events:`, data);
        });
        
        ws.on('security-events-error', (data: any) => {
          console.error(`[SecurityFortress] [${data.correlationId || 'unknown'}] Security events error:`, data);
        });
        
        ws.on('security-event-created', (data: any) => {
          const correlationId = data.correlationId || 'unknown';
          console.log(`[SecurityFortress] [${correlationId}] New security event received:`, {
            eventId: data.event?.id,
            userId: data.userId,
            timestamp: new Date().toISOString(),
          });
          // Debounced refetch to prevent multiple rapid refetches
          debouncedRefetch();
        });
        
        ws.on('security-event-resolved', (data: any) => {
          const correlationId = data.correlationId || 'unknown';
          console.log(`[SecurityFortress] [${correlationId}] Security event resolved:`, {
            eventId: data.event?.id,
            userId: data.userId,
            timestamp: new Date().toISOString(),
          });
          // Debounced refetch
          debouncedRefetch();
        });
        
        ws.connect();
        setSocket(ws);
        
        // Fallback polling if WebSocket fails (every 30 seconds)
        const pollInterval = setInterval(() => {
          if (!ws.connected) {
            console.log('[SecurityFortress] WebSocket not connected, using fallback polling');
            refetchEvents();
            refetchScore();
          }
        }, 30000);
        
        return () => {
          clearInterval(pollInterval);
          if (refetchTimeoutRef.current) {
            clearTimeout(refetchTimeoutRef.current);
          }
          if (ws) {
            ws.emit('unsubscribe-security-events', { userId: user.id });
            ws.disconnect();
          }
        };
      } catch (error) {
        console.error('[SecurityFortress] WebSocket setup error:', error);
        // Fallback to polling only
        const pollInterval = setInterval(() => {
          refetchEvents();
          refetchScore();
        }, 30000);
        
        return () => clearInterval(pollInterval);
      }
    };
    
    const cleanup = setupWebSocket();
    
    return () => {
      if (cleanup) {
        cleanup.then(fn => fn && fn());
      }
      if (socket) {
        socket.emit('unsubscribe-security-events', { userId: user?.id });
        socket.disconnect();
      }
    };
  }, [user?.id, debouncedRefetch]);

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

  // Data is loaded via GraphQL queries, no need for separate loadData function

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

  const toggleBiometricSetting = async (setting: keyof BiometricSettings) => {
    try {
      const newValue = !biometricSettings[setting];
      const variables: any = {};
      
      // Map camelCase to GraphQL variable names
      if (setting === 'faceId') variables.faceId = newValue;
      else if (setting === 'voiceId') variables.voiceId = newValue;
      else if (setting === 'behavioralId') variables.behavioralId = newValue;
      else if (setting === 'deviceFingerprint') variables.deviceFingerprint = newValue;
      else if (setting === 'locationTracking') variables.locationTracking = newValue;
      
      await updateBiometricSettings({ variables });
      await refetchBiometric();
      await refetchScore();
    } catch (error) {
      console.error('Error updating biometric setting:', error);
      Alert.alert('Error', 'Failed to update biometric setting');
    }
  };
  
  const handleResolveEvent = async (eventId: string) => {
    try {
      await resolveSecurityEvent({ variables: { eventId } });
      await refetchEvents();
      await refetchScore();
      Alert.alert('Success', 'Security event resolved');
    } catch (error) {
      console.error('Error resolving security event:', error);
      Alert.alert('Error', 'Failed to resolve security event');
    }
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

      {/* Tab Navigation - Scrollable */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.tabNavigationContainer}
        contentContainerStyle={styles.tabNavigationContent}
      >
        {[
          { id: 'overview', name: 'Overview', icon: '🛡️' },
          { id: 'insights', name: 'Insights', icon: '🤖' },
          { id: 'gamification', name: 'Badges', icon: '🏆' },
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
            <Text 
              style={[
                styles.tabText,
                activeTab === tab.id && styles.tabTextActive,
              ]}
              numberOfLines={1}
            >
              {tab.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      {activeTab === 'insights' && (
        <SecurityInsights />
      )}
      
      {activeTab === 'gamification' && (
        <SecurityGamification />
      )}
      
      {activeTab === 'overview' && (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.overviewContent}>
            {/* Security Score */}
            <View style={styles.securityScoreCard}>
              <View style={styles.securityScoreBlur}>
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
                  onPress={() => {
                    if (!event.resolved) {
                      handleResolveEvent(event.id);
                    }
                    handleSecurityEventPress(event);
                  }}
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
        </ScrollView>
      )}

      {activeTab === 'events' && (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.eventsContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Security Events</Text>
              <Text style={styles.sectionSubtitle}>
                Monitor and manage security alerts
              </Text>
            </View>

            {securityEvents.length > 0 ? (
              securityEvents.map((event) => (
                <SecurityEventCard
                  key={event.id}
                  event={event}
                  onPress={() => {
                    if (!event.resolved) {
                      handleResolveEvent(event.id);
                    }
                    onSecurityEventPress(event);
                  }}
                  getThreatLevelColor={getThreatLevelColor}
                  getThreatLevelIcon={getThreatLevelIcon}
                />
              ))
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>No security events</Text>
              </View>
            )}
          </View>
        </ScrollView>
      )}

      {activeTab === 'compliance' && (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.complianceContent}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Compliance Status</Text>
              <Text style={styles.sectionSubtitle}>
                Security standards and certifications
              </Text>
            </View>

            {complianceStatuses.length > 0 ? (
              complianceStatuses.map((compliance: any) => (
                <ComplianceCard 
                  key={compliance.id} 
                  compliance={{
                    standard: compliance.standard,
                    status: compliance.status,
                    score: compliance.score,
                    lastAudit: compliance.lastAudit,
                    nextAudit: compliance.nextAudit,
                    color: compliance.status === 'Compliant' ? '#34C759' : '#FF9500',
                  }} 
                />
              ))
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>No compliance data available</Text>
              </View>
            )}
          </View>
        </ScrollView>
      )}

      {activeTab === 'biometrics' && (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
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
                <View style={styles.biometricSettingBlur}>
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
        </ScrollView>
      )}
    </Animated.View>
  );
}

// Security Event Card Component
function SecurityEventCard({ event, onPress, getThreatLevelColor, getThreatLevelIcon }: any) {
  return (
    <TouchableOpacity style={styles.eventCard} onPress={onPress}>
      <View style={styles.eventBlur}>
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
      <View style={styles.complianceBlur}>
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
  tabNavigationContainer: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    maxHeight: 70,
  },
  tabNavigationContent: {
    paddingVertical: 12,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginHorizontal: 4,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
    minWidth: 90,
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
  emptyState: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});
