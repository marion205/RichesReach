import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import PortfolioCalculator from '../components/PortfolioCalculator';

const GET_MY_WATCHLIST = gql`
  query GetMyWatchlist {
    myWatchlist {
      id
      stock {
        id
        symbol
        companyName
        sector
        beginnerFriendlyScore
      }
      addedAt
      notes
    }
  }
`;

interface PortfolioScreenProps {
  navigateTo?: (screen: string) => void;
}

const PortfolioScreen: React.FC<PortfolioScreenProps> = ({ navigateTo }) => {
  const [refreshing, setRefreshing] = useState(false);

  const { data: watchlistData, loading: watchlistLoading, error: watchlistError, refetch } = useQuery(GET_MY_WATCHLIST);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (error) {
      // Error refreshing portfolio data
    } finally {
      setRefreshing(false);
    }
  };

  if (watchlistLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Icon name="bar-chart-2" size={24} color="#34C759" />
          <Text style={styles.headerTitle}>Portfolio Calculator</Text>
        </View>
        <View style={styles.loadingContainer}>
          <Icon name="refresh-cw" size={32} color="#34C759" />
          <Text style={styles.loadingText}>Loading your portfolio...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (watchlistError) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Icon name="bar-chart-2" size={24} color="#34C759" />
          <Text style={styles.headerTitle}>Portfolio Calculator</Text>
        </View>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF3B30" />
          <Text style={styles.errorTitle}>Error Loading Portfolio</Text>
          <Text style={styles.errorText}>
            Unable to load your watchlist data. Please try again.
          </Text>
          <View style={styles.errorActions}>
            <Text style={styles.errorActionText} onPress={onRefresh}>
              Tap to retry
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  const watchlistItems = watchlistData?.myWatchlist || [];

  if (watchlistItems.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Icon name="bar-chart-2" size={24} color="#34C759" />
          <Text style={styles.headerTitle}>Portfolio Calculator</Text>
        </View>
        <View style={styles.emptyContainer}>
          <Icon name="bar-chart-2" size={64} color="#9CA3AF" />
          <Text style={styles.emptyTitle}>No Stocks in Portfolio</Text>
          <Text style={styles.emptySubtitle}>
            Add stocks to your watchlist first to use the portfolio calculator.
          </Text>
          <View style={styles.emptyActions}>
            <Text 
              style={styles.emptyActionText}
              onPress={() => navigateTo?.('home')}
            >
              Go to Home to add stocks
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Icon name="bar-chart-2" size={24} color="#34C759" />
        <Text style={styles.headerTitle}>Portfolio Calculator</Text>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        <PortfolioCalculator watchlistItems={watchlistItems} />
        
        {/* Additional Portfolio Features */}
        <View style={styles.featuresSection}>
          <Text style={styles.featuresTitle}>Portfolio Features</Text>
          
          <View style={styles.featureCard}>
            <View style={styles.featureHeader}>
              <Icon name="trending-up" size={20} color="#34C759" />
              <Text style={styles.featureTitle}>Real-Time Calculations</Text>
            </View>
            <Text style={styles.featureDescription}>
              See your portfolio value update instantly as you adjust share quantities.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <View style={styles.featureHeader}>
              <Icon name="edit" size={20} color="#34C759" />
              <Text style={styles.featureTitle}>Interactive Input</Text>
            </View>
            <Text style={styles.featureDescription}>
              Input exact share quantities or use quick add buttons for fast adjustments.
            </Text>
          </View>

          <View style={styles.featureCard}>
            <View style={styles.featureHeader}>
              <Icon name="refresh-cw" size={20} color="#34C759" />
              <Text style={styles.featureTitle}>Easy Reset</Text>
            </View>
            <Text style={styles.featureDescription}>
              Reset all share quantities to zero with a single tap.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  errorActions: {
    marginTop: 20,
  },
  errorActionText: {
    fontSize: 16,
    color: '#34C759',
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
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
    marginBottom: 20,
  },
  emptyActions: {
    marginTop: 20,
  },
  emptyActionText: {
    fontSize: 16,
    color: '#34C759',
    fontWeight: '600',
  },
  featuresSection: {
    padding: 20,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  featureCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  featureHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  featureDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
});

export default PortfolioScreen;
