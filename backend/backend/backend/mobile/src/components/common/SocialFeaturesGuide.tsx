import React from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface SocialFeaturesGuideProps {
onNavigate: (screen: string, params?: any) => void;
}
const SocialFeaturesGuide: React.FC<SocialFeaturesGuideProps> = ({ onNavigate }) => {
const features = [
{
title: 'Portfolio Performance Previews',
description: 'See how other investors\' portfolios are performing with real-time return percentages',
icon: 'trending-up',
color: '#34C759',
howToAccess: 'Go to Discuss tab → Discover tab → Tap on any user card',
example: 'Sarah Johnson: +23.3% return on Growth Portfolio'
},
{
title: 'Enhanced User Profiles',
description: 'Comprehensive profiles showing investment experience, goals, and performance',
icon: 'user',
color: '#007AFF',
howToAccess: 'Go to Discuss tab → Discover tab → Tap "View Profile" on any user',
example: 'Experience badges, risk tolerance, investment goals, monthly budget'
},
{
title: 'Investment Experience Badges',
description: 'Color-coded badges showing user experience level (Beginner/Intermediate/Advanced)',
icon: 'award',
color: '#FF9500',
howToAccess: 'Visible on all user cards and profiles',
example: ' Beginner, Intermediate, Advanced'
},
{
title: 'Risk Tolerance Indicators',
description: 'Visual indicators showing each user\'s risk tolerance level',
icon: 'shield',
color: '#FF3B30',
howToAccess: 'Go to Discuss tab → Discover tab → Tap "View Profile"',
example: 'Conservative (Green), Moderate (Orange), Aggressive (Red)'
},
{
title: 'Public Portfolio Sharing',
description: 'Users can share their portfolio performance and holdings publicly',
icon: 'pie-chart',
color: '#AF52DE',
howToAccess: 'Go to Discuss tab → Discover tab → View user profiles',
example: 'Growth Portfolio: $45,000 value, +23.3% return'
},
{
title: 'Learning Progress Tracking',
description: 'See how much time users have spent learning and modules completed',
icon: 'book-open',
color: '#32D74B',
howToAccess: 'Go to Discuss tab → Discover tab → View user stats',
example: '180 minutes learning, 8 modules completed, 12-day streak'
},
{
title: 'Social Stats',
description: 'Followers, following, portfolios, and learning achievements',
icon: 'users',
color: '#FFD60A',
howToAccess: 'Go to Discuss tab → Discover tab → View user cards',
example: '1,247 followers, 89 following, 2 portfolios, 8 modules'
}
];
return (
<ScrollView style={styles.container}>
<View style={styles.header}>
<Text style={styles.title}> Your New Social Features</Text>
<Text style={styles.subtitle}>
Here's exactly how to access all the new social investing features!
</Text>
</View>
{features.map((feature, index) => (
<View key={index} style={styles.featureCard}>
<View style={styles.featureHeader}>
<View style={[styles.featureIcon, { backgroundColor: feature.color }]}>
<Icon name={feature.icon} size={24} color="#FFFFFF" />
</View>
<View style={styles.featureInfo}>
<Text style={styles.featureTitle}>{feature.title}</Text>
<Text style={styles.featureDescription}>{feature.description}</Text>
</View>
</View>
<View style={styles.howToAccess}>
<Text style={styles.howToTitle}> How to Access:</Text>
<Text style={styles.howToText}>{feature.howToAccess}</Text>
</View>
<View style={styles.example}>
<Text style={styles.exampleTitle}> Example:</Text>
<Text style={styles.exampleText}>{feature.example}</Text>
</View>
</View>
))}
<View style={styles.quickStartCard}>
<Text style={styles.quickStartTitle}> Quick Start Guide</Text>
<View style={styles.steps}>
<View style={styles.step}>
<Text style={styles.stepNumber}>1</Text>
<Text style={styles.stepText}>Tap the "Discuss" tab in bottom navigation</Text>
</View>
<View style={styles.step}>
<Text style={styles.stepNumber}>2</Text>
<Text style={styles.stepText}>Switch to the "Discover" tab at the top</Text>
</View>
<View style={styles.step}>
<Text style={styles.stepNumber}>3</Text>
<Text style={styles.stepText}>Browse investors and tap "View Profile"</Text>
</View>
<View style={styles.step}>
<Text style={styles.stepNumber}>4</Text>
<Text style={styles.stepText}>Follow users to see their updates in "Activity" tab</Text>
</View>
</View>
<TouchableOpacity
style={styles.tryNowButton}
onPress={() => onNavigate('social')}
>
<Icon name="arrow-right" size={20} color="#FFFFFF" />
<Text style={styles.tryNowText}>Try It Now!</Text>
</TouchableOpacity>
</View>
<View style={styles.tabsExplanation}>
<Text style={styles.tabsTitle}> Social Tab Breakdown</Text>
<View style={styles.tabItem}>
<Icon name="trending-up" size={20} color="#34C759" />
<View style={styles.tabInfo}>
<Text style={styles.tabName}>Trending</Text>
<Text style={styles.tabDescription}>Popular discussion posts and market commentary</Text>
</View>
</View>
<View style={styles.tabItem}>
<Icon name="users" size={20} color="#007AFF" />
<View style={styles.tabInfo}>
<Text style={styles.tabName}>Following</Text>
<Text style={styles.tabDescription}>Posts from investors you follow</Text>
</View>
</View>
<View style={styles.tabItem}>
<Icon name="activity" size={20} color="#FF9500" />
<View style={styles.tabInfo}>
<Text style={styles.tabName}>Activity</Text>
<Text style={styles.tabDescription}>Real-time portfolio updates and trading activity</Text>
</View>
</View>
<View style={styles.tabItem}>
<Icon name="search" size={20} color="#AF52DE" />
<View style={styles.tabInfo}>
<Text style={styles.tabName}>Discover</Text>
<Text style={styles.tabDescription}>Find and follow other investors</Text>
</View>
</View>
</View>
</ScrollView>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
header: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
title: {
fontSize: 24,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 8,
},
subtitle: {
fontSize: 16,
color: '#8E8E93',
lineHeight: 22,
},
featureCard: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginBottom: 16,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
featureHeader: {
flexDirection: 'row',
alignItems: 'flex-start',
marginBottom: 16,
},
featureIcon: {
width: 48,
height: 48,
borderRadius: 24,
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
featureInfo: {
flex: 1,
},
featureTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
featureDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
howToAccess: {
backgroundColor: '#E3F2FD',
padding: 12,
borderRadius: 8,
marginBottom: 12,
},
howToTitle: {
fontSize: 14,
fontWeight: '600',
color: '#007AFF',
marginBottom: 4,
},
howToText: {
fontSize: 14,
color: '#1C1C1E',
lineHeight: 20,
},
example: {
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
},
exampleTitle: {
fontSize: 14,
fontWeight: '600',
color: '#8E8E93',
marginBottom: 4,
},
exampleText: {
fontSize: 14,
color: '#1C1C1E',
lineHeight: 20,
},
quickStartCard: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginBottom: 16,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
quickStartTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
steps: {
marginBottom: 20,
},
step: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 12,
},
stepNumber: {
width: 24,
height: 24,
borderRadius: 12,
backgroundColor: '#007AFF',
color: '#FFFFFF',
fontSize: 14,
fontWeight: 'bold',
textAlign: 'center',
lineHeight: 24,
marginRight: 12,
},
stepText: {
flex: 1,
fontSize: 16,
color: '#1C1C1E',
lineHeight: 22,
},
tryNowButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 25,
},
tryNowText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
marginLeft: 8,
},
tabsExplanation: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginBottom: 16,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
tabsTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
tabItem: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 12,
},
tabInfo: {
flex: 1,
marginLeft: 12,
},
tabName: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 2,
},
tabDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
});
export default SocialFeaturesGuide;
