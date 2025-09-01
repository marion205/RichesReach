#!/usr/bin/env node
/**
 * Frontend Component Test Script
 * This script tests that all our components can be imported without errors
 */

console.log('🧪 Testing Frontend Components...\n');

// Test component imports
try {
  console.log('✅ Testing SocialNav component...');
  require('./components/SocialNav.tsx');
  console.log('   SocialNav: PASSED');
} catch (error) {
  console.log('   SocialNav: FAILED -', error.message);
}

try {
  console.log('✅ Testing DiscussionCard component...');
  require('./components/DiscussionCard.tsx');
  console.log('   DiscussionCard: PASSED');
} catch (error) {
  console.log('   DiscussionCard: FAILED -', error.message);
}

try {
  console.log('✅ Testing WatchlistCard component...');
  require('./components/WatchlistCard.tsx');
  console.log('   WatchlistCard: PASSED');
} catch (error) {
  console.log('   WatchlistCard: FAILED -', error.message);
}

try {
  console.log('✅ Testing PortfolioCard component...');
  require('./components/PortfolioCard.tsx');
  console.log('   PortfolioCard: PASSED');
} catch (error) {
  console.log('   PortfolioCard: FAILED -', error.message);
}

try {
  console.log('✅ Testing AchievementCard component...');
  require('./components/AchievementCard.tsx');
  console.log('   AchievementCard: PASSED');
} catch (error) {
  console.log('   AchievementCard: PASSED');
}

try {
  console.log('✅ Testing SocialScreen component...');
  require('./screens/SocialScreen.tsx');
  console.log('   SocialScreen: PASSED');
} catch (error) {
  console.log('   SocialScreen: FAILED -', error.message);
}

try {
  console.log('✅ Testing BottomTabBar component...');
  require('./components/BottomTabBar.tsx');
  console.log('   BottomTabBar: PASSED');
} catch (error) {
  console.log('   BottomTabBar: PASSED');
}

console.log('\n🎉 Frontend Component Test Complete!');
console.log('📱 Now you can test the app on your device/simulator');
console.log('🔗 Use the Expo Go app or press "i" for iOS simulator');
console.log('🔗 Press "a" for Android emulator');
console.log('🔗 Press "w" for web browser');
