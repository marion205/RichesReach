import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Image,
  FlatList,
  RefreshControl,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
} from 'react-native';
import { useMutation, useQuery, useApolloClient } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Queries
const GET_POSTS = gql`
  query GetPosts {
    wallPosts {
      id
      content
      image
      createdAt
      likesCount
      isLikedByUser
      commentsCount
      user {
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
  }
`;

const GET_ME = gql`
  query GetMe {
    me {
      id
      email
      name
      profilePic
    }
  }
`;

const GET_POST_COMMENTS = gql`
  query GetPostComments($postId: ID!) {
    postComments(postId: $postId) {
      id
      content
      createdAt
      user {
        id
        name
      }
    }
  }
`;

// GraphQL Mutations
const CREATE_POST = gql`
  mutation CreatePost($content: String!) {
    createPost(content: $content) {
      post {
        id
        content
        createdAt
        user {
          id
          name
        }
      }
    }
  }
`;

const TOGGLE_LIKE = gql`
  mutation ToggleLike($postId: ID!) {
    toggleLike(postId: $postId) {
      post {
        id
        likesCount
        isLikedByUser
      }
    }
  }
`;

const CREATE_COMMENT = gql`
  mutation CreateComment($postId: ID!, $content: String!) {
    createComment(postId: $postId, content: $content) {
      comment {
        id
        content
        createdAt
        user {
          id
          name
        }
      }
    }
  }
`;

const DELETE_COMMENT = gql`
  mutation DeleteComment($commentId: ID!) {
    deleteComment(commentId: $commentId) {
      success
    }
  }
`;

const TOGGLE_FOLLOW = gql`
  mutation ToggleFollow($userId: ID!) {
    toggleFollow(userId: $userId) {
      user {
        id
        isFollowingUser
        followersCount
      }
      following
    }
  }
`;

// Types
interface User {
  id: string;
  name: string;
  email: string;
  profilePic?: string;
  followersCount: number;
  followingCount: number;
  isFollowingUser: boolean;
  isFollowedByUser: boolean;
}

interface Post {
  id: string;
  content: string;
  image?: string;
  createdAt: string;
  likesCount: number;
  isLikedByUser: boolean;
  commentsCount: number;
  user: User;
}

interface Comment {
  id: string;
  content: string;
  createdAt: string;
  user: {
    id: string;
    name: string;
  };
}

interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function HomeScreen({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) {
  const client = useApolloClient();
  
  // State
  const [posts, setPosts] = useState<Post[]>([]);
  const [newPost, setNewPost] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [showPostForm, setShowPostForm] = useState(false);
  const [showComments, setShowComments] = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Chatbot state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // Queries
  const { data: postsData, loading: postsLoading, refetch: refetchPosts } = useQuery(GET_POSTS);
  const { data: meData, loading: meLoading } = useQuery(GET_ME);

  // Mutations
  const [createPost] = useMutation(CREATE_POST, {
    refetchQueries: [{ query: GET_POSTS }],
    awaitRefetchQueries: true,
  });

  const [toggleLike] = useMutation(TOGGLE_LIKE);
  const [createComment] = useMutation(CREATE_COMMENT, {
    refetchQueries: [{ query: GET_POST_COMMENTS, variables: { postId: showComments } }],
    awaitRefetchQueries: true,
  });
  const [deleteComment] = useMutation(DELETE_COMMENT);
  const [toggleFollow] = useMutation(TOGGLE_FOLLOW);

  // Effects
  useEffect(() => {
    if (postsData?.wallPosts) {
      setPosts(postsData.wallPosts);
    }
  }, [postsData]);

  useEffect(() => {
    console.log('🚀 HomeScreen loaded - console logging is working!');
  }, []);

  // Handlers
  const handleCreatePost = async () => {
    if (!newPost.trim() && !imageUri) {
      Alert.alert('Error', 'Please enter some content or add an image.');
      return;
    }

    setIsSubmitting(true);
    try {
      await createPost({
        variables: {
          content: newPost.trim(),
        },
      });
      
      resetComposer();
      Alert.alert('Success! 🎉', 'Your post has been created!');
    } catch (error) {
      console.error('Failed to create post:', error);
      Alert.alert('Error', 'Failed to create post. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleLike = async (postId: string) => {
    try {
      await toggleLike({ variables: { postId } });
    } catch (error) {
      console.error('Failed to toggle like:', error);
    }
  };

  const handleShowComments = async (postId: string) => {
    if (showComments === postId) {
      setShowComments(null);
      setComments([]);
      return;
    }

    setShowComments(postId);
    try {
      const { data } = await client.query({
        query: GET_POST_COMMENTS,
        variables: { postId },
      });
      setComments(data.postComments || []);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
      setComments([]);
    }
  };

  const handleCreateComment = async () => {
    if (!newComment.trim() || !showComments) return;

    try {
      await createComment({
        variables: {
          postId: showComments,
          content: newComment.trim(),
        },
      });
      
      setNewComment('');
      Alert.alert('Success! 💬', 'Your comment has been added!');
    } catch (error) {
      console.error('Failed to create comment:', error);
      Alert.alert('Error', 'Failed to create comment. Please try again.');
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    Alert.alert('Confirm Delete', 'Are you sure you want to delete this comment?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteComment({ variables: { commentId } });
            setShowComments(null); // Close comments section
            await refetchPosts();
            Alert.alert('Comment Deleted', 'Your comment has been deleted.');
          } catch (error) {
            console.error('Failed to delete comment:', error);
            Alert.alert('Error', 'Failed to delete comment. Please try again.');
          }
        },
      },
    ]);
  };

  const createTestPost = async () => {
    try {
      await createPost({
        variables: { content: "Hello! This is my first post from the new account! 🚀" },
      });
      await refetchPosts();
      Alert.alert('Test Post Created', 'Your test post has been created! You should now see it in the feed.');
    } catch (error) {
      console.error('Failed to create test post:', error);
      Alert.alert('Error', 'Failed to create test post. Please try again.');
    }
  };

  const resetComposer = () => {
    setNewPost('');
    setImageUri(null);
    setShowPostForm(false);
  };

  const pickImage = async () => {
    const { granted } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!granted) {
      Alert.alert('Permission needed', 'Please allow photo library access to add an image.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 1,
      selectionLimit: 1,
    });
    if (!result.canceled && result.assets.length > 0) {
      setImageUri(result.assets[0].uri);
    }
  };

  const canPost = newPost.trim().length > 0 || !!imageUri;

  // -------- Chatbot --------
  const quickPrompts = [
    'What is an ETF?',
    'Roth vs Traditional IRA',
    'Explain 50/30/20 budgeting',
    'How do index funds work?',
    'What is an expense ratio?',
    'Index fund vs ETF',
    'Diversification basics',
    'Dollar-cost averaging',
  ];

  const openChat = () => {
    setChatOpen(true);
    if (chatMessages.length === 0) {
      setChatMessages([
        {
          id: String(Date.now()),
          role: 'assistant',
          content:
            'Educational only — not financial advice.\nWhat do you need help with? Ask about ETFs, IRAs, fees, or budgeting.',
        },
      ]);
    }
    setTimeout(() => listRef.current?.scrollToEnd?.({ animated: false }), 0);
  };

  const closeChat = () => {
    setChatOpen(false);
    setChatInput('');
    setChatSending(false);
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatInput('');
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || chatSending) return;

    const userMessage: ChatMsg = {
      id: String(Date.now()),
      role: 'user',
      content: chatInput.trim(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatSending(true);

    try {
      // Simulate AI response
      setTimeout(() => {
        const aiResponse: ChatMsg = {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `I understand you're asking about "${userMessage.content}". This is a great question about personal finance! While I can provide general educational information, remember that this is not financial advice. For personalized guidance, consider consulting with a qualified financial advisor.`,
        };
        setChatMessages(prev => [...prev, aiResponse]);
        setChatSending(false);
        setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 100);
      }, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
      setChatSending(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetchPosts();
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleToggleFollow = async (userId: string) => {
    try {
      await toggleFollow({ variables: { userId } });
      // Clear cache and refetch to ensure fresh data
      await client.resetStore();
      await refetchPosts();
      // Also refetch user data to get updated follow status
      if (meData?.me?.id) {
        await client.query({
          query: GET_ME,
          fetchPolicy: 'network-only'
        });
      }
    } catch (error) {
      console.error('Failed to toggle follow:', error);
    }
  };

  // Render
  if (postsLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading posts... 📱</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerBar}>
        <TouchableOpacity 
          style={styles.profileButton}
          onPress={() => {
            if (!meLoading && meData?.me?.id) {
              // @ts-ignore
              navigateTo('Profile', { userId: meData.me.id });
            }
          }}
        >
          <View style={styles.profileAvatar}>
            {!meLoading && meData?.me?.profilePic ? (
              <Image 
                source={{ uri: meData.me.profilePic }} 
                style={styles.profilePic} 
              />
            ) : (
              <Text style={styles.profileAvatarText}>
                {!meLoading && meData?.me?.name ? meData.me.name.charAt(0).toUpperCase() : 'U'}
              </Text>
            )}
          </View>
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Image source={require('../assets/whitelogo1.png')} style={styles.logo} />
        </View>

        <View style={styles.headerRight}>
          <TouchableOpacity 
            style={styles.discoverButton}
            onPress={() => navigateTo('DiscoverUsers')}
          >
            <Icon name="users" size={20} color="#00cc99" />
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setShowPostForm(true)}>
            <Text style={styles.icon}>➕</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Post Creation Form */}
      {showPostForm && (
        <View style={styles.postForm}>
          <TextInput
            style={styles.postInput}
            placeholder="What's on your mind? ��"
            value={newPost}
            onChangeText={setNewPost}
            multiline
            maxLength={500}
          />
          
          {imageUri && (
            <View style={styles.imagePreviewContainer}>
              <Image source={{ uri: imageUri }} style={styles.imagePreview} />
              <TouchableOpacity
                style={styles.removeImageButton}
                onPress={() => setImageUri(null)}
              >
                <Text style={styles.removeImageText}>✕</Text>
              </TouchableOpacity>
            </View>
          )}
          
          <View style={styles.formActions}>
            <TouchableOpacity style={styles.imageButton} onPress={pickImage}>
              <Icon name="image" size={20} color="#00cc99" />
              <Text style={styles.imageButtonText}>Add Image</Text>
            </TouchableOpacity>
            
            <View style={styles.postButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={resetComposer}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.postButton, !canPost && styles.postButtonDisabled]}
                onPress={handleCreatePost}
                disabled={!canPost || isSubmitting}
              >
                <Text style={styles.postButtonText}>
                  {isSubmitting ? 'Posting...' : 'Post'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Posts Feed */}
      <ScrollView
        style={styles.feed}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {posts.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No posts yet. Be the first to share! ��</Text>
            <TouchableOpacity style={styles.createFirstPostButton} onPress={createTestPost}>
              <Text style={styles.createFirstPostText}>Create Your First Post</Text>
            </TouchableOpacity>
          </View>
        ) : (
          posts.map((post) => (
            <View key={post.id} style={styles.postCard}>
              <View style={styles.postHeader}>
                <TouchableOpacity 
                  style={styles.userInfo}
                  onPress={() => {
                    // @ts-ignore
                    navigateTo('Profile', { userId: post.user.id });
                  }}
                >
                  <View style={styles.avatar}>
                    {post.user.profilePic ? (
                      <Image 
                        source={{ uri: post.user.profilePic }} 
                        style={styles.postAvatarPic} 
                      />
                    ) : (
                      <Text style={styles.avatarText}>{post.user.name.charAt(0).toUpperCase()}</Text>
                    )}
                  </View>
                  <Text style={styles.author}>{post.user.name}</Text>
                                     {!meLoading && meData?.me?.id && meData.me.id === post.user.id && (
                    <View style={styles.youBadge}>
                      <Text style={styles.youBadgeText}>You</Text>
                    </View>
                  )}
                  <Icon name="chevron-right" size={12} color="#00cc99" style={{ marginLeft: 4 }} />
                </TouchableOpacity>
                <Text style={styles.timestamp}>
                  {new Date(post.createdAt).toLocaleDateString()}
                </Text>
              </View>
              <Text style={styles.content}>{post.content}</Text>
              {!!post.image && <Image source={{ uri: post.image }} style={styles.postImage} />}
              
              <View style={styles.postActions}>
                <TouchableOpacity 
                  style={styles.likeButton} 
                  onPress={() => handleToggleLike(post.id)}
                >
                  <Icon 
                    name={post.isLikedByUser ? "heart" : "heart"} 
                    size={20} 
                    color={post.isLikedByUser ? "#ff4757" : "#666"} 
                    style={{ opacity: post.isLikedByUser ? 1 : 0.6 }}
                  />
                  <Text style={[styles.likeCount, post.isLikedByUser && styles.likedText]}>
                    {post.likesCount}
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.commentButton} 
                  onPress={() => handleShowComments(post.id)}
                >
                  <Icon name="message-circle" size={20} color="#666" />
                  <Text style={styles.commentCount}>{post.commentsCount}</Text>
                </TouchableOpacity>
                
                {!meLoading && meData?.me?.id && meData.me.id !== post.user.id && (
                  <TouchableOpacity 
                    style={styles.followButton} 
                    onPress={() => handleToggleFollow(post.user.id)}
                  >
                    <Icon 
                      name={post.user.isFollowingUser ? "user-check" : "user-plus"} 
                      size={20} 
                      color={post.user.isFollowingUser ? "#00cc99" : "#666"} 
                    />
                    <Text style={[styles.followText, post.user.isFollowingUser && styles.followingText]}>
                      {post.user.isFollowingUser ? "Following" : "Follow"}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>
              
              {/* Comments Section */}
              {showComments === post.id && (
                <View style={styles.commentsSection}>
                  {/* Display existing comments */}
                  {comments.length > 0 && (
                    <View style={styles.commentsList}>
                      {comments.map((comment) => (
                        <View key={comment.id} style={styles.commentItem}>
                          <View style={styles.commentHeader}>
                            <Text style={styles.commentAuthor}>{comment.user.name}</Text>
                            <Text style={styles.commentDate}>
                              {new Date(comment.createdAt).toLocaleDateString()}
                            </Text>
                          </View>
                          <View style={styles.commentContentRow}>
                            <Text style={styles.commentContent}>{comment.content}</Text>
                            {/* Delete button for comments - only show for comment author */}
                            {!meLoading && meData?.me?.id === comment.user.id && (
                              <TouchableOpacity 
                                onPress={() => handleDeleteComment(comment.id)}
                                style={styles.deleteCommentButton}
                              >
                                <Icon name="trash-2" size={16} color="#ef4444" />
                              </TouchableOpacity>
                            )}
                          </View>
                        </View>
                      ))}
                    </View>
                  )}
                  
                  {/* Add new comment */}
                  <View style={styles.addCommentSection}>
                    <TextInput
                      style={styles.commentInput}
                      placeholder="Add a comment... 💬"
                      value={newComment}
                      onChangeText={setNewComment}
                      multiline
                      maxLength={200}
                    />
                    <TouchableOpacity
                      style={[styles.commentButton, !newComment.trim() && styles.commentButtonDisabled]}
                      onPress={handleCreateComment}
                      disabled={!newComment.trim()}
                    >
                      <Text style={styles.commentButtonText}>Comment</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          ))
        )}
      </ScrollView>

      {/* Chatbot Floating Button */}
      <TouchableOpacity style={styles.chatButton} onPress={openChat}>
        <Icon name="message-circle" size={24} color="#fff" />
      </TouchableOpacity>

      {/* Chatbot Modal */}
      {chatOpen && (
        <View style={styles.chatModal}>
          <View style={styles.chatHeader}>
            <Text style={styles.chatTitle}>Financial Education Assistant ��</Text>
            <View style={styles.chatHeaderActions}>
              <TouchableOpacity onPress={clearChat} style={styles.chatActionButton}>
                <Icon name="trash-2" size={16} color="#666" />
              </TouchableOpacity>
              <TouchableOpacity onPress={closeChat} style={styles.chatCloseButton}>
                <Icon name="x" size={20} color="#666" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Quick Prompts */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickPromptsContainer}>
            {quickPrompts.map((prompt, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickPromptButton}
                onPress={() => setChatInput(prompt)}
              >
                <Text style={styles.quickPromptText}>{prompt}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Chat Messages */}
          <FlatList
            ref={listRef}
            data={chatMessages}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={[
                styles.chatMessage,
                item.role === 'user' ? styles.userMessage : styles.assistantMessage
              ]}>
                <Text style={[
                  styles.chatMessageText,
                  item.role === 'user' ? styles.userMessageText : styles.assistantMessageText
                ]}>
                  {item.content}
                </Text>
              </View>
            )}
            style={styles.chatMessages}
            showsVerticalScrollIndicator={false}
          />

          {/* Chat Input */}
          <View style={styles.chatInputContainer}>
            <TextInput
              style={styles.chatInput}
              placeholder="Ask about personal finance..."
              value={chatInput}
              onChangeText={setChatInput}
              multiline
              maxLength={500}
            />
            <TouchableOpacity
              style={[styles.chatSendButton, !chatInput.trim() && styles.chatSendButtonDisabled]}
              onPress={sendMessage}
              disabled={!chatInput.trim() || chatSending}
            >
              <Icon 
                name={chatSending ? "loader" : "send"} 
                size={20} 
                color={chatInput.trim() ? "#fff" : "#ccc"} 
              />
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  
  // Header
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    paddingTop: 70,
  },
  profileButton: {
    padding: 4,
    marginRight: 8,
  },
  profileAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#00cc99',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  profilePic: {
    width: '100%',
    height: '100%',
    borderRadius: 20,
  },
  profileAvatarText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  logo: {
    height: 60,
    width: 240,
    resizeMode: 'contain',
  },
  icon: {
    fontSize: 24,
    color: '#00cc99',
  },
  discoverButton: {
    padding: 4,
    marginRight: 8,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },

  // Loading
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    fontSize: 18,
    color: '#666',
  },

  // Post Form
  postForm: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  postInput: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 15,
  },
  imagePreviewContainer: {
    position: 'relative',
    marginBottom: 15,
  },
  imagePreview: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    resizeMode: 'cover',
  },
  removeImageButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeImageText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  formActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  imageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00cc99',
  },
  imageButtonText: {
    marginLeft: 8,
    color: '#00cc99',
    fontWeight: '600',
  },
  postButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  cancelButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#666',
  },
  cancelButtonText: {
    color: '#666',
    fontWeight: '600',
  },
  postButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  postButtonDisabled: {
    backgroundColor: '#ccc',
  },
  postButtonText: {
    color: '#fff',
    fontWeight: '600',
  },

  // Feed
  feed: {
    flex: 1,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  createFirstPostButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  createFirstPostText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Post Card
  postCard: {
    backgroundColor: '#fff',
    marginHorizontal: 15,
    marginVertical: 8,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#00cc99',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  postAvatarPic: {
    width: '100%',
    height: '100%',
    borderRadius: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  author: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  youBadge: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 8,
  },
  youBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
  },
  content: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
    marginBottom: 15,
  },
  postImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 15,
    resizeMode: 'cover',
  },

  // Post Actions
  postActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  likeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  likeCount: {
    fontSize: 14,
    color: '#666',
  },
  likedText: {
    color: '#ff4757',
    fontWeight: '600',
  },
  commentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  commentCount: {
    fontSize: 14,
    color: '#666',
  },
  followButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  followText: {
    fontSize: 14,
    color: '#666',
  },
  followingText: {
    color: '#00cc99',
    fontWeight: '600',
  },

  // Comments Section
  commentsSection: {
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  commentsList: {
    marginBottom: 15,
  },
  commentItem: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  commentAuthor: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  commentDate: {
    fontSize: 12,
    color: '#666',
  },
  commentContentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  commentContent: {
    fontSize: 14,
    color: '#333',
    flex: 1,
    marginRight: 10,
  },
  deleteCommentButton: {
    padding: 4,
  },
  addCommentSection: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  commentInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    minHeight: 40,
    textAlignVertical: 'top',
  },
  commentButtonDisabled: {
    backgroundColor: '#ccc',
  },
  commentButtonText: {
    color: '#fff',
    fontWeight: '600',
  },

  // Chatbot
  chatButton: {
    position: 'absolute',
    bottom: 30,
    right: 30,
    backgroundColor: '#00cc99',
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  chatModal: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    zIndex: 1000,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    backgroundColor: '#fff',
  },
  chatTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  chatHeaderActions: {
    flexDirection: 'row',
    gap: 15,
  },
  chatActionButton: {
    padding: 8,
  },
  chatCloseButton: {
    padding: 8,
  },
  quickPromptsContainer: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  quickPromptButton: {
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  quickPromptText: {
    fontSize: 14,
    color: '#333',
  },
  chatMessages: {
    flex: 1,
    padding: 20,
  },
  chatMessage: {
    marginBottom: 15,
    maxWidth: '80%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#00cc99',
    padding: 12,
    borderRadius: 18,
    borderBottomRightRadius: 4,
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  chatMessageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userMessageText: {
    color: '#fff',
  },
  assistantMessageText: {
    color: '#333',
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#fff',
  },
  chatInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 20,
    padding: 12,
    fontSize: 14,
    minHeight: 40,
    textAlignVertical: 'top',
    marginRight: 10,
  },
  chatSendButton: {
    backgroundColor: '#00cc99',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatSendButtonDisabled: {
    backgroundColor: '#ccc',
  },
};