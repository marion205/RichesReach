import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
Image,
RefreshControl,
Alert,
SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import UserProfileCard from '../components/UserProfileCard';
import MockUserService, { MockUser } from '../services/MockUserService';
interface UserProfileScreenProps {
userId: string;
onNavigate: (screen: string, params?: any) => void;
}
const UserProfileScreen: React.FC<UserProfileScreenProps> = ({ userId, onNavigate }) => {
const [refreshing, setRefreshing] = useState(false);
const [user, setUser] = useState<MockUser | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [renderKey, setRenderKey] = useState(0);
const mockUserService = MockUserService.getInstance();
// Load user profile from mock service
const loadUserProfile = () => {
setLoading(true);
setError(null);
try {
const userProfile = mockUserService.getUserById(userId);
if (userProfile) {
setUser(userProfile);
} else {
setError('User not found');
}
} catch (err) {
setError('Failed to load user profile');
console.error('Error loading user profile:', err);
} finally {
setLoading(false);
}
};
const handleRefresh = async () => {
setRefreshing(true);
try {
loadUserProfile();
} catch (error) {
console.error('Error refreshing profile:', error);
} finally {
setRefreshing(false);
}
};
const handleFollowToggle = async (isFollowing: boolean) => {
if (!user) return;
try {
const result = mockUserService.toggleFollow(userId);
if (result.success) {
// Reload user profile to reflect the change
loadUserProfile();
// Force re-render of UserProfileCard
setRenderKey(prev => prev + 1);
} else {
Alert.alert('Error', result.message);
}
} catch (error) {
console.error('Error toggling follow:', error);
Alert.alert('Error', 'Failed to update follow status. Please try again.');
}
};
// Load user profile when component mounts
useEffect(() => {
loadUserProfile();
}, [userId]);
if (loading) {
return (
<SafeAreaView style={styles.container}>
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading profile...</Text>
</View>
</SafeAreaView>
);
}
if (error || !user) {
return (
<SafeAreaView style={styles.container}>
<View style={styles.errorContainer}>
<Icon name="user-x" size={48} color="#FF3B30" />
<Text style={styles.errorTitle}>Profile Not Found</Text>
<Text style={styles.errorText}>
Unable to load this user's profile.
</Text>
<TouchableOpacity
style={styles.backButtonAction}
onPress={() => onNavigate('social')}
>
<Text style={styles.backButtonText}>Go Back</Text>
</TouchableOpacity>
</View>
</SafeAreaView>
);
}
const publicPortfolios = user.portfolios?.filter(p => p.isPublic) || [];
return (
<SafeAreaView style={styles.container}>
{/* Header */}
<View style={styles.header}>
<TouchableOpacity
style={styles.backButton}
onPress={() => onNavigate('social')}
>
<Icon name="arrow-left" size={24} color="#007AFF" />
</TouchableOpacity>
<Text style={styles.headerTitle}>Profile</Text>
<TouchableOpacity
style={styles.followButton}
onPress={handleFollowToggle}
>
<Icon
name={user.isFollowingUser ? 'user-check' : 'user-plus'}
size={20}
color={user.isFollowingUser ? '#34C759' : '#007AFF'}
/>
</TouchableOpacity>
</View>
<ScrollView
style={styles.content}
refreshControl={
<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
}
showsVerticalScrollIndicator={false}
>
<UserProfileCard
key={`${user?.id}-${renderKey}`}
user={user}
onNavigate={onNavigate}
showFullProfile={true}
onFollowChange={handleFollowToggle}
/>
</ScrollView>
</SafeAreaView>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
header: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
paddingHorizontal: 16,
paddingVertical: 12,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
backButton: {
padding: 8,
},
headerTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1C1C1E',
},
followButton: {
padding: 8,
},
content: {
flex: 1,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 40,
},
errorTitle: {
fontSize: 20,
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
errorText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
marginBottom: 24,
},
backButtonAction: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 20,
},
backButtonText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
},
});
export default UserProfileScreen;
