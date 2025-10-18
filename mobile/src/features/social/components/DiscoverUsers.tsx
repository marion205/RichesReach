import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
FlatList,
TextInput,
Image,
RefreshControl,
Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { gql, useQuery, useMutation } from '@apollo/client';
import UserProfileCard from '../../UserProfileCard';
import { User } from '../../../types/social';
// Mock data for Discover tab - showing 10+ users since everything is brand new
// GraphQL Queries
const GET_DISCOVER_USERS = gql`
query GetDiscoverUsers($limit: Int, $offset: Int, $searchTerm: String, $experienceLevel: String, $sortBy: String) {
discoverUsers(limit: $limit, offset: $offset, searchTerm: $searchTerm, experienceLevel: $experienceLevel, sortBy: $sortBy) {
id
name
email
profilePic
followersCount
followingCount
isFollowingUser
isFollowedByUser
createdAt
experienceLevel
riskTolerance
investmentGoals
monthlyInvestment
portfolios {
id
name
isPublic
totalValue
totalReturnPercent
}
stats {
totalLearningTime
modulesCompleted
achievements
streakDays
}
}
}
`;
const FOLLOW_USER = gql`
mutation FollowUser($userId: ID!) {
followUser(userId: $userId) {
success
message
}
}
`;
const UNFOLLOW_USER = gql`
mutation UnfollowUser($userId: ID!) {
unfollowUser(userId: $userId) {
success
message
}
}
`;
interface DiscoverUsersProps {
onNavigate: (screen: string, params?: any) => void;
}
// Mock user data for Discover tab - showing 10+ users since everything is brand new
const MOCK_USERS = [
  { id: '1', name: 'Alex Chen', email: 'alex@example.com', profilePic: null, followersCount: 1250, followingCount: 340, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'advanced', bio: 'Quantitative analyst with 8 years experience', totalReturnPercent: 15.2 },
  { id: '2', name: 'Sarah Johnson', email: 'sarah@example.com', profilePic: null, followersCount: 890, followingCount: 210, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'intermediate', bio: 'Growth investor focused on tech stocks', totalReturnPercent: 8.7 },
  { id: '3', name: 'Mike Rodriguez', email: 'mike@example.com', profilePic: null, followersCount: 2100, followingCount: 450, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'advanced', bio: 'Options trader and market strategist', totalReturnPercent: 22.1 },
  { id: '4', name: 'Emma Wilson', email: 'emma@example.com', profilePic: null, followersCount: 650, followingCount: 180, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'beginner', bio: 'Learning about value investing', totalReturnPercent: 3.2 },
  { id: '5', name: 'David Kim', email: 'david@example.com', profilePic: null, followersCount: 1800, followingCount: 320, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'advanced', bio: 'Crypto and DeFi enthusiast', totalReturnPercent: 45.8 },
  { id: '6', name: 'Lisa Thompson', email: 'lisa@example.com', profilePic: null, followersCount: 420, followingCount: 95, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'intermediate', bio: 'Dividend investor and REIT specialist', totalReturnPercent: 12.4 },
  { id: '7', name: 'James Brown', email: 'james@example.com', profilePic: null, followersCount: 1500, followingCount: 280, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'advanced', bio: 'Hedge fund manager and risk analyst', totalReturnPercent: 18.9 },
  { id: '8', name: 'Maria Garcia', email: 'maria@example.com', profilePic: null, followersCount: 750, followingCount: 150, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'intermediate', bio: 'ESG investing advocate', totalReturnPercent: 9.6 },
  { id: '9', name: 'Tom Anderson', email: 'tom@example.com', profilePic: null, followersCount: 320, followingCount: 80, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'beginner', bio: 'New to investing, learning fundamentals', totalReturnPercent: 1.8 },
  { id: '10', name: 'Rachel Davis', email: 'rachel@example.com', profilePic: null, followersCount: 1100, followingCount: 240, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'intermediate', bio: 'Sector rotation specialist', totalReturnPercent: 14.3 },
  { id: '11', name: 'Kevin Lee', email: 'kevin@example.com', profilePic: null, followersCount: 950, followingCount: 190, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'intermediate', bio: 'Technical analysis expert', totalReturnPercent: 11.7 },
  { id: '12', name: 'Amanda White', email: 'amanda@example.com', profilePic: null, followersCount: 680, followingCount: 120, isFollowingUser: false, isFollowedByUser: false, experienceLevel: 'beginner', bio: 'Index fund investor', totalReturnPercent: 6.2 },
];

