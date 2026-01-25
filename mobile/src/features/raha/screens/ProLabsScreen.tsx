import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import StrategyStoreScreen from './StrategyStoreScreen';
import BacktestViewerScreen from './BacktestViewerScreen';
import logger from '../../../utils/logger';

type ProLabsView = 'menu' | 'strategies' | 'backtests';

/**
 * Pro/Labs - Advanced RAHA Controls
 * 
 * This is where power users go to:
 * - Browse and configure strategies
 * - View backtest results
 * - Access full RAHA controls
 * 
 * Philosophy: Hidden by default, discoverable by those who want it.
 */
interface ProLabsScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
}

export default function ProLabsScreen({ navigateTo }: ProLabsScreenProps = {}) {
  const [currentView, setCurrentView] = useState<ProLabsView>('menu');
  
  useEffect(() => {
    // Screen mounted - initialization complete
  }, []);

  // Custom navigation helper (not using React Navigation)
  const navigateBack = () => {
    if (navigateTo) {
      navigateTo('home');
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('home');
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('home');
      }
    }
  };

  const navigateToStrategyDetail = (strategyId: string) => {
    if (navigateTo) {
      navigateTo('raha-strategy-detail', { strategyId });
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('raha-strategy-detail', { strategyId });
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('raha-strategy-detail');
      }
    }
  };

  if (currentView === 'strategies') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setCurrentView('menu')}
          >
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Store</Text>
          <View style={{ width: 24 }} />
        </View>
        <StrategyStoreScreen 
          navigateTo={(screen: string, params?: any) => {
            if (screen === 'raha-strategy-detail') {
              navigateToStrategyDetail(params?.strategyId || '');
            } else {
              // Use custom navigation
              if (navigateTo) {
                navigateTo(screen, params);
              } else if (typeof window !== 'undefined') {
                if ((window as any).__navigateToGlobal) {
                  (window as any).__navigateToGlobal(screen, params);
                }
              }
            }
          }}
        />
      </SafeAreaView>
    );
  }

  if (currentView === 'backtests') {
    return (
      <BacktestViewerScreen 
        navigateTo={navigateTo}
        onBack={() => setCurrentView('menu')}
      />
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={navigateBack}
          >
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle}>Pro / Labs</Text>
            <Text style={styles.headerSubtitle}>Advanced RAHA Controls</Text>
          </View>
          <View style={{ width: 24 }} />
        </View>

        {/* Warning Banner */}
        <View style={styles.warningBanner}>
          <Icon name="alert-triangle" size={20} color="#F59E0B" />
          <View style={styles.warningContent}>
            <Text style={styles.warningTitle}>Advanced Features</Text>
            <Text style={styles.warningText}>
              These tools are for experienced traders. The default Whisper screen is designed for simplicity.
            </Text>
          </View>
        </View>

        {/* Main Menu */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>RAHA Tools</Text>

          {/* Strategy Store */}
          <TouchableOpacity
            style={styles.menuCard}
            onPress={() => setCurrentView('strategies')}
            activeOpacity={0.7}
          >
            <View style={styles.menuCardIcon}>
              <Icon name="layers" size={24} color="#3B82F6" />
            </View>
            <View style={styles.menuCardContent}>
              <Text style={styles.menuCardTitle}>Strategy Store</Text>
              <Text style={styles.menuCardDescription}>
                Browse, enable, and configure RAHA trading strategies
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#9CA3AF" />
          </TouchableOpacity>

          {/* Backtest Viewer */}
          <TouchableOpacity
            style={styles.menuCard}
            onPress={() => setCurrentView('backtests')}
            activeOpacity={0.7}
          >
            <View style={styles.menuCardIcon}>
              <Icon name="bar-chart-2" size={24} color="#10B981" />
            </View>
            <View style={styles.menuCardContent}>
              <Text style={styles.menuCardTitle}>Backtest Results</Text>
              <Text style={styles.menuCardDescription}>
                View equity curves, metrics, and performance analysis
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#9CA3AF" />
          </TouchableOpacity>
        </View>

        {/* Advanced Features Section */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Advanced Features</Text>

          {/* Strategy Builder */}
          <TouchableOpacity
            style={styles.menuCard}
            onPress={() => {
              logger.log('🔍 Strategy Builder pressed');
              if (navigateTo) {
                logger.log('🔍 Using navigateTo function to go to strategy-builder');
                navigateTo('strategy-builder');
              } else if (typeof window !== 'undefined') {
                if ((window as any).__navigateToGlobal) {
                  logger.log('🔍 Using window.__navigateToGlobal to go to strategy-builder');
                  (window as any).__navigateToGlobal('strategy-builder');
                } else if ((window as any).__setCurrentScreen) {
                  logger.log('🔍 Using window.__setCurrentScreen to go to strategy-builder');
                  (window as any).__setCurrentScreen('strategy-builder');
                }
              } else {
                logger.error('🔍 No navigation method available!');
              }
            }}
            activeOpacity={0.7}
          >
            <View style={[styles.menuCardIcon, { backgroundColor: '#FEF3C7' }]}>
              <Icon name="sliders" size={24} color="#F59E0B" />
            </View>
            <View style={styles.menuCardContent}>
              <Text style={styles.menuCardTitle}>Strategy Builder</Text>
              <Text style={styles.menuCardDescription}>
                Create and test your own trading strategies
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#9CA3AF" />
          </TouchableOpacity>

          {/* ML Model Training */}
          <TouchableOpacity
            style={styles.menuCard}
            onPress={() => {
              logger.log('🔍 ML Model Training pressed');
              if (navigateTo) {
                logger.log('🔍 Using navigateTo function to go to ml-training');
                navigateTo('ml-training');
              } else if (typeof window !== 'undefined') {
                if ((window as any).__navigateToGlobal) {
                  logger.log('🔍 Using window.__navigateToGlobal to go to ml-training');
                  (window as any).__navigateToGlobal('ml-training');
                } else if ((window as any).__setCurrentScreen) {
                  logger.log('🔍 Using window.__setCurrentScreen to go to ml-training');
                  (window as any).__setCurrentScreen('ml-training');
                }
              } else {
                logger.error('🔍 No navigation method available!');
              }
            }}
            activeOpacity={0.7}
          >
            <View style={[styles.menuCardIcon, { backgroundColor: '#DBEAFE' }]}>
              <Icon name="cpu" size={24} color="#3B82F6" />
            </View>
            <View style={styles.menuCardContent}>
              <Text style={styles.menuCardTitle}>ML Model Training</Text>
              <Text style={styles.menuCardDescription}>
                Train custom models on your trading history
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#9CA3AF" />
          </TouchableOpacity>

          {/* Multi-Strategy Blending */}
          <TouchableOpacity
            style={styles.menuCard}
            onPress={() => {
              logger.log('🔍 Multi-Strategy Blending pressed');
              if (navigateTo) {
                logger.log('🔍 Using navigateTo function to go to strategy-blend-builder');
                navigateTo('strategy-blend-builder');
              } else if (typeof window !== 'undefined') {
                if ((window as any).__navigateToGlobal) {
                  logger.log('🔍 Using window.__navigateToGlobal to go to strategy-blend-builder');
                  (window as any).__navigateToGlobal('strategy-blend-builder');
                } else if ((window as any).__setCurrentScreen) {
                  logger.log('🔍 Using window.__setCurrentScreen to go to strategy-blend-builder');
                  (window as any).__setCurrentScreen('strategy-blend-builder');
                }
              } else {
                logger.error('🔍 No navigation method available!');
              }
            }}
            activeOpacity={0.7}
          >
            <View style={[styles.menuCardIcon, { backgroundColor: '#E0E7FF' }]}>
              <Icon name="git-branch" size={24} color="#6366F1" />
            </View>
            <View style={styles.menuCardContent}>
              <Text style={styles.menuCardTitle}>Multi-Strategy Blending</Text>
              <Text style={styles.menuCardDescription}>
                Combine multiple strategies with custom weights
              </Text>
            </View>
            <Icon name="chevron-right" size={20} color="#9CA3AF" />
          </TouchableOpacity>
        </View>

        {/* Info Section */}
        <View style={styles.infoSection}>
          <Icon name="info" size={20} color="#6B7280" />
          <Text style={styles.infoText}>
            Pro/Labs features are experimental and may change. For the simplest experience, use The Whisper screen from Day Trading.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 32,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  warningBanner: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginTop: 20,
    padding: 16,
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
    gap: 12,
  },
  warningContent: {
    flex: 1,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 4,
  },
  warningText: {
    fontSize: 13,
    color: '#92400E',
    lineHeight: 18,
  },
  menuSection: {
    marginTop: 32,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  menuCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  menuCardDisabled: {
    opacity: 0.6,
  },
  menuCardIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  menuCardIconDisabled: {
    backgroundColor: '#F9FAFB',
  },
  menuCardContent: {
    flex: 1,
  },
  menuCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  menuCardTitleDisabled: {
    color: '#9CA3AF',
  },
  menuCardDescription: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 18,
  },
  comingSoonBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  comingSoonText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#6B7280',
  },
  infoSection: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginTop: 32,
    padding: 16,
    backgroundColor: '#F0F9FF',
    borderRadius: 12,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#0369A1',
    lineHeight: 18,
  },
});

