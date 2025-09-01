import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  Alert,
  Switch,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import newsAlertsService, { NewsAlert, AlertPreference } from '../services/newsAlertsService';

interface NewsAlertsProps {
  visible: boolean;
  onClose: () => void;
}

const NewsAlerts: React.FC<NewsAlertsProps> = ({ visible, onClose }) => {
  const [alerts, setAlerts] = useState<NewsAlert[]>([]);
  const [preferences, setPreferences] = useState<AlertPreference | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);

  useEffect(() => {
    if (visible) {
      loadAlerts();
      loadPreferences();
    }
  }, [visible]);

  const loadAlerts = async () => {
    try {
      const allAlerts = await newsAlertsService.getAlerts();
      setAlerts(allAlerts);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const loadPreferences = async () => {
    try {
      const prefs = newsAlertsService.getPreferences();
      setPreferences(prefs);
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const markAsRead = async (alertId: string) => {
    try {
      await newsAlertsService.markAsRead(alertId);
      await loadAlerts();
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await newsAlertsService.markAllAsRead();
      await loadAlerts();
    } catch (error) {
      console.error('Error marking all alerts as read:', error);
    }
  };

  const deleteAlert = async (alertId: string) => {
    try {
      await newsAlertsService.deleteAlert(alertId);
      await loadAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const clearAllAlerts = () => {
    Alert.alert(
      'Clear All Alerts',
      'Are you sure you want to clear all alerts? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              await newsAlertsService.clearAllAlerts();
              await loadAlerts();
            } catch (error) {
              console.error('Error clearing alerts:', error);
            }
          },
        },
      ]
    );
  };

  const updatePreference = async (key: keyof AlertPreference, value: any) => {
    if (!preferences) return;
    
    try {
      const newPreferences = { ...preferences, [key]: value };
      await newsAlertsService.updatePreferences(newPreferences);
      setPreferences(newPreferences);
    } catch (error) {
      console.error('Error updating preference:', error);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'breaking':
        return 'alert-circle';
      case 'market':
        return 'trending-up';
      case 'personal':
        return 'user';
      default:
        return 'bell';
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'breaking':
        return '#FF3B30';
      case 'market':
        return '#007AFF';
      case 'personal':
        return '#34C759';
      default:
        return '#8E8E93';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '#FF3B30';
      case 'high':
        return '#FF9500';
      case 'medium':
        return '#007AFF';
      case 'low':
        return '#8E8E93';
      default:
        return '#8E8E93';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const unreadCount = alerts.filter(alert => !alert.isRead).length;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Icon name="bell" size={24} color="#34C759" />
            <Text style={styles.headerTitle}>News Alerts</Text>
            {unreadCount > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{unreadCount}</Text>
              </View>
            )}
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity 
              style={styles.preferencesButton}
              onPress={() => setShowPreferences(true)}
            >
              <Icon name="settings" size={20} color="#8E8E93" />
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={markAllAsRead}
            disabled={unreadCount === 0}
          >
            <Icon name="check" size={16} color="#34C759" />
            <Text style={styles.actionButtonText}>Mark All Read</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={clearAllAlerts}
            disabled={alerts.length === 0}
          >
            <Icon name="trash-2" size={16} color="#FF3B30" />
            <Text style={[styles.actionButtonText, styles.clearText]}>Clear All</Text>
          </TouchableOpacity>
        </View>

        {/* Alerts List */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {alerts.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Icon name="bell" size={48} color="#C7C7CC" />
              <Text style={styles.emptyTitle}>No Alerts</Text>
              <Text style={styles.emptySubtitle}>
                You're all caught up! New alerts will appear here when they arrive.
              </Text>
            </View>
          ) : (
            alerts.map((alert) => (
              <View
                key={alert.id}
                style={[
                  styles.alertItem,
                  !alert.isRead && styles.alertItemUnread,
                ]}
              >
                <View style={styles.alertHeader}>
                  <View style={styles.alertType}>
                    <Icon
                      name={getAlertIcon(alert.type)}
                      size={16}
                      color={getAlertColor(alert.type)}
                    />
                    <Text style={styles.alertTypeText}>
                      {alert.type.charAt(0).toUpperCase() + alert.type.slice(1)}
                    </Text>
                  </View>
                  
                  <View style={styles.alertPriority}>
                    <View
                      style={[
                        styles.priorityDot,
                        { backgroundColor: getPriorityColor(alert.priority) },
                      ]}
                    />
                    <Text style={styles.priorityText}>
                      {alert.priority.charAt(0).toUpperCase() + alert.priority.slice(1)}
                    </Text>
                  </View>
                </View>

                <Text style={styles.alertTitle}>{alert.title}</Text>
                <Text style={styles.alertMessage}>{alert.message}</Text>

                <View style={styles.alertFooter}>
                  <Text style={styles.alertTime}>{formatTime(alert.timestamp)}</Text>
                  
                  <View style={styles.alertActions}>
                    {!alert.isRead && (
                      <TouchableOpacity
                        style={styles.alertActionButton}
                        onPress={() => markAsRead(alert.id)}
                      >
                        <Icon name="check" size={14} color="#34C759" />
                        <Text style={styles.alertActionText}>Mark Read</Text>
                      </TouchableOpacity>
                    )}
                    
                    <TouchableOpacity
                      style={styles.alertActionButton}
                      onPress={() => deleteAlert(alert.id)}
                    >
                      <Icon name="trash-2" size={14} color="#FF3B30" />
                      <Text style={[styles.alertActionText, styles.deleteText]}>Delete</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            ))
          )}
        </ScrollView>

        {/* Preferences Modal */}
        <Modal
          visible={showPreferences}
          animationType="slide"
          presentationStyle="pageSheet"
        >
          <View style={styles.container}>
            <View style={styles.header}>
              <Text style={styles.headerTitle}>Alert Preferences</Text>
              <TouchableOpacity onPress={() => setShowPreferences(false)}>
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
              {preferences && (
                <>
                  {/* Enable/Disable Alerts */}
                  <View style={styles.preferenceSection}>
                    <View style={styles.preferenceRow}>
                      <Text style={styles.preferenceLabel}>Enable News Alerts</Text>
                      <Switch
                        value={preferences.enabled}
                        onValueChange={(value) => updatePreference('enabled', value)}
                        trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                        thumbColor="#FFFFFF"
                      />
                    </View>
                  </View>

                  {/* Alert Types */}
                  <View style={styles.preferenceSection}>
                    <Text style={styles.sectionTitle}>Alert Types</Text>
                    {['breaking', 'market', 'personal', 'general'].map((type) => (
                      <View key={type} style={styles.preferenceRow}>
                        <Text style={styles.preferenceLabel}>
                          {type.charAt(0).toUpperCase() + type.slice(1)} Alerts
                        </Text>
                        <Switch
                          value={preferences.types.includes(type)}
                          onValueChange={(value) => {
                            const newTypes = value
                              ? [...preferences.types, type]
                              : preferences.types.filter(t => t !== type);
                            updatePreference('types', newTypes);
                          }}
                          trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                          thumbColor="#FFFFFF"
                        />
                      </View>
                    ))}
                  </View>

                  {/* Priority Levels */}
                  <View style={styles.preferenceSection}>
                    <Text style={styles.sectionTitle}>Priority Levels</Text>
                    {['urgent', 'high', 'medium', 'low'].map((priority) => (
                      <View key={priority} style={styles.preferenceRow}>
                        <Text style={styles.preferenceLabel}>
                          {priority.charAt(0).toUpperCase() + priority.slice(1)} Priority
                        </Text>
                        <Switch
                          value={preferences.priority.includes(priority)}
                          onValueChange={(value) => {
                            const newPriorities = value
                              ? [...preferences.priority, priority]
                              : preferences.priority.filter(p => p !== priority);
                            updatePreference('priority', newPriorities);
                          }}
                          trackColor={{ false: '#E5E5EA', true: '#34C759' }}
                          thumbColor="#FFFFFF"
                        />
                      </View>
                    ))}
                  </View>

                  {/* Frequency */}
                  <View style={styles.preferenceSection}>
                    <Text style={styles.sectionTitle}>Alert Frequency</Text>
                    {['immediate', 'hourly', 'daily'].map((frequency) => (
                      <TouchableOpacity
                        key={frequency}
                        style={[
                          styles.frequencyOption,
                          preferences.frequency === frequency && styles.frequencyOptionActive,
                        ]}
                        onPress={() => updatePreference('frequency', frequency)}
                      >
                        <Text
                          style={[
                            styles.frequencyText,
                            preferences.frequency === frequency && styles.frequencyTextActive,
                          ]}
                        >
                          {frequency.charAt(0).toUpperCase() + frequency.slice(1)}
                        </Text>
                        {preferences.frequency === frequency && (
                          <Icon name="check" size={16} color="#34C759" />
                        )}
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}
            </ScrollView>
          </View>
        </Modal>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  badge: {
    backgroundColor: '#FF3B30',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  preferencesButton: {
    padding: 8,
  },
  closeButton: {
    padding: 8,
  },
  actions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  clearText: {
    color: '#FF3B30',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  alertItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  alertItemUnread: {
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
    backgroundColor: '#F8FFFE',
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  alertType: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  alertTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    textTransform: 'uppercase',
  },
  alertPriority: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    textTransform: 'uppercase',
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  alertMessage: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 12,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  alertActions: {
    flexDirection: 'row',
    gap: 12,
  },
  alertActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  alertActionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#34C759',
  },
  deleteText: {
    color: '#FF3B30',
  },
  preferenceSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  preferenceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  preferenceLabel: {
    fontSize: 16,
    color: '#1C1C1E',
  },
  frequencyOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#F2F2F7',
    marginBottom: 8,
  },
  frequencyOptionActive: {
    backgroundColor: '#34C759',
  },
  frequencyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  frequencyTextActive: {
    color: '#FFFFFF',
  },
});

export default NewsAlerts;
