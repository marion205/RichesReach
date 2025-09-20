import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// Utils
const timeAgo = (iso?: string) => {
  if (!iso) return '';
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  const m = Math.floor(s/60), h = Math.floor(m/60), d = Math.floor(h/24);
  if (d > 0) return `${d}d ago`;
  if (h > 0) return `${h}h ago`;
  if (m > 0) return `${m}m ago`;
  return `${s}s ago`;
};

const TYPE_MAP: Record<string, { color: string; icon: string; label: string }> = {
  price_alert:   { color:'#F59E0B', icon:'trending-up',  label:'Price'   },
  order_filled:  { color:'#16A34A', icon:'check-circle', label:'Filled'  },
  order_cancelled:{color:'#EF4444', icon:'x-circle',     label:'Canceled'},
  news_update:   { color:'#2563EB', icon:'book-open',    label:'News'    },
  system_update: { color:'#6B7280', icon:'settings',     label:'System'  },
  sbloc_opportunity: { color:'#10B981', icon:'trending-up', label:'SBLOC' },
  sbloc_rate_alert: { color:'#3B82F6', icon:'percent', label:'Rate' },
  sbloc_liquidity_reminder: { color:'#8B5CF6', icon:'credit-card', label:'Liquidity' },
  default:       { color:'#2563EB', icon:'bell',         label:'Alert'   },
};

const Chip = ({ text, tint = '#EEF2F7', color = '#111' }:{
  text: string; tint?: string; color?: string
}) => (
  <View style={[styles.chip, { backgroundColor: tint }]}>
    <Text style={[styles.chipText, { color }]} numberOfLines={1}>{text}</Text>
  </View>
);

// GraphQL Queries
const GET_NOTIFICATIONS = gql`
  query GetNotifications {
    notifications {
      id
      title
      message
      type
      isRead
      createdAt
      data
    }
  }
`;

const GET_NOTIFICATION_SETTINGS = gql`
  query GetNotificationSettings {
    notificationSettings {
      priceAlerts
      orderUpdates
      newsUpdates
      systemUpdates
    }
  }
`;

// GraphQL Mutations
const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($notificationId: String!) {
    markNotificationRead(notificationId: $notificationId) {
      success
      message
    }
  }
`;

const MARK_ALL_NOTIFICATIONS_READ = gql`
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead {
      success
      message
    }
  }
`;

const UPDATE_NOTIFICATION_SETTINGS = gql`
  mutation UpdateNotificationSettings($settings: NotificationSettingsInput!) {
    updateNotificationSettings(settings: $settings) {
      success
      message
      settings {
        priceAlerts
        orderUpdates
        newsUpdates
        systemUpdates
      }
    }
  }
