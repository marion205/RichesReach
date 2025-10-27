/**
 * Real-Time Notifications System
 * Push notifications, alerts, and voice announcements
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Animated,
  Dimensions,
  Alert,
  Vibration,
} from 'react-native';
import { useVoice } from '../contexts/VoiceContext';
import { useMutation, useSubscription } from '@apollo/client';
import { gql } from '@apollo/client';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Subscriptions
const NOTIFICATION_SUBSCRIPTION = gql`
  subscription NotificationSubscription {
    notificationAdded {
      id
      type
      title
      message
      priority
      timestamp
      data
    }
  }
`;

const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($id: ID!) {
    markNotificationRead(id: $id) {
      success
    }
  }
`;

interface Notification {
  id: string;
  type: 'trade' | 'price' | 'education' | 'social' | 'system';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
  data?: any;
  read: boolean;
}

interface NotificationSystemProps {
  userId: string;
  onNotificationPress?: (notification: Notification) => void;
}

export const RealTimeNotificationSystem: React.FC<NotificationSystemProps> = ({
  userId,
  onNotificationPress,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  
  const { speak } = useVoice();
  const slideAnim = useRef(new Animated.Value(-screenWidth)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  const [markNotificationRead] = useMutation(MARK_NOTIFICATION_READ);

  // Subscribe to real-time notifications
  const { data: subscriptionData } = useSubscription(NOTIFICATION_SUBSCRIPTION);

  useEffect(() => {
    if (subscriptionData?.notificationAdded) {
      const newNotification = subscriptionData.notificationAdded;
      addNotification(newNotification);
    }
  }, [subscriptionData]);

  useEffect(() => {
    // Load initial notifications
    loadNotifications();
    
    // Set up periodic checks for connection
    const connectionInterval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(connectionInterval);
  }, []);

  useEffect(() => {
    if (showNotifications) {
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.spring(slideAnim, {
        toValue: -screenWidth,
        useNativeDriver: true,
      }).start();
    }
  }, [showNotifications]);

  const loadNotifications = async () => {
    try {
      // Mock notifications - replace with real API call
      const mockNotifications: Notification[] = [
        {
          id: '1',
          type: 'trade',
          title: 'Trade Executed',
          message: 'BUY 100 AAPL @ $150.25',
          priority: 'high',
          timestamp: new Date().toISOString(),
          read: false,
        },
        {
          id: '2',
          type: 'price',
          title: 'Price Alert',
          message: 'AAPL reached $152.00 target',
          priority: 'medium',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          read: false,
        },
        {
          id: '3',
          type: 'education',
          title: 'Lesson Complete',
          message: 'You earned 50 XP in Options Basics',
          priority: 'low',
          timestamp: new Date(Date.now() - 600000).toISOString(),
          read: true,
        },
      ];
      
      setNotifications(mockNotifications);
      setUnreadCount(mockNotifications.filter(n => !n.read).length);
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  };

  const addNotification = (notification: Notification) => {
    setNotifications(prev => [notification, ...prev]);
    
    if (!notification.read) {
      setUnreadCount(prev => prev + 1);
    }

    // Handle different notification types
    handleNotificationType(notification);
  };

  const handleNotificationType = (notification: Notification) => {
    switch (notification.type) {
      case 'trade':
        handleTradeNotification(notification);
        break;
      case 'price':
        handlePriceNotification(notification);
        break;
      case 'education':
        handleEducationNotification(notification);
        break;
      case 'social':
        handleSocialNotification(notification);
        break;
      case 'system':
        handleSystemNotification(notification);
        break;
    }
  };

  const handleTradeNotification = (notification: Notification) => {
    // Vibrate for trade notifications
    Vibration.vibrate([0, 200, 100, 200]);
    
    // Speak the notification
    speak(`Trade executed: ${notification.message}`, {
      voice: 'Nova',
      rate: 0.9,
    });

    // Show priority-based styling
    if (notification.priority === 'urgent') {
      Alert.alert('Urgent Trade Alert', notification.message);
    }
  };

  const handlePriceNotification = (notification: Notification) => {
    // Gentle vibration for price alerts
    Vibration.vibrate([0, 100]);
    
    speak(`Price alert: ${notification.message}`, {
      voice: 'Shimmer',
      rate: 1.0,
    });
  };

  const handleEducationNotification = (notification: Notification) => {
    // Encouraging voice for education
    speak(`Great job! ${notification.message}`, {
      voice: 'Shimmer',
      rate: 1.1,
    });
  };

  const handleSocialNotification = (notification: Notification) => {
    speak(`Social update: ${notification.message}`, {
      voice: 'Nova',
      rate: 1.0,
    });
  };

  const handleSystemNotification = (notification: Notification) => {
    if (notification.priority === 'urgent') {
      Alert.alert('System Alert', notification.message);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await markNotificationRead({ variables: { id: notificationId } });
      
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, read: true } : n
        )
      );
      
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const checkConnection = () => {
    // Mock connection check - replace with real implementation
    setIsConnected(true);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'trade': return '📈';
      case 'price': return '💰';
      case 'education': return '🎓';
      case 'social': return '👥';
      case 'system': return '⚙️';
      default: return '📢';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#ff4444';
      case 'high': return '#ff8800';
      case 'medium': return '#ffbb00';
      case 'low': return '#00ff88';
      default: return '#888';
    }
  };

  const toggleNotifications = () => {
    setShowNotifications(!showNotifications);
  };

  return (
    <View style={styles.container}>
      {/* Notification Bell */}
      <TouchableOpacity
        style={styles.notificationBell}
        onPress={toggleNotifications}
      >
        <Text style={styles.bellIcon}>🔔</Text>
        {unreadCount > 0 && (
          <Animated.View
            style={[
              styles.badge,
              {
                transform: [{ scale: pulseAnim }],
              },
            ]}
          >
            <Text style={styles.badgeText}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </Text>
          </Animated.View>
        )}
      </TouchableOpacity>

      {/* Notifications Panel */}
      <Animated.View
        style={[
          styles.notificationsPanel,
          {
            transform: [{ translateX: slideAnim }],
          },
        ]}
      >
        {/* Header */}
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Notifications</Text>
          <View style={styles.headerActions}>
            <TouchableOpacity
              style={styles.clearButton}
              onPress={clearAllNotifications}
            >
              <Text style={styles.clearButtonText}>Clear All</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowNotifications(false)}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Connection Status */}
        <View style={styles.connectionStatus}>
          <View style={[
            styles.statusIndicator,
            { backgroundColor: isConnected ? '#00ff88' : '#ff4444' }
          ]} />
          <Text style={styles.statusText}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
        </View>

        {/* Notifications List */}
        <ScrollView style={styles.notificationsList}>
          {notifications.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No notifications</Text>
            </View>
          ) : (
            notifications.map((notification) => (
              <TouchableOpacity
                key={notification.id}
                style={[
                  styles.notificationItem,
                  !notification.read && styles.unreadNotification,
                ]}
                onPress={() => {
                  markAsRead(notification.id);
                  onNotificationPress?.(notification);
                }}
              >
                <View style={styles.notificationContent}>
                  <View style={styles.notificationHeader}>
                    <Text style={styles.notificationIcon}>
                      {getNotificationIcon(notification.type)}
                    </Text>
                    <Text style={styles.notificationTitle}>
                      {notification.title}
                    </Text>
                    <View style={[
                      styles.priorityIndicator,
                      { backgroundColor: getPriorityColor(notification.priority) }
                    ]} />
                  </View>
                  
                  <Text style={styles.notificationMessage}>
                    {notification.message}
                  </Text>
                  
                  <Text style={styles.notificationTime}>
                    {new Date(notification.timestamp).toLocaleTimeString()}
                  </Text>
                </View>
                
                {!notification.read && (
                  <View style={styles.unreadDot} />
                )}
              </TouchableOpacity>
            ))
          )}
        </ScrollView>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickActionButton}>
            <Text style={styles.quickActionIcon}>🔕</Text>
            <Text style={styles.quickActionText}>Mute</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickActionButton}>
            <Text style={styles.quickActionIcon}>⚙️</Text>
            <Text style={styles.quickActionText}>Settings</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickActionButton}>
            <Text style={styles.quickActionIcon}>📱</Text>
            <Text style={styles.quickActionText}>Push</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </View>
  );
};

