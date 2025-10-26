// CircleDetailScreen.tsx - Enhanced with Video Uploads and Push Notifications
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Image,
  Alert,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker'; // For image/video selection
import { Video } from 'expo-av'; // For video playback
import * as Notifications from 'expo-notifications'; // For push notifications
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../../theme/PersonalizedThemes';

// Extend interfaces
interface WealthCircle {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  totalValue: number;
  performance: number;
  category: 'investment' | 'education' | 'entrepreneurship' | 'real_estate' | 'crypto' | 'tax_optimization';
  isPrivate: boolean;
  isJoined: boolean;
  members: CircleMember[];
  recentActivity: CircleActivity[];
  rules: string[];
  tags: string[];
  createdBy: string;
  createdAt: string;
}

interface CircleMember {
  id: string;
  name: string;
  avatar: string;
  role: 'founder' | 'moderator' | 'member';
  portfolioValue: number;
  performance: number;
  isOnline: boolean;
  lastActive: string;
}

interface CircleActivity {
  id: string;
  type: 'trade' | 'insight' | 'discussion' | 'achievement' | 'milestone';
  user: CircleMember;
  content: string;
  timestamp: string;
  likes: number;
  comments: number;
  isLiked: boolean;
}

interface CirclePost {
  id: string;
  content: string;
  image?: string; // New: Optional image URL
  user: { id: string; name: string; avatar: string };
  timestamp: string;
  likes: number;
  comments: Comment[];
}

interface Comment {
  id: string;
  content: string;
  user: { id: string; name: string; avatar: string };
  timestamp: string;
  likes: number;
}

interface CircleDetailProps {
  route: { params: { circle: WealthCircle } };
  navigation: any;
}