`;

const NotificationsScreen = ({ navigateTo }: { navigateTo?: (screen: string) => void }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [filter, setFilter] = useState<'all'|'unread'|'system'|'sbloc'>('all');

  // Queries
  const { 
    data: notificationsData, 
    loading: notificationsLoading, 
    refetch: refetchNotifications 
  } = useQuery(GET_NOTIFICATIONS, { errorPolicy: 'all' });

  const { 
    data: settingsData, 
    loading: settingsLoading,
    refetch: refetchSettings 
  } = useQuery(GET_NOTIFICATION_SETTINGS, { errorPolicy: 'all' });

  // Mutations
  const [markNotificationRead] = useMutation(MARK_NOTIFICATION_READ, {
    onCompleted: (data) => {
      if (data.markNotificationRead.success) {
        refetchNotifications();
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const [markAllNotificationsRead] = useMutation(MARK_ALL_NOTIFICATIONS_READ, {
    onCompleted: (data) => {
      if (data.markAllNotificationsRead.success) {
        refetchNotifications();
        Alert.alert('Success', 'All notifications marked as read');
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const [updateNotificationSettings] = useMutation(UPDATE_NOTIFICATION_SETTINGS, {
    onCompleted: (data) => {
      if (data.updateNotificationSettings.success) {
        refetchSettings();
        Alert.alert('Success', 'Notification settings updated');
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchNotifications(), refetchSettings()]);
    setRefreshing(false);
  };

  const handleMarkAsRead = (notificationId: string) => {
    markNotificationRead({ variables: { notificationId } });
  };

  const handleMarkAllAsRead = () => {
    Alert.alert(
      'Mark All as Read',
      'Are you sure you want to mark all notifications as read?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Mark All', onPress: () => markAllNotificationsRead() }
      ]
    );
  };

  const handleToggleSetting = (setting: string) => {
    const currentSettings = settingsData?.notificationSettings || {};
    const newValue = !currentSettings[setting];
    
    updateNotificationSettings({
      variables: {
        settings: {
          ...currentSettings,
          [setting]: newValue
        }
      }
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'price_alert':
        return 'trending-up';
      case 'order_filled':
        return 'check-circle';
      case 'order_cancelled':
        return 'x-circle';
      case 'news_update':
        return 'newspaper';
      case 'system_update':
        return 'settings';
      default:
        return 'bell';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'price_alert':
        return '#FF9500';
      case 'order_filled':
        return '#34C759';
      case 'order_cancelled':
        return '#FF3B30';
      case 'news_update':
        return '#007AFF';
      case 'system_update':
        return '#8E8E93';
      default:
        return '#007AFF';
    }
  };

  const renderNotification = (n: any) => {
    const meta = TYPE_MAP[n.type] || TYPE_MAP.default;
    const bgTint = `${meta.color}22`; // subtle bg for icon
    const leftAccent = meta.color;

    return (
      <View key={n.id} style={styles.cardWrap}>
        <View style={[styles.cardAccent, { backgroundColor: leftAccent }]} />
        <TouchableOpacity
          activeOpacity={0.9}
          style={[styles.notificationCard, !n.isRead && styles.unreadNotification]}
          onPress={() => handleMarkAsRead(n.id)}
        >
          <View style={styles.rowStart}>
            <View style={[styles.notificationIcon, { backgroundColor: bgTint }]}>
              <Icon name={meta.icon as any} size={18} color={meta.color} />
            </View>
            <View style={{ flex:1 }}>
              <View style={styles.rowBetween}>
                <Text style={[styles.notificationTitle, !n.isRead && styles.unreadText]} numberOfLines={2}>
                  {n.title}
                </Text>
                <Chip text={meta.label} tint="#F3F4F6" color="#6B7280" />
              </View>

              <Text style={styles.notificationMessage} numberOfLines={3}>
                {n.message}
              </Text>

              <View style={styles.rowBetween}>
                <Text style={styles.notificationTime}>{timeAgo(n.createdAt)}</Text>

                {!n.isRead ? (
                  <TouchableOpacity style={styles.markBtn} onPress={() => handleMarkAsRead(n.id)}>
                    <Icon name="check" size={14} color="#fff" />
                    <Text style={styles.markBtnText}>Mark read</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            </View>
          </View>

          {!n.isRead && <View style={styles.unreadDot} />}
        </TouchableOpacity>
      </View>
    );
  };

  const renderSettings = () => {
    if (settingsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading settings...</Text>
        </View>
      );
    }

    const settings = settingsData?.notificationSettings || {};

    return (
      <View style={styles.settingsContainer}>
        <Text style={styles.settingsTitle}>Notification Preferences</Text>
        
        {[
          { key: 'priceAlerts', label: 'Price Alerts', description: 'Get notified when stocks reach your target prices' },
          { key: 'orderUpdates', label: 'Order Updates', description: 'Receive updates about your buy/sell orders' },
          { key: 'newsUpdates', label: 'News Updates', description: 'Stay informed with market news and analysis' },
          { key: 'systemUpdates', label: 'System Updates', description: 'Important app updates and maintenance notices' },
        ].map((setting) => (
          <TouchableOpacity
            key={setting.key}
            style={styles.settingRow}
            onPress={() => handleToggleSetting(setting.key)}
          >
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>{setting.label}</Text>
              <Text style={styles.settingDescription}>{setting.description}</Text>
            </View>
            <View style={[
              styles.toggle,
              settings[setting.key] && styles.toggleActive
            ]}>
              <View style={[
                styles.toggleThumb,
                settings[setting.key] && styles.toggleThumbActive
              ]} />
            </View>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const unreadCount = notificationsData?.notifications?.filter((n: any) => !n.isRead).length || 0;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo?.('profile')} style={styles.backButton}>
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Notifications</Text>
        <View style={styles.headerActions}>
          {unreadCount > 0 && (
            <TouchableOpacity onPress={handleMarkAllAsRead} style={styles.markAllButton}>
              <Text style={styles.markAllText}>Mark All</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity 
            onPress={() => setShowSettings(!showSettings)} 
            style={styles.settingsButton}
          >
            <Icon name="settings" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {showSettings ? (
          renderSettings()
        ) : (
          <>
            {/* Filter / count bar */}
            <View style={styles.filterBar}>
            <View style={styles.filterRow}>
              {(['all','unread','system','sbloc'] as const).map(f => {
                const active = filter === f;
                return (
                  <TouchableOpacity key={f} onPress={() => setFilter(f)}
                    style={[styles.filterPill, active && styles.filterPillActive]}>
                    <Text style={[styles.filterPillText, active && styles.filterPillTextActive]}>
                      {f === 'all' ? 'All' : f === 'unread' ? `Unread (${unreadCount})` : f === 'system' ? 'System' : 'SBLOC'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
              <Text style={styles.countHint}>
                {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
              </Text>
            </View>

            {/* Notifications List */}
            {(() => {
              const allNotifs = notificationsData?.notifications ?? [];
              const filtered = allNotifs.filter((n: any) => {
                if (filter === 'unread') return !n.isRead;
                if (filter === 'system') return n.type === 'system_update';
                if (filter === 'sbloc') return n.type.startsWith('sbloc_');
                return true;
              });

              if (notificationsLoading) {
                return (
                  <View style={styles.skeletonWrap}>
                    {[...Array(4)].map((_,i)=>(
                      <View key={i} style={styles.skelCard}>
                        <View style={styles.skelIcon} />
                        <View style={{ flex:1 }}>
                          <View style={styles.skelLineWide} />
                          <View style={styles.skelLine} />
                        </View>
                      </View>
                    ))}
                  </View>
                );
              }

              if (filtered.length > 0) {
                return filtered.map((n: any) => (
                  <View key={n.id}>
                    {renderNotification(n)}
                  </View>
                ));
              }

              return (
                <View style={styles.emptyState}>
                  <Icon name="bell" size={48} color="#C7C7CC" />
                  <Text style={styles.emptyTitle}>No Notifications</Text>
                  <Text style={styles.emptySubtitle}>You're all set. New alerts will show up here.</Text>
                </View>
              );
            })()}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  markAllButton: {
    marginRight: 12,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  markAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  settingsButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  countContainer: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  countText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  notificationCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  rowStart: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  unreadNotification: {
    backgroundColor: '#F0F8FF',
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  notificationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  unreadText: {
    fontWeight: '700',
  },
  notificationMessage: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 8,
  },
  notificationTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007AFF',
    marginTop: 4,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
  settingsContainer: {
    padding: 20,
  },
  settingsTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 24,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  toggle: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#E5E5EA',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  toggleActive: {
    backgroundColor: '#007AFF',
  },
  toggleThumb: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  toggleThumbActive: {
    transform: [{ translateX: 20 }],
  },
  // Filter bar
  filterBar: { 
    backgroundColor:'#FFF', 
    borderBottomWidth:1, 
    borderBottomColor:'#E5E5EA', 
    paddingHorizontal:20, 
    paddingTop:10, 
    paddingBottom:12 
  },
  filterRow: { 
    flexDirection:'row', 
    gap:8 
  },
  filterPill: { 
    paddingVertical:8, 
    paddingHorizontal:12, 
    borderRadius:18, 
    backgroundColor:'#F2F2F7' 
  },
  filterPillActive: { 
    backgroundColor:'#007AFF' 
  },
  filterPillText: { 
    fontSize:13, 
    color:'#6B7280', 
    fontWeight:'600' 
  },
  filterPillTextActive: { 
    color:'#fff' 
  },
  countHint: { 
    marginTop:8, 
    fontSize:12, 
    color:'#8E8E93', 
    fontWeight:'500' 
  },
  // Card chrome
  cardWrap: { 
    position:'relative' 
  },
  cardAccent: { 
    position:'absolute', 
    left:0, 
    top:0, 
    bottom:0, 
    width:3, 
    borderTopLeftRadius:12, 
    borderBottomLeftRadius:12 
  },
  // Inline action
  markBtn: { 
    flexDirection:'row', 
    alignItems:'center', 
    gap:6, 
    backgroundColor:'#007AFF', 
    paddingHorizontal:10, 
    paddingVertical:6, 
    borderRadius:8 
  },
  markBtnText: { 
    color:'#fff', 
    fontSize:12, 
    fontWeight:'700' 
  },
  // Chip
  chip: { 
    paddingHorizontal:8, 
    paddingVertical:4, 
    borderRadius:999 
  },
  chipText: { 
    fontSize:11, 
    fontWeight:'700' 
  },
  // Skeletons
  skeletonWrap: { 
    padding:16 
  },
  skelCard: { 
    flexDirection:'row', 
    gap:12, 
    padding:14, 
    backgroundColor:'#FFF', 
    borderRadius:12, 
    marginBottom:10 
  },
  skelIcon: { 
    width:36, 
    height:36, 
    borderRadius:18, 
    backgroundColor:'#E5E5EA' 
  },
  skelLineWide: { 
    height:12, 
    backgroundColor:'#E5E5EA', 
    borderRadius:6, 
    width:'60%', 
    marginBottom:8 
  },
  skelLine: { 
    height:10, 
    backgroundColor:'#E5E5EA', 
    borderRadius:6, 
    width:'40%' 
  },
});

export default NotificationsScreen;