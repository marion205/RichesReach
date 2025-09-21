import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
Image,
Alert,
Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { MockUser } from '../../user/services/MockUserService';
const { width } = Dimensions.get('window');
interface UserProfileCardProps {
user: MockUser;
onNavigate: (screen: string, params?: any) => void;
showFullProfile?: boolean;
onFollowChange?: (isFollowing: boolean) => void;
}
const UserProfileCard: React.FC<UserProfileCardProps> = ({
user,
onNavigate,
showFullProfile = false,
onFollowChange,
}) => {
const handleFollowToggle = () => {
// For now, just call the callback - the parent component will handle the actual follow logic
onFollowChange?.(!user.isFollowingUser);
};
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
if (!user) {
return (
<View style={styles.errorContainer}>
<Icon name="user-x" size={24} color="#FF3B30" />
<Text style={styles.errorText}>No user data available</Text>
</View>
);
}
const publicPortfolios = user.portfolios?.filter((p: any) => p.isPublic) || [];
return (
<View style={[styles.container, showFullProfile && styles.fullProfileContainer]}>
{/* Profile Header */}
<View style={styles.profileHeader}>
<View style={styles.profileImageContainer}>
{user.profilePic ? (
<Image source={{ uri: user.profilePic }} style={styles.profileImage} />
) : (
<View style={styles.profileImagePlaceholder}>
<Text style={styles.profileImageText}>{user.name.charAt(0).toUpperCase()}</Text>
</View>
)}
{user && (
<View style={[styles.experienceBadge, { backgroundColor: getExperienceColor(user.experienceLevel) }]}>
<Icon name={getExperienceIcon(user.experienceLevel)} size={12} color="#FFFFFF" />
</View>
)}
</View>
<View style={styles.profileInfo}>
<Text style={styles.userName}>{user.name}</Text>
{user && (
<Text style={styles.userTitle}>
{user.experienceLevel.charAt(0).toUpperCase()}{user.experienceLevel.slice(1)} Investor
</Text>
)}
<Text style={styles.memberSince}>
Member since {new Date(user.createdAt).getFullYear()}
</Text>
</View>
<TouchableOpacity
style={[
styles.followButton,
user.isFollowingUser && styles.followingButton,
]}
onPress={handleFollowToggle}
>
<Icon
name={user.isFollowingUser ? 'user-check' : 'user-plus'}
size={16}
color={user.isFollowingUser ? '#34C759' : '#007AFF'}
/>
<Text style={[
styles.followButtonText,
user.isFollowingUser && styles.followingButtonText,
]}>
{user.isFollowingUser ? 'Following' : 'Follow'}
</Text>
</TouchableOpacity>
</View>
{/* Stats */}
<View style={styles.statsContainer}>
<TouchableOpacity
style={styles.statItem}
onPress={() => onNavigate('followers', { userId: user.id })}
>
<Text style={styles.statNumber}>{user.followersCount}</Text>
<Text style={styles.statLabel}>Followers</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.statItem}
onPress={() => onNavigate('following', { userId: user.id })}
>
<Text style={styles.statNumber}>{user.followingCount}</Text>
<Text style={styles.statLabel}>Following</Text>
</TouchableOpacity>
<View style={styles.statItem}>
<Text style={styles.statNumber}>{publicPortfolios.length}</Text>
<Text style={styles.statLabel}>Portfolios</Text>
</View>
{user && (
<View style={styles.statItem}>
<Text style={styles.statNumber}>{user.stats.modulesCompleted}</Text>
<Text style={styles.statLabel}>Modules</Text>
</View>
)}
</View>
{/* Investment Profile */}
{user && showFullProfile && (
<View style={styles.investmentProfile}>
<Text style={styles.sectionTitle}>Investment Profile</Text>
<View style={styles.profileRow}>
<Text style={styles.profileLabel}>Experience Level</Text>
<View style={styles.profileValue}>
<View style={[styles.riskIndicator, { backgroundColor: getExperienceColor(user.experienceLevel) }]} />
<Text style={styles.profileText}>
{user.experienceLevel.charAt(0).toUpperCase()}{user.experienceLevel.slice(1)}
</Text>
</View>
</View>
<View style={styles.profileRow}>
<Text style={styles.profileLabel}>Risk Tolerance</Text>
<View style={styles.profileValue}>
<View style={[styles.riskIndicator, { backgroundColor: getRiskColor(user.riskTolerance) }]} />
<Text style={styles.profileText}>
{user.riskTolerance.charAt(0).toUpperCase()}{user.riskTolerance.slice(1)}
</Text>
</View>
</View>
<View style={styles.profileRow}>
<Text style={styles.profileLabel}>Investment Goals</Text>
<View style={styles.goalsContainer}>
{user.investmentGoals?.slice(0, 3).map((goal, index) => (
<View key={index} style={styles.goalTag}>
<Text style={styles.goalText}>
{goal.charAt(0).toUpperCase()}{goal.slice(1).replace('-', ' ')}
</Text>
</View>
))}
{(user.investmentGoals?.length || 0) > 3 && (
<Text style={styles.moreGoalsText}>
+{(user.investmentGoals?.length || 0) - 3} more
</Text>
)}
</View>
</View>
<View style={styles.profileRow}>
<Text style={styles.profileLabel}>Monthly Investment</Text>
<Text style={styles.profileText}>
${user.monthlyInvestment?.toLocaleString()}
</Text>
</View>
</View>
)}
{/* Public Portfolios */}
{publicPortfolios.length > 0 && (
<View style={styles.portfoliosSection}>
<View style={styles.sectionHeader}>
<Text style={styles.sectionTitle}>Public Portfolios</Text>
<TouchableOpacity onPress={() => onNavigate('user-portfolios', { userId: user.id })}>
<Text style={styles.viewAllText}>View All</Text>
</TouchableOpacity>
</View>
{publicPortfolios.slice(0, showFullProfile ? 3 : 2).map((portfolio: any) => (
<TouchableOpacity
key={portfolio.id}
style={styles.portfolioCard}
onPress={() => onNavigate('portfolio-detail', { portfolioId: portfolio.id })}
>
<View style={styles.portfolioHeader}>
<Text style={styles.portfolioName}>{portfolio.name}</Text>
<View style={[
styles.returnBadge,
{ backgroundColor: portfolio.totalReturnPercent >= 0 ? '#E8F5E8' : '#FFE8E8' }
]}>
<Text style={[
styles.returnText,
{ color: portfolio.totalReturnPercent >= 0 ? '#34C759' : '#FF3B30' }
]}>
{portfolio.totalReturnPercent >= 0 ? '+' : ''}{portfolio.totalReturnPercent?.toFixed(2)}%
</Text>
</View>
</View>
<Text style={styles.portfolioDescription}>{portfolio.description}</Text>
<View style={styles.portfolioStats}>
<Text style={styles.portfolioValue}>
${portfolio.totalValue?.toLocaleString()}
</Text>
<Text style={styles.portfolioReturn}>
${portfolio.totalReturn?.toLocaleString()} return
</Text>
</View>
</TouchableOpacity>
))}
</View>
)}
{/* Action Buttons */}
<View style={styles.actionButtons}>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('user-portfolios', { userId: user.id })}
>
<Icon name="pie-chart" size={16} color="#007AFF" />
<Text style={styles.actionButtonText}>View Portfolios</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('user-activity', { userId: user.id })}
>
<Icon name="activity" size={16} color="#34C759" />
<Text style={styles.actionButtonText}>Activity</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('message-user', { userId: user.id })}
>
<Icon name="message-circle" size={16} color="#FF9500" />
<Text style={styles.actionButtonText}>Message</Text>
</TouchableOpacity>
</View>
</View>
);
};
const styles = StyleSheet.create({
container: {
backgroundColor: '#FFFFFF',
borderRadius: 16,
padding: 20,
marginHorizontal: 16,
marginVertical: 8,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
fullProfileContainer: {
marginHorizontal: 16,
marginVertical: 16,
},
loadingContainer: {
padding: 20,
alignItems: 'center',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
errorContainer: {
padding: 20,
alignItems: 'center',
},
errorText: {
fontSize: 16,
color: '#FF3B30',
marginTop: 8,
},
// Profile Header
profileHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 16,
},
profileImageContainer: {
position: 'relative',
marginRight: 16,
},
profileImage: {
width: 60,
height: 60,
borderRadius: 30,
},
profileImagePlaceholder: {
width: 60,
height: 60,
borderRadius: 30,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
},
profileImageText: {
fontSize: 24,
fontWeight: 'bold',
color: '#FFFFFF',
},
experienceBadge: {
position: 'absolute',
bottom: -2,
right: -2,
width: 20,
height: 20,
borderRadius: 10,
justifyContent: 'center',
alignItems: 'center',
borderWidth: 2,
borderColor: '#FFFFFF',
},
profileInfo: {
flex: 1,
},
userName: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
userTitle: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
marginBottom: 2,
},
memberSince: {
fontSize: 12,
color: '#8E8E93',
},
followButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 8,
paddingHorizontal: 16,
borderRadius: 20,
borderWidth: 1,
borderColor: '#007AFF',
backgroundColor: 'transparent',
},
followingButton: {
backgroundColor: '#E8F5E8',
borderColor: '#34C759',
},
followButtonText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
marginLeft: 4,
},
followingButtonText: {
color: '#34C759',
},
// Stats
statsContainer: {
flexDirection: 'row',
justifyContent: 'space-around',
paddingVertical: 16,
borderTopWidth: 1,
borderBottomWidth: 1,
borderColor: '#E5E5EA',
marginBottom: 16,
},
statItem: {
alignItems: 'center',
},
statNumber: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 4,
},
statLabel: {
fontSize: 12,
color: '#8E8E93',
},
// Investment Profile
investmentProfile: {
marginBottom: 20,
},
sectionTitle: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 12,
},
profileRow: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 12,
},
profileLabel: {
fontSize: 14,
color: '#8E8E93',
flex: 1,
},
profileValue: {
flexDirection: 'row',
alignItems: 'center',
flex: 1,
justifyContent: 'flex-end',
},
riskIndicator: {
width: 8,
height: 8,
borderRadius: 4,
marginRight: 8,
},
profileText: {
fontSize: 14,
color: '#1C1C1E',
fontWeight: '500',
},
goalsContainer: {
flexDirection: 'row',
flexWrap: 'wrap',
flex: 1,
justifyContent: 'flex-end',
},
goalTag: {
backgroundColor: '#F2F2F7',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
marginLeft: 4,
marginBottom: 4,
},
goalText: {
fontSize: 12,
color: '#1C1C1E',
},
moreGoalsText: {
fontSize: 12,
color: '#8E8E93',
marginLeft: 8,
},
// Portfolios Section
portfoliosSection: {
marginBottom: 20,
},
sectionHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 12,
},
viewAllText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
},
portfolioCard: {
backgroundColor: '#F2F2F7',
borderRadius: 12,
padding: 16,
marginBottom: 12,
},
portfolioHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
portfolioName: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
flex: 1,
},
returnBadge: {
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
},
returnText: {
fontSize: 12,
fontWeight: '600',
},
portfolioDescription: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 12,
lineHeight: 20,
},
portfolioStats: {
flexDirection: 'row',
justifyContent: 'space-between',
},
portfolioValue: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
},
portfolioReturn: {
fontSize: 14,
color: '#8E8E93',
},
// Action Buttons
actionButtons: {
flexDirection: 'row',
justifyContent: 'space-between',
paddingHorizontal: 8,
},
actionButton: {
flexDirection: 'column',
alignItems: 'center',
paddingVertical: 12,
paddingHorizontal: 8,
borderRadius: 20,
backgroundColor: '#F2F2F7',
flex: 1,
marginHorizontal: 2,
justifyContent: 'center',
},
actionButtonText: {
fontSize: 12,
color: '#1C1C1E',
marginTop: 4,
fontWeight: '500',
textAlign: 'center',
},
});
export default UserProfileCard;
