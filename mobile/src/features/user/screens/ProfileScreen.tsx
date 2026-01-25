import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Image,
  SafeAreaView,
  Dimensions,
  Modal,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { gql, useQuery, useMutation, useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JWTAuthService from '../../auth/services/JWTAuthService';
import { GET_MY_PORTFOLIOS } from '../../../portfolioQueries';
import SBLOCCalculator from '../../../components/forms/SBLOCCalculator';
import SblocWidget from '../../../components/forms/SblocWidget';
import SblocCalculatorModal from '../../../components/forms/SblocCalculatorModal';
import { FEATURES } from '../../../config/featureFlags';
import { globalNavigate } from '../../../navigation/NavigationService';
import { PrivacyDashboard } from '../../privacy/components/PrivacyDashboard';
import { useAuth } from '../../../contexts/AuthContext';
import AccountManagementScreen from './AccountManagementScreen';
import LicensingDisclosureScreen from '../../../components/LicensingDisclosureScreen';
import logger from '../../../utils/logger';

// --- Design tokens (light theme) ---
const UI = {
  bg: '#F6F7FB',
  card: '#FFFFFF',
  text: '#111827',
  sub: '#6B7280',
  border: '#E5E7EB',
  accent: '#10B981', // Changed from blue to green
  success: '#10B981',
  warn: '#F59E0B',
  danger: '#EF4444',
  violet: '#6366F1',
  gold: '#FFD700',
  radius: 16,
  space: 16,
};

// tiny utility for shadows that look good on both platforms
const shadow = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.08,
  shadowRadius: 8,
  elevation: 3,
};
const GET_ME = gql`
query GetMe {
me {
id
name
email
profilePic
followersCount
followingCount
isFollowingUser
isFollowedByUser
hasPremiumAccess
subscriptionTier
}
}
`;
const GET_USER_PORTFOLIO = gql`
query GetUserPortfolio($userId: ID!) {
portfolios(userId: $userId) {
id
name
description
isPublic
createdAt
positions {
id
stock {
symbol
companyName
}
shares
entryPrice
currentPrice
positionType
currentValue
}
}
}
`;
const GET_MY_WATCHLIST = gql`
query GetMyWatchlist {
myWatchlist {
id
stock {
symbol
}
notes
targetPrice
addedAt
}
}
`;
const GET_PORTFOLIO_VALUE = gql`
query GetPortfolioValue {
portfolioValue
}
`;
const TOGGLE_FOLLOW = gql`
mutation ToggleFollow($userId: ID!) {
toggleFollow(userId: $userId) {
user {
id
followers_count
following_count
is_following_user
is_followed_by_user
}
following
}
}
`;
type User = {
id: string;
name: string;
email: string;
profilePic?: string;
followersCount: number;
followingCount: number;
isFollowingUser: boolean;
isFollowedByUser: boolean;
};
interface ProfileScreenProps {
navigateTo?: (screen: string, params?: any) => void;
onLogout?: () => void;
}
const { width } = Dimensions.get('window');
const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigateTo, onLogout }) => {
  const navigation = useNavigation<any>();
  const { logout: authLogout } = useAuth();
  const [showSBLOCModal, setShowSBLOCModal] = useState(false);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [showSblocCalculator, setShowSblocCalculator] = useState(false);
  const [showPrivacyDashboard, setShowPrivacyDashboard] = useState(false);
  const [showAccountManagement, setShowAccountManagement] = useState(false);
  const [showLicensingDisclosure, setShowLicensingDisclosure] = useState(false);
  
  // Helper function to navigate - tries React Navigation first, then fallback
  const navigate = (screen: string, params?: any) => {
    logger.log('ProfileScreen: Navigating to', screen, params);
    try {
      // Try direct navigation first
      navigation.navigate(screen as never, params as never);
    } catch (directError) {
      // Fallback to globalNavigate
      try {
        globalNavigate(screen, params);
      } catch (globalError) {
        logger.error('ProfileScreen: Navigation error', globalError);
        // Final fallback to navigateTo prop
        navigateTo?.(screen, params);
      }
    }
  };
  
  // Get Apollo client first
  const client = useApolloClient();
  
  // Non-blocking queries - fetch in background, show UI immediately
  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME, {
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network', // Try cache first, then network
    notifyOnNetworkStatusChange: true,
    returnPartialData: true,
  });
  
  // If query fails with auth error, clear token and trigger login
  useEffect(() => {
    if (meError) {
      const errorMessage = meError.message || '';
      // Check if it's an authentication error
      if (errorMessage.includes('Authentication') || 
          errorMessage.includes('Not authenticated') ||
          errorMessage.includes('401') ||
          errorMessage.includes('Unauthorized')) {
        logger.warn('⚠️ Authentication error in Profile, clearing token');
        // Clear token to trigger login screen
        AsyncStorage.removeItem('token').catch((err) => logger.error('Failed to remove token:', err));
      }
    }
  }, [meError]);

const { data: portfoliosData, loading: portfoliosLoading, error: portfoliosError, refetch: refetchPortfolios } = useQuery(GET_MY_PORTFOLIOS, {
  notifyOnNetworkStatusChange: false,
  fetchPolicy: 'cache-only', // Only use cache initially
  nextFetchPolicy: 'cache-first',
  errorPolicy: 'all',
  returnPartialData: true,
  skip: !meData?.me?.id,
});

// Fetch portfolios in background if cache miss
useEffect(() => {
  if (!portfoliosData && !portfoliosLoading && meData?.me?.id) {
    client.query({ query: GET_MY_PORTFOLIOS, fetchPolicy: 'network-only' }).catch((err) => logger.warn('Failed to fetch portfolios:', err));
  }
}, [portfoliosData, portfoliosLoading, meData, client]);