const DiscoverUsers: React.FC<DiscoverUsersProps> = ({ onNavigate }) => {
const [searchTerm, setSearchTerm] = useState('');
const [selectedExperience, setSelectedExperience] = useState<string>('');
const [sortBy, setSortBy] = useState('followers');
const [refreshing, setRefreshing] = useState(false);
const [users, setUsers] = useState<any[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// Load users from mock data
const loadUsers = () => {
setLoading(true);
setError(null);
try {
// Filter users based on search and experience level
let filteredUsers = MOCK_USERS.filter(user => {
  const matchesSearch = !searchTerm || user.name.toLowerCase().includes(searchTerm.toLowerCase());
  const matchesExperience = !selectedExperience || user.experienceLevel === selectedExperience;
  return matchesSearch && matchesExperience;
});

// Sort users
if (sortBy === 'followers') {
  filteredUsers.sort((a, b) => b.followersCount - a.followersCount);
}

setUsers(filteredUsers);
} catch (err) {
setError('Failed to load users');
console.error('Error loading users:', err);
} finally {
setLoading(false);
}
};
const handleRefresh = async () => {
setRefreshing(true);
try {
loadUsers();
} catch (error) {
console.error('Error refreshing users:', error);
} finally {
setRefreshing(false);
}
};
const handleFollowToggle = async (userId: string, isFollowing: boolean) => {
try {
// Update local state to reflect the follow toggle
setUsers(prevUsers => 
  prevUsers.map(user => 
    user.id === userId 
      ? { 
          ...user, 
          isFollowingUser: !isFollowing,
          followersCount: isFollowing ? user.followersCount - 1 : user.followersCount + 1
        }
      : user
  )
);
} catch (error) {
console.error('Error toggling follow:', error);
Alert.alert('Error', 'Failed to update follow status. Please try again.');
}
};
// Load users when component mounts or filters change
useEffect(() => {
loadUsers();
}, [searchTerm, selectedExperience, sortBy]);
const experienceLevels = [
{ id: '', label: 'All Levels', icon: 'users' },
{ id: 'beginner', label: 'Beginners', icon: 'book-open' },
{ id: 'intermediate', label: 'Intermediate', icon: 'trending-up' },
{ id: 'advanced', label: 'Advanced', icon: 'bar-chart-2' },
];
const sortOptions = [
{ id: 'followers', label: 'Most Followers', icon: 'users' },
{ id: 'recent', label: 'Recently Joined', icon: 'clock' },
{ id: 'performance', label: 'Best Performance', icon: 'trending-up' },
{ id: 'activity', label: 'Most Active', icon: 'activity' },
];
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
const renderUserCard = (user: any) => (
<View key={user.id} style={styles.userCard}>
<View style={styles.userHeader}>
<View style={styles.userImageContainer}>
{user.profilePic ? (
<Image source={{ uri: user.profilePic }} style={styles.userImage} />
) : (
<View style={styles.userImagePlaceholder}>
<Text style={styles.userImageText}>{user.name.charAt(0).toUpperCase()}</Text>
</View>
)}
<View style={[styles.experienceBadge, { backgroundColor: getExperienceColor(user.experienceLevel) }]}>
<Icon name={getExperienceIcon(user.experienceLevel)} size={10} color="#FFFFFF" />
</View>
</View>
<View style={styles.userInfo}>
<Text style={styles.userName}>{user.name}</Text>
<Text style={styles.userTitle}>
{user.experienceLevel.charAt(0).toUpperCase()}{user.experienceLevel.slice(1)} Investor
</Text>
<Text style={styles.memberSince}>
Member since {new Date(user.createdAt).getFullYear()}
</Text>
</View>
<TouchableOpacity
style={[
styles.followButton,
user.isFollowingUser && styles.followingButton,
]}
onPress={() => handleFollowToggle(user.id, user.isFollowingUser)}
>
<Icon
name={user.isFollowingUser ? 'user-check' : 'user-plus'}
size={14}
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
<View style={styles.userStats}>
<View style={styles.statItem}>
<Text style={styles.statNumber}>{user.followersCount}</Text>
<Text style={styles.statLabel}>Followers</Text>
</View>
<View style={styles.statItem}>
<Text style={styles.statNumber}>{user.followingCount}</Text>
<Text style={styles.statLabel}>Following</Text>
</View>
<View style={styles.statItem}>
<Text style={styles.statNumber}>{user.portfolios?.filter((p: any) => p.isPublic).length || 0}</Text>
<Text style={styles.statLabel}>Portfolios</Text>
</View>
<View style={styles.statItem}>
<Text style={styles.statNumber}>{user.stats?.modulesCompleted || 0}</Text>
<Text style={styles.statLabel}>Modules</Text>
</View>
</View>
{user.portfolios && user.portfolios.length > 0 && (
<View style={styles.portfolioPreview}>
<Text style={styles.portfolioPreviewTitle}>Public Portfolios</Text>
{user.portfolios.filter((p: any) => p.isPublic).slice(0, 2).map((portfolio: any) => (
<View key={portfolio.id} style={styles.portfolioItem}>
<Text style={styles.portfolioName}>{portfolio.name}</Text>
<View style={[
styles.portfolioReturn,
{ backgroundColor: portfolio.totalReturnPercent >= 0 ? '#E8F5E8' : '#FFE8E8' }
]}>
<Text style={[
styles.portfolioReturnText,
{ color: portfolio.totalReturnPercent >= 0 ? '#34C759' : '#FF3B30' }
]}>
{portfolio.totalReturnPercent >= 0 ? '+' : ''}{portfolio.totalReturnPercent.toFixed(1)}%
</Text>
</View>
</View>
))}
</View>
)}
<View style={styles.userActions}>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('user-profile', { userId: user.id })}
>
<Icon name="user" size={16} color="#007AFF" />
<Text style={styles.actionButtonText}>View Profile</Text>
</TouchableOpacity>
<TouchableOpacity
style={styles.actionButton}
onPress={() => onNavigate('user-portfolios', { userId: user.id })}
>
<Icon name="pie-chart" size={16} color="#34C759" />
<Text style={styles.actionButtonText}>Portfolios</Text>
</TouchableOpacity>
</View>
</View>
);
return (
<View style={styles.container}>
{/* Search and Filters */}
<View style={styles.searchSection}>
<View style={styles.searchContainer}>
<Icon name="search" size={20} color="#8E8E93" />
<TextInput
style={styles.searchInput}
placeholder="Search investors..."
value={searchTerm}
onChangeText={setSearchTerm}
placeholderTextColor="#8E8E93"
/>
{searchTerm.length > 0 && (
<TouchableOpacity onPress={() => setSearchTerm('')}>
<Icon name="x" size={20} color="#8E8E93" />
</TouchableOpacity>
)}
</View>
{/* Experience Level Filter */}
<ScrollView
horizontal
showsHorizontalScrollIndicator={false}
style={styles.filterContainer}
>
{experienceLevels.map((level) => (
<TouchableOpacity
key={level.id}
style={[
styles.filterChip,
selectedExperience === level.id && styles.filterChipSelected,
]}
onPress={() => setSelectedExperience(level.id)}
>
<Icon
name={level.icon}
size={16}
color={selectedExperience === level.id ? '#007AFF' : '#8E8E93'}
/>
<Text style={[
styles.filterChipText,
selectedExperience === level.id && styles.filterChipTextSelected,
]}>
{level.label}
</Text>
</TouchableOpacity>
))}
</ScrollView>
{/* Sort Options */}
<ScrollView
horizontal
showsHorizontalScrollIndicator={false}
style={styles.sortContainer}
>
{sortOptions.map((option) => (
<TouchableOpacity
key={option.id}
style={[
styles.sortChip,
sortBy === option.id && styles.sortChipSelected,
]}
onPress={() => setSortBy(option.id)}
>
<Icon
name={option.icon}
size={14}
color={sortBy === option.id ? '#007AFF' : '#8E8E93'}
/>
<Text style={[
styles.sortChipText,
sortBy === option.id && styles.sortChipTextSelected,
]}>
{option.label}
</Text>
</TouchableOpacity>
))}
</ScrollView>
</View>
{/* Users List */}
<FlatList
  style={styles.content}
  data={users || []}
  keyExtractor={(item) => item.id}
  renderItem={({ item }) => renderUserCard(item)}
  refreshControl={
    <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
  }
  showsVerticalScrollIndicator={false}
  ListEmptyComponent={
    loading ? (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Finding investors...</Text>
      </View>
    ) : error ? (
      <View style={styles.errorContainer}>
        <Icon name="users" size={48} color="#8E8E93" />
        <Text style={styles.errorText}>Welcome to the community!</Text>
        <Text style={styles.errorSubText}>
          We're building something amazing here. Check back soon to discover other investors and traders.
        </Text>
        <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
          <Text style={styles.retryButtonText}>Refresh</Text>
        </TouchableOpacity>
      </View>
    ) : (
      <View style={styles.emptyContainer}>
        <Icon name="users" size={48} color="#8E8E93" />
        <Text style={styles.emptyTitle}>No Investors Found</Text>
        <Text style={styles.emptyText}>
          Try adjusting your search criteria or filters
        </Text>
      </View>
    )
  }
  contentContainerStyle={!users || users.length === 0 ? styles.emptyContainer : undefined}
/>
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
// Search Section
searchSection: {
backgroundColor: '#FFFFFF',
paddingHorizontal: 16,
paddingVertical: 12,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
searchContainer: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F2F2F7',
borderRadius: 12,
paddingHorizontal: 12,
paddingVertical: 8,
marginBottom: 12,
},
searchInput: {
flex: 1,
fontSize: 16,
color: '#1C1C1E',
marginLeft: 8,
},
filterContainer: {
marginBottom: 8,
},
filterChip: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 12,
paddingVertical: 6,
borderRadius: 16,
backgroundColor: '#F2F2F7',
marginRight: 8,
borderWidth: 1,
borderColor: 'transparent',
},
filterChipSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
filterChipText: {
fontSize: 14,
color: '#8E8E93',
marginLeft: 6,
},
filterChipTextSelected: {
color: '#007AFF',
fontWeight: '600',
},
sortContainer: {
marginBottom: 4,
},
sortChip: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 10,
paddingVertical: 4,
borderRadius: 12,
backgroundColor: '#F2F2F7',
marginRight: 6,
borderWidth: 1,
borderColor: 'transparent',
},
sortChipSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
sortChipText: {
fontSize: 12,
color: '#8E8E93',
marginLeft: 4,
},
sortChipTextSelected: {
color: '#007AFF',
fontWeight: '600',
},
// Content
content: {
flex: 1,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 20,
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 20,
},
errorText: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 12,
marginBottom: 8,
textAlign: 'center',
},
errorSubText: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 20,
textAlign: 'center',
lineHeight: 20,
},
retryButton: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 20,
},
retryButtonText: {
fontSize: 16,
color: '#FFFFFF',
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
fontWeight: 'bold',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
emptyText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
},
// User Card
userCard: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
userHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 12,
},
userImageContainer: {
position: 'relative',
marginRight: 12,
},
userImage: {
width: 50,
height: 50,
borderRadius: 25,
},
userImagePlaceholder: {
width: 50,
height: 50,
borderRadius: 25,
backgroundColor: '#007AFF',
justifyContent: 'center',
alignItems: 'center',
},
userImageText: {
fontSize: 20,
fontWeight: 'bold',
color: '#FFFFFF',
},
experienceBadge: {
position: 'absolute',
bottom: -2,
right: -2,
width: 16,
height: 16,
borderRadius: 8,
justifyContent: 'center',
alignItems: 'center',
borderWidth: 2,
borderColor: '#FFFFFF',
},
userInfo: {
flex: 1,
},
userName: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 2,
},
userTitle: {
fontSize: 12,
color: '#007AFF',
fontWeight: '600',
marginBottom: 2,
},
memberSince: {
fontSize: 10,
color: '#8E8E93',
},
followButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 6,
paddingHorizontal: 12,
borderRadius: 16,
borderWidth: 1,
borderColor: '#007AFF',
backgroundColor: 'transparent',
},
followingButton: {
backgroundColor: '#E8F5E8',
borderColor: '#34C759',
},
followButtonText: {
fontSize: 12,
color: '#007AFF',
fontWeight: '600',
marginLeft: 4,
},
followingButtonText: {
color: '#34C759',
},
// User Stats
userStats: {
flexDirection: 'row',
justifyContent: 'space-around',
paddingVertical: 12,
borderTopWidth: 1,
borderBottomWidth: 1,
borderColor: '#E5E5EA',
marginBottom: 12,
},
statItem: {
alignItems: 'center',
},
statNumber: {
fontSize: 16,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 2,
},
statLabel: {
fontSize: 10,
color: '#8E8E93',
},
// Portfolio Preview
portfolioPreview: {
marginBottom: 12,
},
portfolioPreviewTitle: {
fontSize: 12,
fontWeight: '600',
color: '#8E8E93',
marginBottom: 8,
},
portfolioItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 4,
},
portfolioName: {
fontSize: 14,
color: '#1C1C1E',
flex: 1,
},
portfolioReturn: {
paddingHorizontal: 6,
paddingVertical: 2,
borderRadius: 8,
},
portfolioReturnText: {
fontSize: 10,
fontWeight: '600',
},
// User Actions
userActions: {
flexDirection: 'row',
justifyContent: 'space-around',
},
actionButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 8,
paddingHorizontal: 12,
borderRadius: 16,
backgroundColor: '#F2F2F7',
},
actionButtonText: {
fontSize: 12,
color: '#1C1C1E',
marginLeft: 4,
fontWeight: '500',
},
});
export default DiscoverUsers;
