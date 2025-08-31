import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  Image,
} from 'react-native';
import { gql, useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';

const GET_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
      email
      profilePic
      followersCount
      followingCount
      isFollowingUser
      isFollowedByUser
    }
  }
`;

const GET_ME = gql`
  query GetMe {
    me {
      id
      name
      email
      profilePic
    }
  }
`;

const GET_USER_POSTS = gql`
  query GetUserPosts($userId: ID!) {
    userPosts(userId: $userId) {
      id
      content
      createdAt
      likesCount
      commentsCount
      isLikedByUser
      user {
        id
        name
      }
    }
  }
`;

const TOGGLE_FOLLOW = gql`
  mutation ToggleFollow($userId: ID!) {
    toggleFollow(userId: $userId) {
      user {
        id
        followersCount
        followingCount
        isFollowingUser
        isFollowedByUser
      }
      following
    }
  }
`;

type User = {
  id: string;
  name: string;
  email: string;
  followersCount: number;
  followingCount: number;
  isFollowingUser: boolean;
  isFollowedByUser: boolean;
};

type Post = {
  id: string;
  content: string;
  createdAt: string;
  likesCount: number;
  commentsCount: number;
  isLikedByUser: boolean;
  user: {
    id: string;
    name: string;
  };
};

export default function ProfileScreen({ navigateTo, data }) {
  // Remove the insets usage since we're not using safe area context anymore
  
  // @ts-ignore
  const userId = data?.userId;
  
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(GET_USER, {
    variables: { id: userId },
    skip: !userId,
  });
  
  const { data: postsData, loading: postsLoading, refetch: refetchPosts } = useQuery(GET_USER_POSTS, {
    variables: { userId },
    skip: !userId,
  });
  
  const { data: meData, loading: meLoading } = useQuery(GET_ME);
  
  const [toggleFollow] = useMutation(TOGGLE_FOLLOW);
  const [refreshing, setRefreshing] = useState(false);

  const user: User | null = userData?.user;
  const posts: Post[] = postsData?.userPosts || [];

  const handleToggleFollow = async () => {
    if (!user) return;
    
    try {
      await toggleFollow({
        variables: { userId: user.id },
      });
      // Clear cache and refetch to ensure fresh data
      await client.resetStore();
      await refetchUser();
    } catch (error) {
      console.error('Failed to toggle follow:', error);
      Alert.alert('Error', 'Failed to follow/unfollow user. Please try again.');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchUser(), refetchPosts()]);
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setRefreshing(false);
    }
  };

  if (userLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  if (!user) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>User not found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: 50 }]}>
        <TouchableOpacity onPress={() => navigateTo('Back')}>
          <Icon name="arrow-left" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={['#00cc99']}
            tintColor="#00cc99"
          />
        }
      >
        {/* User Info */}
        <View style={styles.userInfo}>
          <View style={styles.avatar}>
            {!meLoading && meData?.me?.profilePic ? (
              <Image 
                source={{ uri: meData.me.profilePic }} 
                style={styles.avatarImage} 
              />
            ) : (
              <Text style={styles.avatarText}>{user.name.charAt(0).toUpperCase()}</Text>
            )}
          </View>
          
          <Text style={styles.userName}>{user.name}</Text>
          <Text style={styles.userEmail}>{user.email}</Text>
          
          <View style={styles.stats}>
            <View style={styles.stat}>
              <Text style={styles.statNumber}>{posts.length}</Text>
              <Text style={styles.statLabel}>Posts</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statNumber}>{user.followersCount}</Text>
              <Text style={styles.statLabel}>Followers</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statNumber}>{user.followingCount}</Text>
              <Text style={styles.statLabel}>Following</Text>
            </View>
          </View>
          
                     {!meLoading && meData?.me?.id && meData.me.id !== user.id && (
            <TouchableOpacity
              style={[
                styles.followButton,
                user.isFollowingUser && styles.followingButton
              ]}
              onPress={handleToggleFollow}
            >
              <Icon 
                name={user.isFollowingUser ? "user-check" : "user-plus"} 
                size={16} 
                color={user.isFollowingUser ? "#fff" : "#00cc99"} 
              />
              <Text style={[
                styles.followButtonText,
                user.isFollowingUser && styles.followingButtonText
              ]}>
                {user.isFollowingUser ? "Following" : "Follow"}
              </Text>
            </TouchableOpacity>
          )}
          
          {/* Logout button for own profile */}
                     {!meLoading && meData?.me?.id && meData.me.id === user.id && (
            <TouchableOpacity
              style={styles.logoutButton}
              onPress={async () => {
                await AsyncStorage.removeItem('token');
                Alert.alert('Logged out', 'You have been successfully logged out.');
                // @ts-ignore
                navigateTo('Login');
              }}
            >
              <Icon name="log-out" size={16} color="#ff4757" />
              <Text style={styles.logoutButtonText}>Logout</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Posts */}
        <View style={styles.postsSection}>
          <Text style={styles.sectionTitle}>Posts</Text>
          
          {postsLoading ? (
            <Text style={styles.loadingText}>Loading posts...</Text>
          ) : posts.length === 0 ? (
            <Text style={styles.emptyText}>No posts yet</Text>
          ) : (
            posts.map((post) => (
              <View key={post.id} style={styles.postCard}>
                <Text style={styles.postContent}>{post.content}</Text>
                <View style={styles.postMeta}>
                  <Text style={styles.postDate}>
                    {new Date(post.createdAt).toLocaleDateString()}
                  </Text>
                  <View style={styles.postStats}>
                    <Icon name="heart" size={14} color="#666" />
                    <Text style={styles.postStat}>{post.likesCount}</Text>
                    <Icon name="message-circle" size={14} color="#666" />
                    <Text style={styles.postStat}>{post.commentsCount}</Text>
                  </View>
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  userInfo: {
    alignItems: 'center',
    padding: 30,
    backgroundColor: '#fff',
    margin: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#00cc99',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 15,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  userEmail: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  stat: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  followButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#00cc99',
    backgroundColor: 'transparent',
  },
  followingButton: {
    backgroundColor: '#00cc99',
  },
  followButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  followingButtonText: {
    color: '#fff',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ff4757',
    backgroundColor: 'transparent',
    marginTop: 10,
  },
  logoutButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ff4757',
  },
  postsSection: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  postCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  postContent: {
    fontSize: 16,
    marginBottom: 10,
  },
  postMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postDate: {
    fontSize: 12,
    color: '#666',
  },
  postStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  postStat: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
    marginRight: 10,
  },
  loadingText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    marginTop: 50,
  },
  errorText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#ff4757',
    marginTop: 50,
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    marginTop: 20,
  },
});