const { data: watchlistData, loading: watchlistLoading, error: watchlistError } = useQuery(GET_MY_WATCHLIST, {
skip: !meData?.me?.id,
errorPolicy: 'all',
fetchPolicy: 'cache-only', // Only use cache initially
nextFetchPolicy: 'cache-first',
notifyOnNetworkStatusChange: false,
returnPartialData: true,
});

// Fetch watchlist in background if cache miss
useEffect(() => {
  if (!watchlistData && !watchlistLoading && meData?.me?.id) {
    client.query({ query: GET_MY_WATCHLIST, fetchPolicy: 'network-only' }).catch((err) => logger.warn('Failed to fetch watchlist:', err));
  }
}, [watchlistData, watchlistLoading, meData, client]);

  // Show UI immediately - don't wait for queries
  // Always show mock data first, then update when real data arrives
  const [meLoadingTimeout] = useState(true); // Always show UI immediately
  const [portfoliosLoadingTimeout] = useState(true); // Always show UI immediately
  const [watchlistLoadingTimeout] = useState(true); // Always show UI immediately
const [toggleFollow] = useMutation(TOGGLE_FOLLOW);
const [refreshing, setRefreshing] = useState(false);
// Production: Use real data only - no demo user fallbacks
const effectiveMeData = useMemo(() => {
  if (meData?.me) {
    return meData.me;
  }
  // Production: Return null if no data - let UI handle loading/error states
  if (meError) {
    logger.error('❌ Error loading user profile:', meError.message);
  }
  return null;
}, [meData, meError]);

const actualUser: User | null = effectiveMeData ? {
id: effectiveMeData.id,
name: effectiveMeData.name,
email: effectiveMeData.email,
profilePic: effectiveMeData.profilePic,
followersCount: effectiveMeData.followersCount || 0,
followingCount: effectiveMeData.followingCount || 0,
isFollowingUser: effectiveMeData.isFollowingUser || false,
isFollowedByUser: effectiveMeData.isFollowedByUser || false
} : null;

// Production: Use real user or show loading/error state
const user = actualUser;

// Production: Show proper loading states
const effectiveMeLoading = meLoading && !meData;
const effectivePortfoliosLoading = portfoliosLoading && !portfoliosData;
const effectiveWatchlistLoading = watchlistLoading && !watchlistData;
const handleToggleFollow = async () => {
if (!actualUser || !user) {
  Alert.alert('Error', 'Please log in to use this feature.');
  return;
}
try {
await toggleFollow({
variables: { userId: user.id },
});
await client.resetStore();
} catch (error) {
// Failed to toggle follow
Alert.alert('Error', 'Failed to follow/unfollow user. Please try again.');
}
};
const handleRefresh = async () => {
setRefreshing(true);
try {
// Refetch queries with network-only to get fresh data on pull-to-refresh
const refreshQueries = [
client.query({ query: GET_ME, fetchPolicy: 'network-only' }),
client.query({ query: GET_MY_PORTFOLIOS, fetchPolicy: 'network-only' }),
];
if (meData?.me?.id) {
refreshQueries.push(client.query({ query: GET_MY_WATCHLIST, fetchPolicy: 'network-only' }));
}
await Promise.all(refreshQueries);
} catch (error) {
logger.warn('Refresh error:', error);
// Failed to refresh - continue with cached data
} finally {
setRefreshing(false);
}
};
// Get real portfolio value from saved portfolio data - use mock data if loading/timeout
const effectivePortfoliosData = useMemo(() => {
  if (portfoliosData?.myPortfolios) {
    return portfoliosData.myPortfolios;
  }
  // Return mock portfolio data for immediate display
  return {
    totalValue: 0,
    totalPortfolios: 0,
    portfolios: [],
  };
}, [portfoliosData, portfoliosLoadingTimeout, portfoliosError]);

const portfolioValue = effectivePortfoliosData.totalValue || 0;
const investmentGoals = effectivePortfoliosData.totalPortfolios || 0;

// Effective watchlist data
const effectiveWatchlistData = useMemo(() => {
  if (watchlistData?.myWatchlist) {
    return watchlistData.myWatchlist;
  }
  return [];
}, [watchlistData, watchlistLoadingTimeout, watchlistError]);

// Debug logging
logger.log('Portfolio Data Debug:', {
  portfoliosData,
  portfolioValue,
  investmentGoals,
  loading: portfoliosLoading
});

const handleLogout = async () => {
try {
    logger.log('🔴 Logout button pressed');
    
    // Clear Apollo cache
    await client.cache.reset();
    logger.log('✅ ProfileScreen: Apollo cache cleared');
    
    // ✅ ONLY call AuthContext logout - no navigation here
    // The root App will handle rendering LoginScreen based on auth state
    await authLogout();
    logger.log('✅ ProfileScreen: AuthContext logout completed');
    
    // Also call onLogout if provided (for backwards compatibility)
    if (onLogout) {
        await onLogout();
    }
} catch (error) {
    logger.error('❌ ProfileScreen logout error:', error);
    Alert.alert('Error', 'Failed to logout properly. Please try again.');
}
};
// Always render content - never show blocking loading screen
// Mock data ensures user, portfolios, and watchlist are always available
// Handle error state gracefully - use demo user if query fails
if (meError && !meData) {
  logger.warn('ProfileScreen: Error loading user data, using demo user:', meError);
  // Continue rendering with demo user - don't block the UI
}
return (
<SafeAreaView style={styles.container}>
{/* Header */}
<View style={styles.header}>
<View style={styles.headerLeft}>
      <TouchableOpacity onPress={() => {
        try {
          navigation.goBack();
        } catch {
          navigate('home');
        }
      }}>
        <Icon name="arrow-left" size={24} color="#333" />
      </TouchableOpacity>
<Text style={styles.headerTitle}>Profile</Text>
</View>
<View style={styles.headerRight}>
<TouchableOpacity 
  onPress={() => setShowSettingsMenu(!showSettingsMenu)} 
  style={styles.settingsButton}
>
<Icon name="more-vertical" size={20} color="#333" />
</TouchableOpacity>
{showSettingsMenu && (
<View style={styles.settingsDropdown}>
                <TouchableOpacity 
                  style={styles.settingsItem}
                  onPress={() => {
                    setShowSettingsMenu(false);
                    navigate('subscription');
                  }}
                >
                  <Icon name="credit-card" size={16} color="#333" />
                  <Text style={styles.settingsItemText}>Subscription</Text>
                </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            navigate('notification-center');
          }}
        >
          <Icon name="bell" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Notification Center</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            navigate('Invest', { screen: 'premium-analytics', params: { initialTab: 'tax' } }); // Tax tools in Premium Analytics
          }}
        >
          <Icon name="calculator" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Tax Tools</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            navigate('Learn', { screen: 'LearnMain' }); // Learning paths
          }}
        >
          <Icon name="book-open" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Learning</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            setShowPrivacyDashboard(true);
          }}
        >
          <Icon name="shield" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Privacy & Data</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            setShowAccountManagement(true);
          }}
        >
          <Icon name="settings" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Account Settings</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.settingsItem}
          onPress={() => {
            setShowSettingsMenu(false);
            setShowLicensingDisclosure(true);
          }}
        >
          <Icon name="file-text" size={16} color="#333" />
          <Text style={styles.settingsItemText}>Regulatory & Licensing Info</Text>
        </TouchableOpacity>
