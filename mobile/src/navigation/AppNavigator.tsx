import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Feather from '@expo/vector-icons/Feather';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import { View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import ProfileScreen from '../features/user/screens/ProfileScreen';
import { setNavigator } from './NavigationService';

// Existing screens (paths reflect current project structure)
import HomeScreen from '../navigation/HomeScreen';
import CryptoScreen from '../navigation/CryptoScreen';
import AIPortfolioScreen from '../features/portfolio/screens/AIPortfolioScreen';
import TutorScreen from '../features/education/screens/TutorScreen';
import StockScreen from '../features/stocks/screens/StockScreen';
import StockScreenWrapper from './StockScreenWrapper';
import StockDetailScreen from '../features/stocks/screens/StockDetailScreen';
import PortfolioScreen from '../features/portfolio/screens/UserPortfoliosScreen';
import SocialScreen from '../features/social/screens/SocialScreen';
import AIScansScreen from '../features/aiScans/screens/AIScansScreen';
import AIOptionsScreen from '../features/options/screens/AIOptionsScreen';
import OptionsCopilotScreen from '../features/options/screens/OptionsCopilotScreen';
import DayTradingScreen from '../features/trading/screens/DayTradingScreen';
import TradingScreenWrapper from './TradingScreenWrapper';

// New hub screen
import InvestHubScreen from '../features/invest/InvestHubScreen';
import InvestAdvancedSheet from '../features/invest/InvestAdvancedSheet';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain" component={HomeScreen} />
      {/* Legacy alias to preserve existing navigations */}
      <Stack.Screen name="home" component={HomeScreen} />
      <Stack.Screen name="Profile" component={ProfileScreen} />
      <Stack.Screen name="profile" component={ProfileScreen} />
    </Stack.Navigator>
  );
}

function InvestStack() {
  return (
    <Stack.Navigator screenOptions={{ headerBackTitleVisible: false }}>
      <Stack.Screen name="InvestMain" component={InvestHubScreen} options={{ headerShown: false }} />

      {/* Primary flows */}
      <Stack.Screen name="Stocks" component={StockScreenWrapper} options={{ headerShown: true, title: 'Stocks' }} />
      <Stack.Screen name="StockDetail" component={StockDetailScreen} options={{ headerShown: true, title: 'Stock Detail' }} />
      <Stack.Screen name="Crypto" component={CryptoScreen} options={{ headerShown: true, title: 'Crypto' }} />
      <Stack.Screen name="AIPortfolio" component={AIPortfolioScreen} options={{ headerShown: true, title: 'AI Portfolio' }} />
      <Stack.Screen name="Portfolio" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="Screeners" component={AIScansScreen} options={{ headerShown: true, title: 'Screeners' }} />
      <Stack.Screen name="AIOptions" component={AIOptionsScreen} options={{ headerShown: true, title: 'Options' }} />
      <Stack.Screen name="OptionsCopilot" component={OptionsCopilotScreen} options={{ headerShown: true, title: 'Options Copilot' }} />
      <Stack.Screen name="DayTrading" component={TradingScreenWrapper} options={{ headerShown: false }} />
      <Stack.Screen
        name="InvestAdvanced"
        component={InvestAdvancedSheet}
        options={{ presentation: 'transparentModal', animation: 'fade', headerShown: false }}
      />

      {/* Legacy aliases to avoid breaking existing navigate calls */}
      <Stack.Screen name="stock" component={StockScreenWrapper} options={{ headerShown: true, title: 'Stocks' }} />
      <Stack.Screen name="crypto" component={CryptoScreen} options={{ headerShown: true, title: 'Crypto' }} />
      <Stack.Screen name="ai-recommendations" component={AIPortfolioScreen} options={{ headerShown: true, title: 'AI Portfolio' }} />
      <Stack.Screen name="portfolio" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="portfolio-management" component={PortfolioScreen} options={{ headerShown: true, title: 'Portfolio' }} />
      <Stack.Screen name="premium-analytics" component={PortfolioScreen} options={{ headerShown: true, title: 'Analytics' }} />
      <Stack.Screen name="subscription" component={PortfolioScreen} options={{ headerShown: true, title: 'Subscription' }} />
      <Stack.Screen name="portfolio-analytics" component={PortfolioScreen} options={{ headerShown: true, title: 'Analytics' }} />
      <Stack.Screen name="stock-screening" component={AIScansScreen} options={{ headerShown: true, title: 'Screeners' }} />
      <Stack.Screen name="trading" component={TradingScreenWrapper} options={{ headerShown: false }} />
      <Stack.Screen name="day-trading" component={TradingScreenWrapper} options={{ headerShown: false }} />
    </Stack.Navigator>
  );
}

function LearnStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="LearnMain" component={TutorScreen} />
      {/* Legacy alias */}
      <Stack.Screen name="tutor" component={TutorScreen} />
    </Stack.Navigator>
  );
}

function CommunityStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CommunityMain" component={SocialScreen} />
      {/* Legacy alias */}
      <Stack.Screen name="social" component={SocialScreen} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  const navRef = React.useRef<any>(null);
  const [currentTabIndex, setCurrentTabIndex] = React.useState<number>(0);
  const tabOrder = React.useMemo(() => ['Home', 'Invest', 'Learn', 'Community'], []);

  const handleStateChange = React.useCallback(() => {
    const rootState = navRef.current?.getRootState?.();
    if (!rootState || !Array.isArray(rootState.routes)) return;
    const idx = typeof rootState.index === 'number' ? rootState.index : 0;
    setCurrentTabIndex(idx);
  }, []);

  const handleGesture = React.useCallback((event: any) => {
    const { state, translationX } = event.nativeEvent;
    if (state !== State.END) return;
    const dx = translationX;
    // Determine left/right swipe with a sensible threshold
    const threshold = 50;
    if (dx <= -threshold && currentTabIndex < tabOrder.length - 1) {
      // swipe left: go to next tab
      const next = tabOrder[currentTabIndex + 1];
      navRef.current?.navigate(next);
      return;
    }
    if (dx >= threshold && currentTabIndex > 0) {
      // swipe right: go to previous tab
      const prev = tabOrder[currentTabIndex - 1];
      navRef.current?.navigate(prev);
    }
  }, [currentTabIndex, tabOrder]);

  React.useEffect(() => {
    if (navRef.current) setNavigator(navRef.current);
  }, []);

  return (
    <NavigationContainer ref={navRef} onStateChange={handleStateChange}>
      <PanGestureHandler onGestureEvent={handleGesture} onHandlerStateChange={handleGesture}>
        <View style={{ flex: 1 }}>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              headerShown: false,
              tabBarLabelStyle: { fontSize: 12, fontWeight: '700' },
              tabBarIcon: ({ color, size }) => {
                const iconMap: Record<string, keyof typeof Feather.glyphMap> = {
                  Home: 'home',
                  Invest: 'bar-chart-2',
                  Learn: 'book-open',
                  Community: 'users',
                };
                const name = iconMap[route.name] ?? 'grid';
                return <Feather name={name} size={size} color={color} />;
              },
              tabBarActiveTintColor: '#34C759', // mint
              tabBarInactiveTintColor: '#8E8E93',
              tabBarStyle: { borderTopWidth: 0, elevation: 0 },
              tabBarBackground: () => (
                <LinearGradient
                  colors={["#FFFFFF", "#FDF7E3", "#F5FFF8"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={{ flex: 1 }}
                />
              ),
              lazy: true,
            })}
          >
            <Tab.Screen name="Home" component={HomeStack} />
            <Tab.Screen name="Invest" component={InvestStack} />
            <Tab.Screen name="Learn" component={LearnStack} />
            <Tab.Screen name="Community" component={CommunityStack} />
          </Tab.Navigator>
        </View>
      </PanGestureHandler>
    </NavigationContainer>
  );
}