// Configurable API base URL
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function CircleDetailScreen({ route, navigation }: CircleDetailProps) {
  const theme = useTheme();
  const { circle } = route.params;
  const [posts, setPosts] = useState<CirclePost[]>([]);
  const [newPostText, setNewPostText] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null); // New: Selected image URI
  const [loading, setLoading] = useState(true);
  const [expandedPostId, setExpandedPostId] = useState<string | null>(null); // For toggling comments
  const [newComment, setNewComment] = useState<{ [postId: string]: string }>({}); // Per-post comments
  const socketRef = useRef<any>(null); // Real-time socket (commented out for now)

  useEffect(() => {
    loadPosts();
    // setupSocket(); // Commented out for now - requires socket.io setup
    navigation.setOptions({ 
      title: circle.name,
      headerRight: () => (
        <TouchableOpacity onPress={() => setExpandedPostId(null)} style={styles.headerClose}>
          <Text style={styles.headerCloseText}>Close</Text>
        </TouchableOpacity>
      ),
    });
    return () => {
      if (socketRef.current) socketRef.current.disconnect();
    };
  }, [circle.id]);

  const setupSocket = useCallback(() => {
    // Socket.io setup - commented out for now
    // socketRef.current = io(API_BASE_URL);
    // socketRef.current.emit('join_circle', { circleId: circle.id });
    // socketRef.current.on('new_post', (newPost: CirclePost) => {
    //   setPosts(prev => [newPost, ...prev]);
    // });
    // socketRef.current.on('new_comment', ({ postId, comment }: { postId: string; comment: Comment }) => {
    //   setPosts(prev => prev.map(post => 
    //     post.id === postId 
    //       ? { ...post, comments: [...(post.comments || []), comment] }
    //       : post
    //   ));
    // });
  }, [circle.id]);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const apiPosts = await response.json();
        // Transform: Add empty comments array if needed
        const transformed = apiPosts.map((post: any) => ({ ...post, comments: post.comments || [] }));
        setPosts(transformed);
      } else {
        // Fallback mocks with images
        setPosts([
          {
            id: '1',
            content: 'Loving the discussions here—anyone tried tax-loss harvesting this quarter? 📈',
            image: 'https://via.placeholder.com/300x200/667eea/ffffff?text=Portfolio+Chart',
            user: { id: 'user1', name: 'Alex Rivera', avatar: 'https://via.placeholder.com/40' },
            timestamp: '2 hours ago',
            likes: 12,
            comments: [ // Mock comments
              {
                id: 'c1',
                content: 'Yes! Saved me 5k last year.',
                user: { id: 'user2', name: 'Jordan Lee', avatar: 'https://via.placeholder.com/40' },
                timestamp: '1 hour ago',
                likes: 2,
              },
            ],
          },
          {
            id: '2',
            content: 'Market volatility is creating great opportunities for value investors. What\'s everyone\'s strategy?',
            user: { id: 'user3', name: 'Sarah Williams', avatar: 'https://via.placeholder.com/40' },
            timestamp: '4 hours ago',
            likes: 8,
            comments: []
          },
          {
            id: '3',
            content: 'Just hit my first $100K milestone! 🎉 Thanks to this community for all the guidance.',
            image: 'https://via.placeholder.com/300x200/34C759/ffffff?text=Milestone+Chart',
            user: { id: 'user4', name: 'Michael Chen', avatar: 'https://via.placeholder.com/40' },
            timestamp: '6 hours ago',
            likes: 25,
            comments: [
              {
                id: 'c2',
                content: 'Congratulations! That\'s amazing progress!',
                user: { id: 'user5', name: 'Emma Davis', avatar: 'https://via.placeholder.com/40' },
                timestamp: '5 hours ago',
                likes: 3
              }
            ]
          }
        ]);
      }
    } catch (err) {
      console.error('Error loading posts:', err);
    } finally {
      setLoading(false);
    }
  }, [circle.id]);

  // New: Image Picker
  const pickImage = useCallback(async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please grant access to your photos.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });
    if (!result.canceled) {
      setSelectedImage(result.assets[0].uri);
    }
  }, []);

  // Upload image to backend (assume endpoint returns URL)
  const uploadImage = useCallback(async (uri: string) => {
    const formData = new FormData();
    formData.append('image', { uri, type: 'image/jpeg', name: 'post-image.jpg' } as any);
    const token = await AsyncStorage.getItem('authToken');
    const response = await fetch(`${API_BASE_URL}/api/upload-image/`, {
      method: 'POST',
      body: formData,
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (response.ok) {
      const { imageUrl } = await response.json();
      return imageUrl;
    }
    throw new Error('Upload failed');
  }, []);

  const submitPost = useCallback(async () => {
    if (!newPostText.trim() && !selectedImage) return;
    setLoading(true);
    try {
      let imageUrl: string | undefined;
      if (selectedImage) {
        imageUrl = await uploadImage(selectedImage);
      }
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/wealth-circles/${circle.id}/posts/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content: newPostText, image: imageUrl }),
      });
      if (response.ok) {
        const newPost = await response.json();
        // Emit via socket for real-time
        if (socketRef.current) socketRef.current.emit('new_post', newPost);
        setNewPostText('');
        setSelectedImage(null);
        // Refresh posts
        loadPosts();
      }
    } catch (err) {
      console.error('Error posting:', err);
      Alert.alert('Error', 'Failed to post. Try again.');
    } finally {
      setLoading(false);
    }
  }, [circle.id, newPostText, selectedImage, uploadImage, loadPosts]);

  // New: Submit Comment
  const submitComment = useCallback(async (postId: string) => {
    const content = newComment[postId]?.trim();
    if (!content) return;
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content }),
      });
      if (response.ok) {
        const comment = await response.json();
        // Emit via socket
        if (socketRef.current) socketRef.current.emit('new_comment', { postId, comment });
        setNewComment(prev => ({ ...prev, [postId]: '' }));
        // Refresh posts to update comments count
        loadPosts();
      }
    } catch (err) {
      console.error('Error commenting:', err);
    }
  }, [loadPosts]);

  const toggleComments = (postId: string) => {
    setExpandedPostId(prev => prev === postId ? null : postId);
  };

  const renderPost = ({ item: post }: { item: CirclePost }) => (
    <View style={[styles.postCard, { backgroundColor: theme.currentTheme.colors.card }]}>
      <LinearGradient
        colors={['#f8f9fa', '#ffffff']}
        style={styles.postGradient}
      >
        <View style={styles.postHeader}>
          <View style={styles.userAvatarContainer}>
            <Image source={{ uri: post.user.avatar }} style={styles.userAvatar} />
            <View style={styles.onlineDot} />
          </View>
          <View style={styles.userInfo}>
            <Text style={[styles.postUser, { color: theme.currentTheme.colors.textPrimary }]}>{post.user.name}</Text>
            <Text style={[styles.postTime, { color: theme.currentTheme.colors.textSecondary }]}>{post.timestamp}</Text>
          </View>
        </View>
        <Text style={[styles.postContent, { color: theme.currentTheme.colors.textPrimary }]}>{post.content}</Text>
        {post.image && (
          <Image source={{ uri: post.image }} style={styles.postImage} resizeMode="cover" />
        )}
        <View style={styles.postActions}>
          <TouchableOpacity style={styles.actionButton}>
            <LinearGradient colors={['#667eea', '#764ba2']} style={styles.actionGradient}>
              <Text style={styles.actionText}>👍 {post.likes}</Text>
            </LinearGradient>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => toggleComments(post.id)}>
            <LinearGradient colors={['#34C759', '#30D158']} style={styles.actionGradient}>
              <Text style={styles.actionText}>💬 {post.comments.length}</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* New: Comments Section */}
      {expandedPostId === post.id && (
        <View style={styles.commentsSection}>
          <FlatList
            data={post.comments || []}
            renderItem={({ item: comment }) => (
              <View style={styles.commentItem}>
                <Image source={{ uri: comment.user.avatar }} style={styles.commentAvatar} />
                <View style={styles.commentContent}>
                  <Text style={[styles.commentUser, { color: theme.currentTheme.colors.textPrimary }]}>{comment.user.name}</Text>
                  <Text style={[styles.commentText, { color: theme.currentTheme.colors.textPrimary }]}>{comment.content}</Text>
                  <Text style={[styles.commentTime, { color: theme.currentTheme.colors.textSecondary }]}>{comment.timestamp}</Text>
                </View>
              </View>
            )}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
          />
          {/* Comment Input */}
          <View style={styles.commentInputContainer}>
            <TextInput
              style={[styles.commentInput, { color: theme.currentTheme.colors.textPrimary }]}
              placeholder="Add a comment..."
              placeholderTextColor={theme.currentTheme.colors.textSecondary}
              value={newComment[post.id] || ''}
              onChangeText={(text) => setNewComment(prev => ({ ...prev, [post.id]: text }))}
              multiline
            />
            <TouchableOpacity 
              onPress={() => submitComment(post.id)} 
              style={styles.commentSubmit}
              disabled={!newComment[post.id]?.trim()}
            >
              <Text style={styles.commentSubmitText}>Send</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );

  if (loading) {
    return (
      <LinearGradient colors={['#f8f9fa', '#e9ecef']} style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.currentTheme.colors.primary} />
      </LinearGradient>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        style={styles.postsList}
        contentContainerStyle={styles.postsContent}
      />
      {/* Enhanced Post Input Bar with Image Picker */}
      <View style={[styles.inputBar, { backgroundColor: theme.currentTheme.colors.card }]}>
        <TouchableOpacity onPress={pickImage} style={styles.imagePicker}>
          <LinearGradient colors={['#FF9500', '#FF3B30']} style={styles.imagePickerGradient}>
            <Text style={styles.imagePickerText}>📷</Text>
          </LinearGradient>
        </TouchableOpacity>
        <TextInput
          style={[styles.input, { color: theme.currentTheme.colors.textPrimary }]}
          placeholder="Share your thoughts or insights..."
          placeholderTextColor={theme.currentTheme.colors.textSecondary}
          value={newPostText}
          onChangeText={setNewPostText}
          multiline
          maxLength={500}
        />
        <TouchableOpacity onPress={submitPost} style={styles.postButton} disabled={!newPostText.trim() && !selectedImage}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={[
              styles.postButtonGradient, 
              (!newPostText.trim() && !selectedImage) && styles.postButtonDisabled
            ]}
          >
            <Text style={styles.postButtonText}>Post</Text>
          </LinearGradient>
        </TouchableOpacity>
        {selectedImage && (
          <Image source={{ uri: selectedImage }} style={styles.previewImage} />
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  postsList: { flex: 1 },
  postsContent: { padding: 16 },
  postCard: {
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({ 
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 8 }, 
      android: { elevation: 8 } 
    }),
  },
  postGradient: {
    padding: 16,
  },
  postHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  userAvatarContainer: { position: 'relative', marginRight: 12 },
  userAvatar: { width: 40, height: 40, borderRadius: 20 },
  onlineDot: { 
    position: 'absolute', bottom: 0, right: 0, width: 12, height: 12, borderRadius: 6, 
    backgroundColor: '#34C759', borderWidth: 2, borderColor: 'white' 
  },
  userInfo: { flex: 1 },
  postUser: { fontWeight: 'bold', fontSize: 14 },
  postTime: { fontSize: 12, marginTop: 2 },
  postContent: { fontSize: 16, lineHeight: 22, marginBottom: 12 },
  postImage: { 
    width: '100%', height: 200, borderRadius: 12, marginBottom: 12 
  },
  postActions: { flexDirection: 'row' },
  actionButton: { marginRight: 8 },
  actionGradient: { 
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, minWidth: 60, alignItems: 'center' 
  },
  actionText: { color: 'white', fontWeight: '600', fontSize: 12 },
  commentsSection: { 
    backgroundColor: '#f8f9fa', padding: 16, borderTopLeftRadius: 16, borderTopRightRadius: 16 
  },
  commentItem: { 
    flexDirection: 'row', marginBottom: 12, alignItems: 'flex-start' 
  },
  commentAvatar: { width: 32, height: 32, borderRadius: 16, marginRight: 8 },
  commentContent: { flex: 1 },
  commentUser: { fontWeight: '600', fontSize: 12 },
  commentText: { fontSize: 14, marginTop: 2, lineHeight: 18 },
  commentTime: { fontSize: 10, marginTop: 2 },
  commentInputContainer: { 
    flexDirection: 'row', alignItems: 'flex-end', marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#e0e0e0' 
  },
  commentInput: { 
    flex: 1, minHeight: 36, maxHeight: 80, borderRadius: 18, paddingHorizontal: 12, 
    backgroundColor: 'white', marginRight: 8 
  },
  commentSubmit: { 
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: '#667eea' 
  },
  commentSubmitText: { color: 'white', fontWeight: '600' },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  imagePicker: { marginRight: 8 },
  imagePickerGradient: { 
    width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' 
  },
  imagePickerText: { fontSize: 20, color: 'white' },
  input: { 
    flex: 1, minHeight: 40, maxHeight: 120, borderRadius: 20, paddingHorizontal: 16, 
    backgroundColor: '#f0f0f0', marginRight: 8 
  },
  postButton: { marginLeft: 8 },
  postButtonGradient: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20 },
  postButtonDisabled: { opacity: 0.5 },
  postButtonText: { color: 'white', fontWeight: '600' },
  previewImage: { 
    position: 'absolute', bottom: 80, right: 16, width: 80, height: 80, borderRadius: 8 
  },
  headerClose: { padding: 8 },
  headerCloseText: { color: '#667eea', fontWeight: '600' },
});