<TouchableOpacity 
  style={[styles.settingsItem, styles.logoutItem]}
  onPress={() => {
    setShowSettingsMenu(false);
    handleLogout();
  }}
>
<Icon name="power" size={16} color="#ff4757" />
<Text style={[styles.settingsItemText, styles.logoutText]}>Logout</Text>
</TouchableOpacity>
</View>
)}
</View>
</View>
<ScrollView 
style={styles.content}
refreshControl={
<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
}
showsVerticalScrollIndicator={false}
>
{/* Profile Hero */}
<View style={styles.heroWrap}>
<View style={styles.heroTop} />

{effectiveMeLoading ? (
  <View style={[styles.heroCard, shadow]}>
    <Text style={styles.heroName}>Loading...</Text>
  </View>
) : user ? (
<View style={[styles.heroCard, shadow]}>
<TouchableOpacity style={styles.avatarWrap} activeOpacity={0.85} onPress={() => navigateTo?.('stock')}>
{user.profilePic ? (
<Image source={{ uri: user.profilePic }} style={styles.avatarImg} />
) : (
<View style={styles.avatarFallback}>
<Text style={styles.avatarFallbackTxt}>{user.name.charAt(0).toUpperCase()}</Text>
</View>
)}
<View style={styles.avatarRing} />
</TouchableOpacity>

<Text style={styles.heroName}>{user.name}</Text>
<Text style={styles.heroEmail}>{user.email}</Text>
<Text style={styles.heroSince}>Member since {new Date().getFullYear()}</Text>

<View style={styles.pillsRow}>
<View style={styles.pill}>
<Icon name="users" size={14} color={UI.accent} />
<Text style={styles.pillTxt}>{user.followersCount} Followers</Text>
</View>
<View style={styles.pill}>
<Icon name="user-check" size={14} color={UI.violet} />
<Text style={styles.pillTxt}>{user.followingCount} Following</Text>
</View>
{meData?.me?.hasPremiumAccess && (
<View style={[styles.pill, { borderColor: UI.gold, backgroundColor: '#FFF8E1' }]}>
<Icon name="star" size={14} color={UI.gold} />
<Text style={[styles.pillTxt, { color: '#B8860B' }]}>Premium</Text>
</View>
)}
</View>
</View>
) : (
  <View style={[styles.heroCard, shadow]}>
    <Text style={styles.heroName}>
      {meLoading ? 'Loading Profile...' : 'Authentication Required'}
    </Text>
    <Text style={styles.heroEmail}>
      {meLoading 
        ? 'Please wait...' 
        : meError?.message?.includes('Authentication') || meError?.message?.includes('Not authenticated')
          ? 'Please log in to view your profile'
          : meError?.message || 'Please try again'}
    </Text>
    {!meLoading && meError && (
      <TouchableOpacity 
        style={[styles.ctaBtn, { marginTop: 12 }]} 
        onPress={async () => {
          // Clear token and trigger login
          await AsyncStorage.removeItem('token');
          // App will automatically show login screen
        }}
      >
        <Text style={styles.ctaBtnTxt}>Go to Login</Text>
      </TouchableOpacity>
    )}
  </View>
)}
</View>
{/* Actions */}
<View style={styles.sectionCard}>
<Text style={styles.sectionTitle}>Actions</Text>

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('Invest', { screen: 'Stocks' })}>
          <View style={[styles.rowIcon, { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' }]}>
            <Icon name="edit" size={16} color={UI.success} />
          </View>
          <Text style={styles.rowText}>Manage Stocks</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => {
          Alert.alert('News Preferences', 'News preferences feature coming soon!');
        }}>
          <View style={[styles.rowIcon, { backgroundColor: '#F0F9FF', borderColor: '#BAE6FD' }]}>
            <Icon name="settings" size={16} color={UI.accent} />
          </View>
          <Text style={styles.rowText}>News Preferences</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('Community')}>
          <View style={[styles.rowIcon, { backgroundColor: '#FFF7ED', borderColor: '#FED7AA' }]}>
            <Icon name="message-circle" size={16} color={UI.warn} />
          </View>
          <Text style={styles.rowText}>Discussion Hub</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => {
          // Navigate to onboarding/investment profile screen
          navigate('onboarding');
        }}>
          <View style={[styles.rowIcon, { backgroundColor: '#F5F3FF', borderColor: '#DDD6FE' }]}>
            <Icon name="user-plus" size={16} color={UI.violet} />
          </View>
<Text style={styles.rowText}>Update Investment Profile</Text>
<Icon name="chevron-right" size={18} color="#CBD5E1" />
</TouchableOpacity>

