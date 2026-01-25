/**
 * SharedOrb Component
 * Multi-user synchronized Constellation Orb for family sharing
 * Shows real-time gestures and updates from family members
 * Optimized for fast loading and performance
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Vibration,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import * as Haptics from 'expo-haptics';
import ConstellationOrb from '../../portfolio/components/ConstellationOrb';
import { familySharingService, FamilyMember, OrbSyncEvent } from '../services/FamilySharingService';
import { MoneySnapshot } from '../../portfolio/services/MoneySnapshotService';
import { getFamilyWebSocketService, OrbSyncEvent as WSEvent } from '../services/FamilyWebSocketService';
import logger from '../../../utils/logger';

interface SharedOrbProps {
  snapshot: MoneySnapshot;
  familyGroupId: string;
  currentUser: FamilyMember;
  onGesture?: (gesture: string) => void;
}

export const SharedOrb: React.FC<SharedOrbProps> = ({
  snapshot,
  familyGroupId,
  currentUser,
  onGesture,
}) => {
  const [activeMembers, setActiveMembers] = useState<FamilyMember[]>([]);
  const [recentEvents, setRecentEvents] = useState<OrbSyncEvent[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const syncIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const wsServiceRef = useRef(getFamilyWebSocketService());
  const wsUnsubscribeRef = useRef<(() => void) | null>(null);
  const lastSyncRef = useRef<number>(0);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const syncOrbStateRef = useRef<(() => Promise<void>) | null>(null);
  const fetchRecentEventsRef = useRef<(() => Promise<void>) | null>(null);
  const triggerPulseAnimationRef = useRef<(() => void) | null>(null);

  // Memoize filtered members for performance
  const otherMembers = useMemo(() => {
    return activeMembers.filter(m => m.id !== currentUser.id);
  }, [activeMembers, currentUser.id]);

  // Initialize WebSocket connection (optimized - only once)
  useEffect(() => {
    const wsService = wsServiceRef.current;
    let mounted = true;

    const connectWebSocket = async () => {
      try {
        await wsService.connect(familyGroupId);
        
        // Subscribe to events
        const unsubscribe = wsService.onEvent((event: WSEvent) => {
          if (!mounted) return;
          
          handleWebSocketEvent(event);
        });
        
        wsUnsubscribeRef.current = unsubscribe;
        
        // Check connection status
        const checkConnection = setInterval(() => {
          if (mounted) {
            setWsConnected(wsService.isReady);
          }
        }, 1000);
        
        return () => {
          clearInterval(checkConnection);
        };
      } catch (error) {
        logger.error('[SharedOrb] WebSocket connection failed:', error);
        // Fallback to polling will be handled by useEffect when wsConnected is false
      }
    };

    connectWebSocket();

    return () => {
      mounted = false;
      if (wsUnsubscribeRef.current) {
        wsUnsubscribeRef.current();
      }
      wsService.disconnect();
    };
  }, [familyGroupId]);

  // Handle WebSocket events
  const handleWebSocketEvent = useCallback((event: WSEvent) => {
    switch (event.type) {
      case 'orb_sync':
        if (event.userId !== currentUser.userId && event.netWorth !== undefined) {
          // Someone else updated the orb
          if (triggerPulseAnimationRef.current) triggerPulseAnimationRef.current();
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        }
        break;
        
      case 'gesture':
        if (event.userId !== currentUser.userId && event.gesture) {
          // Someone else performed a gesture
          if (triggerPulseAnimationRef.current) triggerPulseAnimationRef.current();
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          
          // Add to recent events
          setRecentEvents(prev => [
            {
              type: 'gesture',
              userId: event.userId || '',
              userName: event.userName || 'Family Member',
              timestamp: new Date().toISOString(),
              data: { gesture: event.gesture },
            },
            ...prev.slice(0, 4), // Keep last 5
          ]);
        }
        break;
        
      case 'initial_state':
        // Initial state received
        break;
    }
  }, [currentUser.userId]);

  // Fetch active family members (optimized - memoized)
  const loadFamilyMembers = useCallback(async () => {
    try {
      const group = await familySharingService.getFamilyGroup();
      if (group) {
        // Store all members, filtering happens in useMemo
        setActiveMembers(group.members);
      }
    } catch (error) {
      logger.error('[SharedOrb] Failed to load members:', error);
    }
  }, []);

  // Load members on mount (only once)
  useEffect(() => {
    loadFamilyMembers();
  }, [loadFamilyMembers]);

  // Fallback polling sync (only if WebSocket not connected)
  useEffect(() => {
    if (wsConnected) {
      // Clear any polling intervals when WebSocket is connected
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
        syncIntervalRef.current = null;
      }
      return;
    }
    
    // Start polling fallback
    syncIntervalRef.current = setInterval(async () => {
      if (syncOrbStateRef.current) await syncOrbStateRef.current();
      if (fetchRecentEventsRef.current) await fetchRecentEventsRef.current();
    }, 5000);

    // Initial sync
    if (syncOrbStateRef.current) syncOrbStateRef.current();
    if (fetchRecentEventsRef.current) fetchRecentEventsRef.current();
    
    return () => {
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
        syncIntervalRef.current = null;
      }
    };
  }, [wsConnected]);

  // Debounced sync to avoid too many updates
  const syncOrbState = useCallback(async () => {
    const now = Date.now();
    if (now - lastSyncRef.current < 1000) {
      // Debounce: only sync once per second
      return;
    }
    lastSyncRef.current = now;

    try {
      setIsSyncing(true);
      
      // Use WebSocket if available (faster)
      if (wsConnected && wsServiceRef.current.isReady) {
        wsServiceRef.current.syncOrbState(snapshot.netWorth);
      } else {
        // Fallback to HTTP
        await familySharingService.syncOrbState({
          netWorth: snapshot.netWorth,
        });
      }
    } catch (error) {
      logger.warn('[SharedOrb] Sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [snapshot.netWorth, wsConnected]);
  syncOrbStateRef.current = syncOrbState;

  const fetchRecentEvents = useCallback(async () => {
    try {
      const events = await familySharingService.getOrbSyncEvents();
      setRecentEvents(events.slice(0, 5)); // Show last 5 events
      
      // Trigger haptic feedback for new events
      if (events.length > 0) {
        const latestEvent = events[0];
        if (latestEvent.userId !== currentUser.userId) {
          // Someone else interacted with the orb
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          if (triggerPulseAnimationRef.current) triggerPulseAnimationRef.current();
        }
      }
    } catch (error) {
      logger.warn('[SharedOrb] Failed to fetch events:', error);
    }
  }, [currentUser.userId]);
  fetchRecentEventsRef.current = fetchRecentEvents;

  const triggerPulseAnimation = useCallback(() => {
    Animated.sequence([
      Animated.timing(pulseAnim, {
        toValue: 1.1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(pulseAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [pulseAnim]);
  triggerPulseAnimationRef.current = triggerPulseAnimation;

  // Optimized gesture handler with WebSocket
  const handleGesture = useCallback(async (gesture: string) => {
    // Send gesture via WebSocket (instant) or HTTP (fallback)
    if (wsConnected && wsServiceRef.current.isReady) {
      wsServiceRef.current.sendGesture(gesture);
      wsServiceRef.current.syncOrbState(snapshot.netWorth);
    } else {
      // Fallback to HTTP
      await familySharingService.syncOrbState({
        netWorth: snapshot.netWorth,
        gesture,
      });
    }

    // Call parent handler immediately (don't wait for sync)
    if (onGesture) {
      onGesture(gesture);
    }
  }, [snapshot.netWorth, wsConnected, onGesture]);

  const pulseStyle = {
    transform: [{ scale: pulseAnim }],
  };

  return (
    <View style={styles.container}>
      {/* Family Members Indicator */}
      {otherMembers.length > 0 && (
        <View style={styles.membersBar}>
          <View style={styles.membersList}>
            <Text style={styles.membersLabel}>Family viewing:</Text>
            {otherMembers.map((member) => (
              <View key={member.id} style={styles.memberBadge}>
                <View style={styles.memberAvatar}>
                  <Text style={styles.memberInitial}>
                    {member.name.charAt(0).toUpperCase()}
                  </Text>
                </View>
                <Text style={styles.memberName}>{member.name}</Text>
              </View>
            ))}
          </View>
          {isSyncing && (
            <View style={styles.syncIndicator}>
              <Icon name="refresh-cw" size={12} color="#007AFF" />
            </View>
          )}
        </View>
      )}

      {/* Shared Orb */}
      <Animated.View style={[styles.orbContainer, pulseStyle]}>
        <ConstellationOrb
          snapshot={snapshot}
          onTap={() => handleGesture('tap')}
          onDoubleTap={() => handleGesture('double_tap')}
          onLongPress={() => handleGesture('long_press')}
          onSwipeLeft={() => handleGesture('swipe_left')}
          onSwipeRight={() => handleGesture('swipe_right')}
          onPinch={() => handleGesture('pinch')}
        />
      </Animated.View>

      {/* Recent Activity Feed */}
      {recentEvents.length > 0 && (
        <View style={styles.activityFeed}>
          <Text style={styles.activityTitle}>Recent Activity</Text>
          {recentEvents.map((event, index) => (
            <View key={index} style={styles.activityItem}>
              <View style={styles.activityAvatar}>
                <Text style={styles.activityInitial}>
                  {event.userName.charAt(0).toUpperCase()}
                </Text>
              </View>
              <View style={styles.activityContent}>
                <Text style={styles.activityText}>
                  <Text style={styles.activityName}>{event.userName}</Text>
                  {' '}
                  {event.type === 'gesture' 
                    ? `performed ${event.data?.gesture || 'an action'}`
                    : event.type === 'update'
                    ? 'updated the orb'
                    : 'viewed the orb'}
                </Text>
                <Text style={styles.activityTime}>
                  {new Date(event.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Sync Status */}
      <View style={styles.syncStatus}>
        <Icon 
          name={wsConnected ? "wifi" : isSyncing ? "refresh-cw" : "check-circle"} 
          size={16} 
          color={wsConnected ? "#34C759" : isSyncing ? "#007AFF" : "#8E8E93"} 
        />
        <Text style={styles.syncStatusText}>
          {wsConnected ? 'Real-time' : isSyncing ? 'Syncing...' : 'Synced'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  membersBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#F0F8FF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  membersList: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  membersLabel: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '600',
  },
  memberBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  memberAvatar: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  memberInitial: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  memberName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  syncIndicator: {
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  orbContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityFeed: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  activityAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#007AFF20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityInitial: {
    fontSize: 14,
    fontWeight: '700',
    color: '#007AFF',
  },
  activityContent: {
    flex: 1,
  },
  activityText: {
    fontSize: 13,
    color: '#1C1C1E',
    lineHeight: 18,
  },
  activityName: {
    fontWeight: '700',
    color: '#1C1C1E',
  },
  activityTime: {
    fontSize: 11,
    color: '#8E8E93',
    marginTop: 2,
  },
  syncStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    backgroundColor: '#F8F9FA',
  },
  syncStatusText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '600',
  },
});

export default SharedOrb;