// Styles
const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  notificationBell: {
    position: 'relative',
    backgroundColor: '#1a1a1a',
    borderRadius: 25,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bellIcon: {
    fontSize: 20,
  },
  badge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#ff4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  notificationsPanel: {
    position: 'absolute',
    top: 60,
    right: 0,
    width: screenWidth * 0.9,
    height: screenWidth * 1.2,
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  panelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  panelTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  clearButton: {
    backgroundColor: '#333',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 10,
  },
  clearButtonText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  closeButton: {
    backgroundColor: '#333',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: 'bold',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#0a0a0a',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 12,
    color: '#888',
  },
  notificationsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#888',
    fontStyle: 'italic',
  },
  notificationItem: {
    flexDirection: 'row',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    position: 'relative',
  },
  unreadNotification: {
    backgroundColor: '#0a0a0a',
  },
  notificationContent: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  notificationIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  notificationTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  priorityIndicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  notificationMessage: {
    fontSize: 13,
    color: '#ccc',
    marginBottom: 5,
    lineHeight: 18,
  },
  notificationTime: {
    fontSize: 11,
    color: '#888',
  },
  unreadDot: {
    position: 'absolute',
    right: 0,
    top: 20,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007bff',
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  quickActionButton: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  quickActionIcon: {
    fontSize: 20,
    marginBottom: 5,
  },
  quickActionText: {
    fontSize: 12,
    color: '#888',
  },
});

export default RealTimeNotificationSystem;