<TouchableOpacity style={styles.rowItem} onPress={() => navigate('Invest', { screen: 'premium-analytics' })}>
<View style={[styles.rowIcon, { backgroundColor: '#FFF8E1', borderColor: '#FFE58F' }]}>
<Icon name="star" size={16} color={UI.gold} />
</View>
<Text style={[styles.rowText, { color: '#B8860B' }]}>Premium Analytics</Text>
<Icon name="chevron-right" size={18} color={UI.gold} />
</TouchableOpacity>

<TouchableOpacity style={styles.rowItem} onPress={() => navigate('bank-accounts')}>
<View style={[styles.rowIcon, { backgroundColor: '#F0F8FF', borderColor: '#BAE6FD' }]}>
<Icon name="credit-card" size={16} color={UI.accent} />
</View>
<Text style={styles.rowText}>Bank Accounts</Text>
<Icon name="chevron-right" size={18} color="#CBD5E1" />
</TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('notification-center')}>
          <View style={[styles.rowIcon, { backgroundColor: '#FFF7ED', borderColor: '#FED7AA' }]}>
            <Icon name="bell" size={16} color={UI.warn} />
          </View>
          <Text style={styles.rowText}>Notification Center</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('Invest', { screen: 'DayTrading' })}>
          <View style={[styles.rowIcon, { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' }]}>
            <Icon name="trending-up" size={16} color={UI.success} />
          </View>
          <Text style={styles.rowText}>Trading</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        {FEATURES.THEME_SETTINGS_ENABLED && (
        <TouchableOpacity style={styles.rowItem} onPress={() => {
          Alert.alert('Theme Settings', 'Theme settings feature coming soon!');
        }}>
          <View style={[styles.rowIcon, { backgroundColor: '#F5F3FF', borderColor: '#DDD6FE' }]}>
            <Icon name="color-palette" size={16} color={UI.violet} />
          </View>
          <Text style={styles.rowText}>Theme Settings</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('security-fortress')}>
          <View style={[styles.rowIcon, { backgroundColor: '#FEF2F2', borderColor: '#FECACA' }]}>
            <Icon name="shield" size={16} color={UI.danger} />
          </View>
          <Text style={styles.rowText}>Security Fortress</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.rowItem} onPress={() => navigate('viral-growth')}>
          <View style={[styles.rowIcon, { backgroundColor: '#FEF3C7', borderColor: '#FDE68A' }]}>
            <Icon name="trending-up" size={16} color="#F59E0B" />
          </View>
          <Text style={styles.rowText}>Viral Growth System</Text>
          <Icon name="chevron-right" size={18} color="#CBD5E1" />
        </TouchableOpacity>
</View>
{/* ---- Overview card ---- */}
<View style={styles.sectionCard}>
  <View style={styles.sectionHeader}>
    <View style={styles.sectionHeaderLeft}>
      <Text style={styles.sectionEyebrow}>Profile</Text>
      <Text style={styles.sectionTitle}>Overview</Text>
    </View>

    {/* tiny helper action; swap handler if you like */}
    <TouchableOpacity onPress={() => navigateTo?.('portfolio-management')} hitSlop={{top:8,bottom:8,left:8,right:8}}>
      <View style={styles.sectionAction}>
        <Icon name="arrow-right" size={14} color="#007AFF" />
        <Text style={styles.sectionActionText}>Manage</Text>
      </View>
    </TouchableOpacity>
  </View>

  {/* SBLOC Borrowing Power */}
  <View style={{ marginBottom: 12 }}>
    <SblocWidget
      equity={portfolioValue || 0}
      apr={8.5}
      ltv={50}
      eligibleEquity={portfolioValue || 0}
      loading={effectivePortfoliosLoading}
      onOpenCalculator={() => setShowSblocCalculator(true)}
      onLearnMore={() => {
        Alert.alert(
          'SBLOC Information',
          'A Securities-Based Line of Credit lets you borrow against your investment portfolio without selling stocks. You can typically borrow up to 50% of your eligible securities value at competitive rates.\n\nThis provides liquidity while keeping your investments growing and potentially avoiding capital gains taxes.',
          [
            { text: 'Learn More', onPress: () => navigateTo?.('learning-paths') },
            { text: 'OK' }
          ]
        );
      }}
    />
  </View>

  {/* Tiles (snap-scrolling) */}
  <ScrollView
    horizontal
    showsHorizontalScrollIndicator={false}
    contentContainerStyle={styles.tileScrollContent}
    snapToAlignment="start"
    decelerationRate="fast"
    snapToInterval={168}               // tile width + gap (adjust if you change width)
  >
    {/* Portfolio Value */}
    <TouchableOpacity
      onPress={() => navigateTo?.('portfolio-management')}
      activeOpacity={0.85}
      style={[styles.tile, styles.shadow]}
      disabled={effectivePortfoliosLoading || effectiveWatchlistLoading}
    >
      <View style={[styles.tileIcon, { backgroundColor:'#ECFDF5', borderColor:'#A7F3D0' }]}>
        <Icon name="trending-up" size={18} color="#10B981" />
      </View>

      <Text style={styles.tileLabel}>Portfolio Value</Text>

      {(effectivePortfoliosLoading || effectiveWatchlistLoading) ? (
        <View style={styles.skeletonLine} />
      ) : (
        <Text style={[styles.tileValue, { color:'#0F766E' }]}>
          ${portfolioValue && portfolioValue > 0 ? portfolioValue.toLocaleString() : '0.00'}
        </Text>
      )}

      <View style={styles.tileFooterRow}>
        <Text style={styles.tileHint}>Updated today</Text>
        <Icon name="chevron-right" size={16} color="#C7CED6" />
      </View>
    </TouchableOpacity>

    {/* Portfolios count / goals */}
    <TouchableOpacity
      onPress={() => navigateTo?.('portfolio-management')}
      activeOpacity={0.85}
      style={[styles.tile, styles.shadow]}
      disabled={effectivePortfoliosLoading}
    >
      <View style={[styles.tileIcon, { backgroundColor:'#EEF2FF', borderColor:'#C7D2FE' }]}>
        <Icon name="crosshair" size={18} color="#6366F1" />
      </View>

      <Text style={styles.tileLabel}>Portfolios</Text>

      {effectivePortfoliosLoading ? (
        <View style={styles.skeletonLine} />
      ) : (
        <View style={styles.badgeRow}>
          <View style={[styles.badge, { backgroundColor:'#EEF2FF' }]}>
            <Text style={[styles.badgeText, { color:'#6366F1' }]}>
              {typeof investmentGoals === 'number' ? `${investmentGoals}` : `${investmentGoals}`}
            </Text>
          </View>
          <Text style={styles.tileHint}>active</Text>
        </View>
      )}

      <View style={styles.tileFooterRow}>
        <Text style={styles.tileHint}>Configure targets</Text>
        <Icon name="chevron-right" size={16} color="#C7CED6" />
      </View>
    </TouchableOpacity>
  </ScrollView>
</View>
{/* My Portfolios */}
<View style={styles.sectionCard}>
<Text style={styles.sectionTitle}>My Portfolios</Text>

{effectivePortfoliosLoading ? (
<View style={styles.loadingBox}>
<Icon name="refresh-cw" size={20} color="#A3A3A3" />
<Text style={styles.loadingBoxTxt}>Loading portfolios…</Text>
</View>
) : effectivePortfoliosData.totalPortfolios > 0 ? (
(effectivePortfoliosData.portfolios.length > 0
? effectivePortfoliosData.portfolios
: [{ name: 'My Portfolio', totalValue: effectivePortfoliosData.totalValue, holdings: [] }]
).map((portfolio: any, index: number) => (
<View key={portfolio.name || `portfolio-${index}`} style={[styles.portCard, shadow]}>
<View style={styles.portHeader}>
<Text style={styles.portName}>{portfolio.name}</Text>
<Text style={styles.portVal}>${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0.00'}</Text>
</View>

{portfolio.holdings?.length ? (
<>
{portfolio.holdings.slice(0, 3).map((h: any, i: number) => (
<View key={h.id || `h-${i}`} style={styles.holdingRow}>
<View style={styles.tickerBadge}>
<Text style={styles.tickerBadgeTxt}>{h.stock.symbol}</Text>
</View>
<View style={{ flex: 1 }}>
<Text style={styles.holdingName}>{h.stock.companyName}</Text>
<Text style={styles.holdingMeta}>{h.shares} shares</Text>
</View>
<Text style={styles.holdingValue}>${h.totalValue && h.totalValue > 0 ? h.totalValue.toLocaleString() : '0.00'}</Text>
</View>
))}
{portfolio.holdings.length > 3 && (
<Text style={styles.moreText}>+{portfolio.holdings.length - 3} more holdings</Text>
)}
</>
) : (
<Text style={styles.emptyHint}>No holdings yet</Text>
)}
</View>
))
) : (
<View style={styles.emptyBox}>
<Icon name="briefcase" size={40} color="#C7C7CC" />
<Text style={styles.emptyTitle}>No Portfolios Yet</Text>
<Text style={styles.emptySub}>Create your first portfolio to start tracking your investments</Text>
<TouchableOpacity style={styles.ctaBtn} onPress={() => navigateTo?.('ai-portfolio')}>
<Icon name="plus" size={16} color="#fff" />
<Text style={styles.ctaBtnTxt}>Create Portfolio</Text>
</TouchableOpacity>
</View>
)}
</View>
{/* Watchlist */}
<View style={styles.sectionCard}>
<Text style={styles.sectionTitle}>Watchlist</Text>

{effectiveWatchlistLoading ? (
<View style={styles.loadingBox}>
<Icon name="refresh-cw" size={20} color="#A3A3A3" />
<Text style={styles.loadingBoxTxt}>Loading watchlist…</Text>
</View>
) : effectiveWatchlistData.length > 0 ? (
effectiveWatchlistData.map((w: any) => (
<View key={w.id} style={[styles.watchRow, shadow]}>
<View style={styles.tickerBadge}>
<Text style={styles.tickerBadgeTxt}>{w.stock.symbol}</Text>
</View>
<View style={{ flex: 1 }}>
<Text style={styles.holdingName}>{w.stock.companyName}</Text>
<Text style={styles.holdingMeta}>Added {new Date(w.addedAt).toLocaleDateString()}</Text>
<Text style={styles.noteTxt}>{w.notes || 'No notes added'}</Text>
</View>
<View style={{ alignItems: 'flex-end' }}>
<Text style={styles.holdingValue}>${w.stock.currentPrice}</Text>
{w.targetPrice && <Text style={styles.targetTxt}>Target ${w.targetPrice}</Text>}
</View>
</View>
))
) : (
<View style={styles.emptyBox}>
<Icon name="eye" size={40} color="#C7C7CC" />
<Text style={styles.emptyTitle}>No Watchlist Stocks</Text>
<Text style={styles.emptySub}>Add stocks to your watchlist to start tracking performance</Text>
<TouchableOpacity style={styles.ctaBtn} onPress={() => navigateTo?.('stock')}>
<Icon name="plus" size={16} color="#fff" />
<Text style={styles.ctaBtnTxt}>Add Stocks</Text>
</TouchableOpacity>
</View>
)}
</View>
{/* Quick Actions */}
<View style={styles.sectionCard}>
<Text style={styles.sectionTitle}>Quick Actions</Text>
<View style={styles.quickActionsGrid}>
<TouchableOpacity 
style={styles.quickActionButton}
onPress={() => navigateTo?.('stock')}
>
<Icon name="plus" size={24} color="#34C759" />
<Text style={styles.quickActionText}>Add Stock</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.quickActionButton}
onPress={() => navigateTo?.('portfolio')}
>
<Icon name="bar-chart-2" size={24} color="#007AFF" />
<Text style={styles.quickActionText}>View Portfolio</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.quickActionButton}
onPress={() => navigateTo?.('ai-portfolio')}
>
<Icon name="cpu" size={24} color="#FF9500" />
<Text style={styles.quickActionText}>AI Analysis</Text>
</TouchableOpacity>
<TouchableOpacity 
  style={styles.quickActionButton}
  onPress={() => navigateTo?.('social-feed')}
>
  <Icon name="bookmark" size={24} color="#5856D6" />
  <Text style={styles.quickActionText}>News Feed</Text>
</TouchableOpacity>
</View>
      </View>
    </ScrollView>

    {/* SBLOC Calculator */}
    <SBLOCCalculator
      visible={showSBLOCModal}
      onClose={() => setShowSBLOCModal(false)}
      portfolioValue={portfolioValue}
      onApply={() => {
        setShowSBLOCModal(false);
        Alert.alert(
          'SBLOC Application',
          'This would open the SBLOC application flow with our partner banks.',
          [{ text: 'OK' }]
        );
      }}
    />

    {/* Privacy Dashboard Modal */}
    <PrivacyDashboard
      visible={showPrivacyDashboard}
      onClose={() => setShowPrivacyDashboard(false)}
    />

    {/* New SBLOC Calculator Modal */}
    <SblocCalculatorModal
      visible={showSblocCalculator}
      onClose={() => setShowSblocCalculator(false)}
      apr={8.5}
      eligibleEquity={portfolioValue || 0}
      maxLtvPct={50}
      currentDebt={0}
      onApply={(amount) => {
        setShowSblocCalculator(false);
        // Navigate to SBLOC bank selection
        if (navigateTo) {
          navigateTo('SBLOCBankSelection', { amountUsd: amount });
        } else {
          Alert.alert(
            'SBLOC Application',
            `This would open the SBLOC application flow for $${amount.toLocaleString()}.`,
            [{ text: 'OK' }]
          );
        }
      }}
    />

    {/* Account Management Modal */}
    <Modal
      visible={showAccountManagement}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowAccountManagement(false)}
    >
      <View style={{ flex: 1 }}>
        <AccountManagementScreen 
          navigateTo={(screen: string) => {
            // If navigating back to profile, close the modal instead
            if (screen === 'profile') {
              setShowAccountManagement(false);
            } else if (navigateTo) {
              navigateTo(screen);
            } else {
              navigate(screen);
            }
          }}
        />
      </View>
    </Modal>

    {/* Licensing Disclosure Modal */}
    <Modal
      visible={showLicensingDisclosure}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowLicensingDisclosure(false)}
    >
      <LicensingDisclosureScreen onClose={() => setShowLicensingDisclosure(false)} />
    </Modal>
  </SafeAreaView>
);
};
const styles = StyleSheet.create({
container: { flex: 1, backgroundColor: UI.bg },

// Header (keep yours; unchanged)
header: {
flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
paddingHorizontal: 20, paddingVertical: 16, backgroundColor: UI.card,
borderBottomWidth: 1, borderBottomColor: UI.border,
},
headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 16 },
headerRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },
headerTitle: { fontSize: 20, fontWeight: '700', color: UI.text },
refreshButton: {
padding: 8,
borderRadius: 20,
backgroundColor: '#F2F2F7',
},
spinningIcon: {
transform: [{ rotate: '360deg' }],
},
logoutButton: {
flexDirection: 'row',
alignItems: 'center',
gap: 8,
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 16,
backgroundColor: '#FFF5F5',
},
logoutButtonText: {
fontSize: 14,
fontWeight: '600',
color: '#ff4757',
},
settingsButton: {
padding: 8,
borderRadius: 20,
backgroundColor: '#F2F2F7',
},
settingsDropdown: {
position: 'absolute',
top: 50,
right: 0,
backgroundColor: '#FFFFFF',
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 4 },
shadowOpacity: 0.15,
shadowRadius: 8,
elevation: 8,
minWidth: 180,
zIndex: 1000,
},
settingsItem: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 16,
paddingVertical: 12,
gap: 12,
},
logoutItem: {
borderTopWidth: 1,
borderTopColor: '#E5E7EB',
},
settingsItemText: {
fontSize: 16,
color: '#1F2937',
fontWeight: '500',
},
logoutText: {
color: '#ff4757',
},

