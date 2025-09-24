import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
TouchableOpacity,
Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import UserProfileService, { ExtendedUserProfile } from '../../features/user/services/UserProfileService';
const { width } = Dimensions.get('window');
interface PersonalizedDashboardProps {
onNavigate: (screen: string, params?: any) => void;
}
const PersonalizedDashboard: React.FC<PersonalizedDashboardProps> = ({ onNavigate }) => {
const [profile, setProfile] = useState<ExtendedUserProfile | null>(null);
const [recommendations, setRecommendations] = useState<any>(null);
const [loading, setLoading] = useState(true);
useEffect(() => {
loadUserProfile();
}, []);
const loadUserProfile = async () => {
try {
const userProfileService = UserProfileService.getInstance();
const userProfile = await userProfileService.getProfile();
if (userProfile) {
setProfile(userProfile);
const personalizedRecs = userProfileService.getPersonalizedRecommendations(userProfile);
setRecommendations(personalizedRecs);
}
} catch (error) {
console.error('Error loading user profile:', error);
} finally {
setLoading(false);
}
};
if (loading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading your personalized dashboard...</Text>
</View>
);
}
if (!profile) {
return (
<View style={styles.noProfileContainer}>
<Icon name="user-plus" size={48} color="#8E8E93" />
<Text style={styles.noProfileTitle}>Complete Your Profile</Text>
<Text style={styles.noProfileText}>
Set up your investment profile to get personalized recommendations
</Text>
<TouchableOpacity 
style={styles.setupButton}
onPress={() => onNavigate('onboarding')}
>
<Text style={styles.setupButtonText}>Get Started</Text>
</TouchableOpacity>
</View>
);
}
const getExperienceIcon = (level: string) => {
switch (level) {
case 'beginner': return 'book-open';
case 'intermediate': return 'trending-up';
case 'advanced': return 'bar-chart-2';
default: return 'user';
}
};
const getExperienceColor = (level: string) => {
switch (level) {
case 'beginner': return '#34C759';
case 'intermediate': return '#007AFF';
case 'advanced': return '#FF9500';
default: return '#8E8E93';
}
};
const getRiskColor = (risk: string) => {
switch (risk) {
case 'conservative': return '#34C759';
case 'moderate': return '#FF9500';
case 'aggressive': return '#FF3B30';
default: return '#8E8E93';
}
};
return (
<ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
{/* Welcome Section */}
<View style={styles.welcomeSection}>
<View style={styles.welcomeHeader}>
<View style={styles.profileIcon}>
<Icon name={getExperienceIcon(profile.experienceLevel)} size={24} color="#FFFFFF" />
</View>
<View style={styles.welcomeText}>
<Text style={styles.welcomeTitle}>
Welcome back, {profile.experienceLevel} investor!
</Text>
<Text style={styles.welcomeSubtitle}>
{UserProfileService.getInstance().getUserStyleSummary(profile)}
</Text>
</View>
</View>
</View>
{/* Quick Stats */}
<View style={styles.statsSection}>
<Text style={styles.sectionTitle}>Your Progress</Text>
<View style={styles.statsGrid}>
<View style={styles.statCard}>
<Icon name="clock" size={20} color="#007AFF" />
<Text style={styles.statValue}>{profile.stats.totalLearningTime}m</Text>
<Text style={styles.statLabel}>Learning Time</Text>
</View>
<View style={styles.statCard}>
<Icon name="check-circle" size={20} color="#34C759" />
<Text style={styles.statValue}>{profile.stats.modulesCompleted}</Text>
<Text style={styles.statLabel}>Modules Done</Text>
</View>
<View style={styles.statCard}>
<Icon name="award" size={20} color="#FF9500" />
<Text style={styles.statValue}>{profile.stats.achievements.length}</Text>
<Text style={styles.statLabel}>Achievements</Text>
</View>
<View style={styles.statCard}>
<Icon name="trending-up" size={20} color="#FF3B30" />
<Text style={styles.statValue}>{profile.stats.streakDays}</Text>
<Text style={styles.statLabel}>Day Streak</Text>
</View>
</View>
</View>
{/* Personalized Recommendations */}
{recommendations && (
<View style={styles.recommendationsSection}>
<Text style={styles.sectionTitle}>Recommended for You</Text>
{/* Learning Recommendations */}
<View style={styles.recommendationCard}>
<View style={styles.recommendationHeader}>
<Icon name="book" size={20} color="#007AFF" />
<Text style={styles.recommendationTitle}>Continue Learning</Text>
</View>
<Text style={styles.recommendationText}>
{recommendations.nextSteps[0] || 'Complete your learning path to unlock new features'}
</Text>
<TouchableOpacity 
style={styles.recommendationButton}
onPress={() => onNavigate('learning-paths')}
>
<Text style={styles.recommendationButtonText}>Start Learning</Text>
<Icon name="arrow-right" size={16} color="#007AFF" />
</TouchableOpacity>
</View>
{/* Investment Recommendations */}
{recommendations.investmentSuggestions.length > 0 && (
<View style={styles.recommendationCard}>
<View style={styles.recommendationHeader}>
<Icon name="trending-up" size={20} color="#34C759" />
<Text style={styles.recommendationTitle}>Investment Ideas</Text>
</View>
{recommendations.investmentSuggestions.map((suggestion: string, index: number) => (
<Text key={index} style={styles.recommendationText}>
• {suggestion}
</Text>
))}
<TouchableOpacity 
style={styles.recommendationButton}
onPress={() => onNavigate('portfolio')}
>
<Text style={styles.recommendationButtonText}>View Portfolio</Text>
<Icon name="arrow-right" size={16} color="#007AFF" />
</TouchableOpacity>
</View>
)}
{/* Risk Profile */}
<View style={styles.recommendationCard}>
<View style={styles.recommendationHeader}>
<View style={[styles.riskIndicator, { backgroundColor: getRiskColor(profile.riskTolerance) }]} />
<Text style={styles.recommendationTitle}>Your Risk Profile</Text>
</View>
<Text style={styles.recommendationText}>
{profile.riskTolerance.charAt(0).toUpperCase()}{profile.riskTolerance.slice(1)} - 
Suggested allocation: {recommendations.suggestedAllocation.stocks}% stocks, 
{recommendations.suggestedAllocation.bonds}% bonds
</Text>
<TouchableOpacity 
style={styles.recommendationButton}
onPress={() => onNavigate('portfolio-analytics')}
>
<Text style={styles.recommendationButtonText}>Optimize Portfolio</Text>
<Icon name="arrow-right" size={16} color="#007AFF" />
</TouchableOpacity>
</View>
</View>
)}
{/* Goals Progress */}
{profile.investmentGoals && profile.investmentGoals.length > 0 && (
<View style={styles.goalsSection}>
<Text style={styles.sectionTitle}>Your Investment Goals</Text>
<View style={styles.goalsList}>
{profile.investmentGoals.map((goal, index) => (
<View key={index} style={styles.goalItem}>
<Icon name="target" size={16} color="#007AFF" />
<Text style={styles.goalText}>
{goal.charAt(0).toUpperCase()}{goal.slice(1).replace('-', ' ')}
</Text>
</View>
))}
</View>
</View>
)}
{/* Quick Actions */}
<View style={styles.actionsSection}>
<Text style={styles.sectionTitle}>Quick Actions</Text>
<View style={styles.actionsGrid}>
<TouchableOpacity 
style={styles.actionCard}
onPress={() => onNavigate('learning-paths')}
>
<Icon name="book-open" size={24} color="#007AFF" />
<Text style={styles.actionText}>Learn</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionCard}
onPress={() => onNavigate('portfolio')}
>
<Icon name="pie-chart" size={24} color="#34C759" />
<Text style={styles.actionText}>Portfolio</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionCard}
onPress={() => onNavigate('social')}
>
<Icon name="globe" size={24} color="#FF9500" />
<Text style={styles.actionText}>News</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.actionCard}
onPress={() => onNavigate('discuss')}
>
<Icon name="message-circle" size={24} color="#AF52DE" />
<Text style={styles.actionText}>Discuss</Text>
</TouchableOpacity>
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
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#F2F2F7',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
noProfileContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#F2F2F7',
paddingHorizontal: 40,
},
noProfileTitle: {
fontSize: 24,
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 20,
marginBottom: 10,
},
noProfileText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
marginBottom: 30,
},
setupButton: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 25,
},
setupButtonText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
},
// Welcome Section
welcomeSection: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
welcomeHeader: {
flexDirection: 'row',
alignItems: 'center',
},
profileIcon: {
width: 48,
height: 48,
borderRadius: 24,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
welcomeText: {
flex: 1,
},
welcomeTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
welcomeSubtitle: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
// Stats Section
statsSection: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
sectionTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 16,
},
statsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 12,
},
statCard: {
flex: 1,
minWidth: (width - 64) / 2,
backgroundColor: '#F2F2F7',
padding: 16,
borderRadius: 12,
alignItems: 'center',
},
statValue: {
fontSize: 24,
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 8,
marginBottom: 4,
},
statLabel: {
fontSize: 12,
color: '#8E8E93',
textAlign: 'center',
},
// Recommendations Section
recommendationsSection: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
recommendationCard: {
backgroundColor: '#F2F2F7',
padding: 16,
borderRadius: 12,
marginBottom: 12,
},
recommendationHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 8,
},
recommendationTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginLeft: 8,
},
recommendationText: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
marginBottom: 12,
},
recommendationButton: {
flexDirection: 'row',
alignItems: 'center',
alignSelf: 'flex-start',
},
recommendationButtonText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
marginRight: 4,
},
riskIndicator: {
width: 12,
height: 12,
borderRadius: 6,
},
// Goals Section
goalsSection: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
goalsList: {
gap: 8,
},
goalItem: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 8,
},
goalText: {
fontSize: 16,
color: '#1C1C1E',
marginLeft: 12,
},
// Actions Section
actionsSection: {
backgroundColor: '#FFFFFF',
padding: 20,
marginBottom: 16,
},
actionsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 12,
},
actionCard: {
flex: 1,
minWidth: (width - 64) / 2,
backgroundColor: '#F2F2F7',
padding: 20,
borderRadius: 12,
alignItems: 'center',
},
actionText: {
fontSize: 14,
color: '#1C1C1E',
marginTop: 8,
fontWeight: '500',
},
});
export default PersonalizedDashboard;
