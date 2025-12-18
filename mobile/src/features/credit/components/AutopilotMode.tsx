/**
 * Autopilot Mode - AI selects 1-2 actions per week and tracks completion
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { AutopilotStatus, CreditAction } from '../types/CreditTypes';

interface AutopilotModeProps {
  status: AutopilotStatus;
  availableActions: CreditAction[];
  onToggle: (enabled: boolean) => void;
  onCompleteAction: (actionId: string) => void;
  onSelectActions: (actions: CreditAction[]) => void;
}

export const AutopilotMode: React.FC<AutopilotModeProps> = ({
  status,
  availableActions,
  onToggle,
  onCompleteAction,
  onSelectActions,
}) => {
  const [showHistory, setShowHistory] = useState(false);

  const handleToggle = () => {
    onToggle(!status.enabled);
    if (!status.enabled) {
      // Auto-select 1-2 actions when enabling
      const topActions = availableActions
        .filter(a => !a.completed)
        .sort((a, b) => (b.projectedScoreGain || 0) - (a.projectedScoreGain || 0))
        .slice(0, 2);
      onSelectActions(topActions);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 100) return '#34C759';
    if (progress >= 50) return '#FF9500';
    return '#8E8E93';
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon 
            name={status.enabled ? "zap" : "zap-off"} 
            size={24} 
            color={status.enabled ? "#FFD700" : "#8E8E93"} 
          />
          <View style={styles.headerText}>
            <Text style={styles.title}>Autopilot Mode</Text>
            <Text style={styles.subtitle}>
              {status.enabled 
                ? `Week of ${formatDate(status.currentWeek.weekStart)}`
                : 'AI selects 1-2 actions per week'}
            </Text>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.toggle, status.enabled && styles.toggleActive]}
          onPress={handleToggle}
        >
          <View style={[styles.toggleCircle, status.enabled && styles.toggleCircleActive]} />
        </TouchableOpacity>
      </View>

      {status.enabled && (
        <>
          {/* Current Week Progress */}
          <View style={styles.progressBox}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressLabel}>This Week's Progress</Text>
              <Text style={[styles.progressValue, { color: getProgressColor(status.currentWeek.progress) }]}>
                {status.currentWeek.progress}%
              </Text>
            </View>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill, 
                  { 
                    width: `${status.currentWeek.progress}%`,
                    backgroundColor: getProgressColor(status.currentWeek.progress)
                  }
                ]} 
              />
            </View>
            {status.streak > 0 && (
              <View style={styles.streakBox}>
                <Icon name="flame" size={16} color="#FF9500" />
                <Text style={styles.streakText}>
                  {status.streak} week streak! 🔥
                </Text>
              </View>
            )}
          </View>

          {/* Selected Actions */}
          <View style={styles.actionsBox}>
            <Text style={styles.sectionTitle}>This Week's Actions</Text>
            {status.currentWeek.selectedActions.map((action) => {
              const isCompleted = status.currentWeek.completedActions.includes(action.id);
              return (
                <TouchableOpacity
                  key={action.id}
                  style={[styles.actionCard, isCompleted && styles.actionCardCompleted]}
                  onPress={() => !isCompleted && onCompleteAction(action.id)}
                >
                  <View style={styles.actionLeft}>
                    <Icon 
                      name={isCompleted ? "check-circle" : "circle"} 
                      size={20} 
                      color={isCompleted ? "#34C759" : "#8E8E93"} 
                    />
                    <View style={styles.actionContent}>
                      <Text style={styles.actionTitle}>{action.title}</Text>
                      <Text style={styles.actionDescription}>{action.description}</Text>
                      {action.projectedScoreGain && (
                        <Text style={styles.actionGain}>
                          +{action.projectedScoreGain} points
                        </Text>
                      )}
                    </View>
                  </View>
                  {isCompleted && (
                    <Icon name="check" size={20} color="#34C759" />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Weekly Summary */}
          {status.currentWeek.summary && (
            <View style={styles.summaryBox}>
              <Text style={styles.summaryTitle}>AI Summary</Text>
              <Text style={styles.summaryText}>{status.currentWeek.summary}</Text>
            </View>
          )}

          {/* History Button */}
          {status.weeklyHistory.length > 0 && (
            <TouchableOpacity
              style={styles.historyButton}
              onPress={() => setShowHistory(true)}
            >
              <Icon name="clock" size={16} color="#007AFF" />
              <Text style={styles.historyButtonText}>
                View {status.weeklyHistory.length} past weeks
              </Text>
            </TouchableOpacity>
          )}

          {/* Stats */}
          <View style={styles.statsBox}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{status.totalActionsCompleted}</Text>
              <Text style={styles.statLabel}>Actions Completed</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{status.streak}</Text>
              <Text style={styles.statLabel}>Week Streak</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>
                {status.weeklyHistory.filter(w => w.progress === 100).length}
              </Text>
              <Text style={styles.statLabel}>Perfect Weeks</Text>
            </View>
          </View>
        </>
      )}

      {/* History Modal */}
      <Modal
        visible={showHistory}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowHistory(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Weekly History</Text>
            <TouchableOpacity onPress={() => setShowHistory(false)}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            {status.weeklyHistory.map((week, index) => (
              <View key={index} style={styles.historyCard}>
                <Text style={styles.historyWeek}>
                  Week of {formatDate(week.weekStart)}
                </Text>
                <View style={styles.historyProgress}>
                  <View style={styles.historyProgressBar}>
                    <View 
                      style={[
                        styles.historyProgressFill,
                        { width: `${week.progress}%` }
                      ]} 
                    />
                  </View>
                  <Text style={styles.historyProgressText}>{week.progress}%</Text>
                </View>
                <Text style={styles.historyActions}>
                  {week.completedActions.length} of {week.selectedActions.length} actions completed
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  subtitle: {
    fontSize: 13,
    color: '#8E8E93',
    marginTop: 2,
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
    backgroundColor: '#34C759',
  },
  toggleCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start',
  },
  toggleCircleActive: {
    alignSelf: 'flex-end',
  },
  progressBox: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  progressValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  streakBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
  },
  streakText: {
    fontSize: 13,
    color: '#FF9500',
    fontWeight: '600',
  },
  actionsBox: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  actionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  actionCardCompleted: {
    opacity: 0.6,
  },
  actionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  actionDescription: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
  },
  actionGain: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },
  summaryBox: {
    backgroundColor: '#E3F2FD',
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  summaryText: {
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
  historyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 16,
  },
  historyButtonText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  statsBox: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  historyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
  },
  historyWeek: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  historyProgress: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  historyProgressBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
    overflow: 'hidden',
  },
  historyProgressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 3,
  },
  historyProgressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    minWidth: 40,
  },
  historyActions: {
    fontSize: 13,
    color: '#8E8E93',
  },
});