content: { flex: 1 },

/* --- HERO --- */
heroWrap: { backgroundColor: UI.bg },
heroTop: {
height: 80,
backgroundColor: UI.accent,
},
heroCard: {
marginTop: -40,
marginHorizontal: 16,
backgroundColor: UI.card,
borderRadius: UI.radius,
padding: 16,
alignItems: 'center',
borderWidth: 1,
borderColor: UI.border,
},
avatarWrap: { width: 88, height: 88, borderRadius: 44, overflow: 'hidden', marginTop: -56, marginBottom: 8 },
avatarImg: { width: '100%', height: '100%' },
avatarFallback: { flex: 1, backgroundColor: UI.violet, alignItems: 'center', justifyContent: 'center' },
avatarFallbackTxt: { fontSize: 36, color: '#fff', fontWeight: '800' },
avatarRing: {
position: 'absolute', inset: 0, borderRadius: 44,
borderWidth: 3, borderColor: '#FFFFFF99',
},
heroName: { fontSize: 20, fontWeight: '800', color: UI.text, marginTop: 4 },
heroEmail: { fontSize: 14, color: UI.sub, marginTop: 2 },
heroSince: { fontSize: 12, color: '#9CA3AF', marginTop: 2 },
pillsRow: { flexDirection: 'row', gap: 8, marginTop: 12, flexWrap: 'wrap', justifyContent: 'center' },
pill: {
flexDirection: 'row', alignItems: 'center',
paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999,
backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: UI.border,
},
pillTxt: { marginLeft: 6, fontSize: 12, fontWeight: '700', color: UI.text },

/* --- SECTION CARD WRAPPER --- */

/* --- TILES --- */
tileRow: { flexDirection: 'row', gap: 12 },
tileScrollView: {
  marginTop: 16,
},

// New UI styles for polished overview
sectionCard:{
  backgroundColor:'#fff',
  borderRadius:16,
  padding:16,
  marginHorizontal:20,
  marginTop:12,
  marginBottom:8,
  shadowColor:'#000',
  shadowOffset:{ width:0, height:2 },
  shadowOpacity:0.06,
  shadowRadius:6,
  elevation:2,
},
sectionHeader:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:8 },
sectionHeaderLeft:{},
sectionEyebrow:{ fontSize:12, color:'#8E8E93', fontWeight:'600', letterSpacing:0.2 },
sectionTitle:{ fontSize:20, fontWeight:'800', color:'#1C1C1E', marginTop:2 },
sectionAction:{
  flexDirection:'row', alignItems:'center', gap:6,
  backgroundColor:'#E7F1FF', paddingHorizontal:10, paddingVertical:6, borderRadius:999
},
sectionActionText:{ color:'#007AFF', fontWeight:'700', fontSize:12 },

tileScrollContent:{ paddingVertical:4, paddingRight:6 },
tile:{
  width:160,                   // keeps snap tidy
  borderRadius:14,
  padding:14,
  backgroundColor:'#fff',
  marginRight:8,
},
shadow:{
  shadowColor:'#000',
  shadowOffset:{ width:0, height:2 },
  shadowOpacity:0.06,
  shadowRadius:4,
  elevation:2,
},
tileIcon:{
  width:32, height:32, borderRadius:8, borderWidth:1,
  alignItems:'center', justifyContent:'center', marginBottom:10
},
tileLabel:{ fontSize:12, color:'#6B7280', fontWeight:'700', letterSpacing:0.3 },
tileValue:{ fontSize:20, fontWeight:'800', marginTop:6 },
tileHint:{ fontSize:12, color:'#94A3B8' },
tileFooterRow:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginTop:10 },

badgeRow:{ flexDirection:'row', alignItems:'center', gap:8, marginTop:6 },
badge:{ borderRadius:999, paddingHorizontal:10, paddingVertical:4 },
badgeText:{ fontSize:12, fontWeight:'800' },

skeletonLine:{
  height:22, borderRadius:6, marginTop:6,
  backgroundColor:'#EEF2F6',
},
tileValueMuted: { marginTop: 2, fontSize: 16, color: '#9CA3AF', fontWeight: '700' },
tileChevron: { position: 'absolute', bottom: 10, right: 10 },

/* --- ROW LIST (actions) --- */
rowItem: {
flexDirection: 'row', alignItems: 'center',
paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#F3F4F6',
},
rowIcon: {
width: 32, height: 32, borderRadius: 8, borderWidth: 1,
alignItems: 'center', justifyContent: 'center', marginRight: 12,
},
rowText: { flex: 1, fontSize: 15, color: UI.text, fontWeight: '600' },

/* --- PORTFOLIO CARD --- */
portCard: {
backgroundColor: '#F9FAFB', borderRadius: 14, borderWidth: 1, borderColor: UI.border, padding: 14, marginBottom: 12,
},
portHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
portName: { fontSize: 15, fontWeight: '800', color: UI.text },
portVal: { fontSize: 16, fontWeight: '800', color: UI.success },
holdingRow: {
flexDirection: 'row', alignItems: 'center', paddingVertical: 10,
borderTopWidth: 1, borderTopColor: '#EEF2F7',
},
tickerBadge: {
minWidth: 52, paddingHorizontal: 10, height: 28,
borderRadius: 999, backgroundColor: '#F1F5F9',
alignItems: 'center', justifyContent: 'center', marginRight: 10, borderWidth: 1, borderColor: UI.border,
},
tickerBadgeTxt: { fontSize: 12, fontWeight: '800', color: UI.text },
holdingName: { fontSize: 14, fontWeight: '700', color: UI.text },
holdingMeta: { fontSize: 12, color: UI.sub, marginTop: 2 },
holdingValue: { fontSize: 14, fontWeight: '800', color: UI.text },
moreText: { textAlign: 'center', marginTop: 8, fontSize: 12, color: UI.sub, fontStyle: 'italic' },
emptyHint: { fontSize: 13, color: UI.sub, marginTop: 4 },

/* --- WATCHLIST ROW --- */
watchRow: {
flexDirection: 'row', alignItems: 'center',
backgroundColor: '#FFFFFF', borderRadius: 12, borderWidth: 1, borderColor: UI.border,
padding: 12, marginBottom: 10,
},
noteTxt: { fontSize: 12, color: '#9CA3AF', marginTop: 2, fontStyle: 'italic' },
targetTxt: { fontSize: 12, color: UI.accent, marginTop: 2, fontWeight: '700' },

/* --- EMPTY / LOADING --- */
emptyBox: { alignItems: 'center', paddingVertical: 20 },
emptyTitle: { fontSize: 16, fontWeight: '800', color: UI.text, marginTop: 12 },
emptySub: { fontSize: 13, color: UI.sub, textAlign: 'center', marginTop: 4 },
ctaBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: UI.success, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 999, marginTop: 12 },
ctaBtnTxt: { color: '#fff', fontSize: 14, fontWeight: '800' },
loadingBox: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8 },
loadingBoxTxt: { color: '#9CA3AF', fontWeight: '700' },

// Quick Actions (keep existing)
quickActionsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 12,
},
quickActionButton: {
width: (width - 64) / 2,
backgroundColor: '#F8F9FA',
borderRadius: 12,
padding: 16,
alignItems: 'center',
borderWidth: 1,
borderColor: '#E5E5EA',
},
quickActionText: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 8,
textAlign: 'center',
},

// Loading and Error states
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

// Debug button
debugButton: {
  backgroundColor: '#007AFF',
  paddingHorizontal: 20,
  paddingVertical: 12,
  borderRadius: 8,
  marginTop: 16,
},
debugButtonText: {
  color: '#FFFFFF',
  fontSize: 14,
  fontWeight: '600',
  textAlign: 'center',
},

// SBLOC Widget Styles
sblocBadge: {
  position: 'absolute',
  top: 8,
  left: 8,
  backgroundColor: '#FEF3C7',
  paddingHorizontal: 6,
  paddingVertical: 2,
  borderRadius: 8,
  borderWidth: 1,
  borderColor: '#FDE68A',
},
sblocBadgeText: {
  fontSize: 10,
  fontWeight: '800',
  color: '#F59E0B',
},

// SBLOC Modal Styles
modalContainer: {
  flex: 1,
  backgroundColor: '#F6F7FB',
},
modalHeader: {
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
  paddingHorizontal: 20,
  paddingVertical: 16,
  backgroundColor: '#FFFFFF',
  borderBottomWidth: 1,
  borderBottomColor: '#E5E7EB',
},
modalCloseButton: {
  padding: 8,
  borderRadius: 20,
  backgroundColor: '#F2F2F7',
},
modalTitle: {
  fontSize: 18,
  fontWeight: '700',
  color: '#111827',
  flex: 1,
  textAlign: 'center',
  marginRight: 40, // Compensate for close button
},
modalContent: {
  flex: 1,
  paddingHorizontal: 20,
},
modalFooter: {
  flexDirection: 'row',
  gap: 12,
  padding: 20,
  backgroundColor: '#FFFFFF',
  borderTopWidth: 1,
  borderTopColor: '#E5E7EB',
},

// SBLOC Hero Section
sblocHero: {
  alignItems: 'center',
  paddingVertical: 32,
  paddingHorizontal: 20,
  backgroundColor: '#FFFFFF',
  borderRadius: 16,
  marginVertical: 16,
  borderWidth: 1,
  borderColor: '#E5E7EB',
},
sblocIcon: {
  width: 64,
  height: 64,
  borderRadius: 32,
  backgroundColor: '#FEF3C7',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: 16,
  borderWidth: 1,
  borderColor: '#FDE68A',
},
sblocTitle: {
  fontSize: 24,
  fontWeight: '800',
  color: '#111827',
  textAlign: 'center',
  marginBottom: 8,
},
sblocSubtitle: {
  fontSize: 16,
  color: '#6B7280',
  textAlign: 'center',
  lineHeight: 24,
},

// SBLOC Cards
sblocCard: {
  backgroundColor: '#FFFFFF',
  borderRadius: 16,
  padding: 20,
  marginBottom: 16,
  borderWidth: 1,
  borderColor: '#E5E7EB',
},
sblocCardTitle: {
  fontSize: 18,
  fontWeight: '700',
  color: '#111827',
  marginBottom: 12,
},
sblocDescription: {
  fontSize: 15,
  color: '#6B7280',
  lineHeight: 22,
  marginBottom: 16,
},

// Borrowing Power
borrowingPowerRow: {
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: 8,
},
borrowingPowerItem: {
  alignItems: 'center',
  flex: 1,
},
borrowingPowerLabel: {
  fontSize: 14,
  color: '#6B7280',
  fontWeight: '600',
  marginBottom: 4,
},
borrowingPowerValue: {
  fontSize: 20,
  fontWeight: '800',
  color: '#111827',
},
borrowingPowerNote: {
  fontSize: 12,
  color: '#9CA3AF',
  textAlign: 'center',
  fontStyle: 'italic',
},

// Benefits List
benefitsList: {
  marginTop: 8,
},
benefitItem: {
  flexDirection: 'row',
  alignItems: 'center',
  marginBottom: 12,
},
benefitText: {
  fontSize: 15,
  color: '#111827',
  marginLeft: 12,
  fontWeight: '500',
},

// Rate Comparison
rateComparison: {
  flexDirection: 'row',
  justifyContent: 'space-between',
},
rateItem: {
  alignItems: 'center',
  flex: 1,
},
rateType: {
  fontSize: 14,
  color: '#6B7280',
  fontWeight: '600',
  marginBottom: 8,
},
rateValue: {
  fontSize: 18,
  fontWeight: '800',
},

// Steps List
stepsList: {
  marginTop: 8,
},
stepItem: {
  flexDirection: 'row',
  alignItems: 'flex-start',
  marginBottom: 20,
},
stepNumber: {
  width: 32,
  height: 32,
  borderRadius: 16,
  backgroundColor: '#F59E0B',
  alignItems: 'center',
  justifyContent: 'center',
  marginRight: 16,
},
stepNumberText: {
  fontSize: 16,
  fontWeight: '800',
  color: '#FFFFFF',
},
stepContent: {
  flex: 1,
},
stepTitle: {
  fontSize: 16,
  fontWeight: '700',
  color: '#111827',
  marginBottom: 4,
},
stepDescription: {
  fontSize: 14,
  color: '#6B7280',
  lineHeight: 20,
},

// Considerations List
considerationsList: {
  marginTop: 8,
},
considerationItem: {
  flexDirection: 'row',
  alignItems: 'flex-start',
  marginBottom: 12,
},
considerationText: {
  fontSize: 14,
  color: '#6B7280',
  marginLeft: 12,
  flex: 1,
  lineHeight: 20,
},

// Modal Footer Buttons
sblocCalculatorBtn: {
  flex: 1,
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 8,
  backgroundColor: '#F59E0B',
  paddingVertical: 16,
  borderRadius: 12,
},
sblocCalculatorBtnText: {
  fontSize: 16,
  fontWeight: '700',
  color: '#FFFFFF',
},
sblocApplyBtn: {
  flex: 1,
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: '#10B981',
  paddingVertical: 16,
  borderRadius: 12,
},
sblocApplyBtnText: {
  fontSize: 16,
  fontWeight: '700',
  color: '#FFFFFF',
},
});
export default ProfileScreen;
