import React, { useState, useLayoutEffect, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  Modal,
  Image,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  FlatList,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Icon from 'react-native-vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';
import { gql, useMutation, useQuery, useApolloClient } from '@apollo/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// -------- Types --------
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
    email: string;
    followersCount: number;
    followingCount: number;
    isFollowingUser: boolean;
    isFollowedByUser: boolean;
  };
  image?: string;
};

type Comment = {
  id: string;
  content: string;
  createdAt: string;
  user: {
    id: string;
    name: string;
  };
};

type ChatMsg = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: { title: string; url?: string | null; snippet?: string | null }[];
  confidence?: number | null;
};

// -------- GraphQL --------
const CREATE_CHAT_SESSION = gql`
  mutation CreateChatSession {
    createChatSession {
      session {
        id
      }
    }
  }
`;

const SEND_MESSAGE = gql`
  mutation SendMessage($sessionId: ID!, $content: String!) {
    sendMessage(sessionId: $sessionId, content: $content) {
      message {
        id
        role
        content
        createdAt
        confidence
        sources { title url snippet }
      }
    }
  }
`;

const CREATE_POST = gql`
  mutation CreatePost($content: String!) {
    createPost(content: $content) {
      post {
        id
        content
        createdAt
        likesCount
        commentsCount
        isLikedByUser
        user {
          id
          name
          email
          followersCount
          followingCount
          isFollowingUser
          isFollowedByUser
        }
      }
    }
  }
`;

const GET_POSTS = gql`
  query GetPosts {
    wallPosts {
      id
      content
      createdAt
      likesCount
      commentsCount
      isLikedByUser
      user {
        id
        name
        email
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
      name
      email
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
      liked
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

export default function HomeScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();

  // feed
  const [showDropdown, setShowDropdown] = useState(false);
  const [showPostForm, setShowPostForm] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  
  // comments
  const [showComments, setShowComments] = useState<string | null>(null);
  const [commentInput, setCommentInput] = useState('');
  const [comments, setComments] = useState<Comment[]>([]);

  // chatbot
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // chat session id persisted on device
  const [sessionId, setSessionId] = useState<string>('');

  const [createChatSession] = useMutation(CREATE_CHAT_SESSION);
  const [mutateSendMessage] = useMutation(SEND_MESSAGE);
  const [createPost] = useMutation(CREATE_POST);
  const [toggleLike] = useMutation(TOGGLE_LIKE);
  const [createComment] = useMutation(CREATE_COMMENT);
  const [toggleFollow] = useMutation(TOGGLE_FOLLOW);
  const { data: postsData, loading: postsLoading, refetch: refetchPosts } = useQuery(GET_POSTS);
  const { data: meData, loading: meLoading } = useQuery(GET_ME);
  
  // Debug logging for meData
  useEffect(() => {
    console.log('meData:', meData);
    console.log('meData?.me?.id:', meData?.me?.id);
  }, [meData]);
  
  // Test log to verify console is working
  useEffect(() => {
    console.log('🚀 HomeScreen loaded - console logging is working!');
  }, []);
  const client = useApolloClient();

  // Function to create a new chat session
  const createNewSession = async (): Promise<string | null> => {
    try {
      console.log('Creating new chat session...');
      const { data } = await createChatSession();
      const sid = data?.createChatSession?.session?.id;
      if (sid && !isNaN(Number(sid))) {
        console.log('Created session with ID:', sid);
        await AsyncStorage.setItem('chat_session_id', sid);
        setSessionId(sid);
        return sid;
      }
      return null;
    } catch (error) {
      console.error('Failed to create chat session:', error);
      return null;
    }
  };

  // Load posts from backend
  useEffect(() => {
    if (postsData?.wallPosts) {
      setPosts(postsData.wallPosts);
    }
  }, [postsData]);

  useEffect(() => {
    (async () => {
      const key = 'chat_session_id';
      let sid = await AsyncStorage.getItem(key);
      
      // Check if we have a valid numeric session ID
      if (sid && !isNaN(Number(sid))) {
        console.log('Using existing session ID:', sid);
        setSessionId(sid);
        return;
      }
      
      // Clear invalid session ID
      if (sid) {
        console.log('Clearing invalid session ID:', sid);
        await AsyncStorage.removeItem(key);
      }
      
      // If no valid session exists, create a new one
      try {
        console.log('Creating new chat session...');
        const { data } = await createChatSession();
        sid = data?.createChatSession?.session?.id;
        if (sid && !isNaN(Number(sid))) {
          console.log('Created session with ID:', sid);
          await AsyncStorage.setItem(key, sid);
          setSessionId(sid);
        } else {
          console.error('Invalid session ID received:', sid);
          setSessionId('');
        }
      } catch (error) {
        console.error('Failed to create chat session:', error);
        setSessionId('');
      }
    })();
  }, [createChatSession]);

  useLayoutEffect(() => {
    // @ts-ignore
    navigation.setOptions({ headerShown: false });
  }, [navigation]);

  // -------- Auth --------
  const handleLogout = async () => {
    await AsyncStorage.removeItem('token');
    Alert.alert('Logged out');
    // @ts-ignore
    navigation.replace('Login');
  };

  // -------- Posts --------
    const handleSubmitPost = async () => {
    const content = newPost.trim();
    if (!content && !imageUri) return;

    try {
      console.log('Creating post with content:', content);
      const { data } = await createPost({
        variables: { content },
      });
      
      console.log('Post creation response:', data);
      
      if (data?.createPost?.post) {
        console.log('Post created successfully!');
        // Clear the form
        resetComposer();
        
        // Force a refetch to ensure the post appears
        setTimeout(async () => {
          try {
            console.log('Forcing refetch to ensure post appears...');
            await refetchPosts({ fetchPolicy: 'network-only' });
            console.log('Refetch completed');
          } catch (error) {
            console.error('Refetch failed:', error);
          }
        }, 100);
      } else {
        console.warn('No post data returned from creation');
        resetComposer();
      }
    } catch (error) {
      console.error('Failed to create post:', error);
      Alert.alert('Error', 'Failed to create post. Please try again.');
    }
  };

  const handleToggleLike = async (postId: string) => {
    try {
      await toggleLike({
        variables: { postId },
      });
      // Refresh posts to get updated like counts
      await refetchPosts();
    } catch (error) {
      console.error('Failed to toggle like:', error);
      Alert.alert('Error', 'Failed to like/unlike post. Please try again.');
    }
  };

  const handleToggleFollow = async (userId: string) => {
    try {
      await toggleFollow({
        variables: { userId },
      });
      // Refresh posts to get updated follow counts
      await refetchPosts();
    } catch (error) {
      console.error('Failed to toggle follow:', error);
      Alert.alert('Error', 'Failed to follow/unfollow user. Please try again.');
    }
  };

  const handleCreateComment = async (postId: string) => {
    const content = commentInput.trim();
    if (!content) return;

    try {
      await createComment({
        variables: { postId, content },
      });
      setCommentInput('');
      
      // Refresh posts to get updated comment counts
      await refetchPosts();
      
      // Refresh comments for this post
      const { data } = await client.query({
        query: GET_POST_COMMENTS,
        variables: { postId },
      });
      
      if (data?.postComments) {
        setComments(data.postComments);
      }
    } catch (error) {
      console.error('Failed to create comment:', error);
      Alert.alert('Error', 'Failed to create comment. Please try again.');
    }
  };

  const handleShowComments = async (postId: string) => {
    if (showComments === postId) {
      setShowComments(null);
      return;
    }
    
    setShowComments(postId);
    
    // Fetch comments for this post
    try {
      const { data } = await client.query({
        query: GET_POST_COMMENTS,
        variables: { postId },
      });
      
      if (data?.postComments) {
        setComments(data.postComments);
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error);
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

  // mutation-backed sender
  async function sendToBackend(question: string): Promise<ChatMsg | null> {
    try {
      // Check if we have a valid session ID
      let currentSessionId = sessionId;
      if (!currentSessionId || isNaN(Number(currentSessionId))) {
        console.log('Invalid session ID, creating new session...');
        currentSessionId = await createNewSession();
        if (!currentSessionId) {
          console.error('Failed to create new session');
          return null;
        }
      }
      
      console.log('Sending message to backend with sessionId:', currentSessionId);
      const { data } = await mutateSendMessage({
        variables: { sessionId: currentSessionId, content: question },
      });
      const resp = data?.sendMessage?.message;
      if (!resp) {
        console.warn('No response from sendMessage mutation');
        return null;
      }
      return {
        id: resp.id ?? `${Date.now()}-a`,
        role: resp.role ?? 'assistant',
        content: resp.content ?? '',
        sources: resp.sources ?? [],
        confidence: resp.confidence ?? null,
      };
    } catch (e: any) {
      console.error('sendMessage error:', {
        message: e?.message,
        networkError: e?.networkError?.result,
        graphQLErrors: e?.graphQLErrors,
        fullError: e
      });
      return null;
    }
  }

  const handleChatSend = async (seed?: string) => {
    const q = (seed ?? chatInput).trim();
    if (!q || chatSending || !sessionId) return;

    // Check if user is logged in
    const token = await AsyncStorage.getItem('token');
    if (!token) {
      Alert.alert('Login Required', 'Please log in to use the chatbot.');
      return;
    }

    setChatSending(true);
    const u: ChatMsg = { id: `${Date.now()}-u`, role: 'user', content: q };
    setChatMessages((prev) => [...prev, u]);
    setChatInput('');
    setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 0);

    try {
      const reply = await sendToBackend(q);
      if (reply) {
        setChatMessages((prev) => [...prev, reply]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          { id: `${Date.now()}-e`, role: 'assistant', content: "Sorry — I couldn't process that just now." },
        ]);
      }
      setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 0);
    } finally {
      setChatSending(false);
    }
  };

  // -------- UI --------
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerBar}>
        <TouchableOpacity 
          style={styles.profileButton}
                     onPress={() => {
             if (!meLoading && meData?.me?.id) {
               // @ts-ignore
               navigation.navigate('Profile', { userId: meData.me.id });
             }
           }}
        >
          <View style={styles.profileAvatar}>
                         <Text style={styles.profileAvatarText}>
               {!meLoading && meData?.me?.name ? meData.me.name.charAt(0).toUpperCase() : 'U'}
             </Text>
          </View>
        </TouchableOpacity>

        <Image source={require('../assets/whitelogo1.png')} style={styles.logo} />

        <TouchableOpacity onPress={() => setShowPostForm(true)}>
          <Text style={styles.icon}>➕</Text>
        </TouchableOpacity>
      </View>

      {/* Feed */}
      <ScrollView 
        contentContainerStyle={styles.feed}
        refreshControl={
          <RefreshControl
            refreshing={postsLoading}
            onRefresh={refetchPosts}
            colors={['#00cc99']}
            tintColor="#00cc99"
          />
        }
      >
        {postsLoading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading posts...</Text>
          </View>
        ) : posts.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No posts yet. Be the first to share! 🚀</Text>
          </View>
        ) : (
          posts.map((post) => (
            <View key={post.id} style={styles.postCard}>
              <View style={styles.postHeader}>
                <TouchableOpacity 
                  style={styles.userInfo}
                  onPress={() => {
                    // @ts-ignore
                    navigation.navigate('Profile', { userId: post.user.id });
                  }}
                >
                  <View style={styles.avatar}>
                    <Text style={styles.avatarText}>{post.user.name.charAt(0).toUpperCase()}</Text>
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
                          <Text style={styles.commentContent}>{comment.content}</Text>
                        </View>
                      ))}
                    </View>
                  )}
                  
                  {/* Comment input */}
                  <View style={styles.commentInputContainer}>
                    <TextInput
                      style={styles.commentInput}
                      placeholder="Write a comment..."
                      value={commentInput}
                      onChangeText={setCommentInput}
                      multiline
                    />
                    <TouchableOpacity 
                      style={styles.commentSubmitButton}
                      onPress={() => handleCreateComment(post.id)}
                    >
                      <Text style={styles.commentSubmitText}>Post</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          ))
        )}
      </ScrollView>

      {/* Post Composer Modal */}
      <Modal visible={showPostForm} animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={resetComposer}>
              <Icon name="x" size={26} color="#333" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Create Post</Text>
          </View>

          <View style={styles.inputWrapper}>
            <TouchableOpacity onPress={pickImage} style={styles.imageButton}>
              <Icon name="image" size={22} color="#555" />
            </TouchableOpacity>
            <TextInput
              style={styles.modalInput}
              placeholder="Write your thoughts..."
              value={newPost}
              onChangeText={setNewPost}
              multiline
            />
          </View>

          {!!imageUri && <Image source={{ uri: imageUri }} style={styles.previewImage} />}

          <TouchableOpacity
            style={[styles.modalPostButton, !canPost && { opacity: 0.5 }]}
            onPress={handleSubmitPost}
            disabled={!canPost}
          >
            <Text style={styles.postButtonText}>Post</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={resetComposer} style={styles.cancelButton}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </Modal>

      {/* Floating Chatbot Button */}
      <TouchableOpacity style={styles.fab} onPress={openChat} activeOpacity={0.85}>
        <Icon name="message-circle" size={24} color="#fff" />
      </TouchableOpacity>

      {/* Chatbot Sheet */}
      <Modal visible={chatOpen} animationType="fade" transparent>
        <KeyboardAvoidingView
          style={styles.chatOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 64 : 0}
        >
          <Pressable style={styles.backdrop} onPress={closeChat} />

          <View style={[styles.chatSheet, { paddingBottom: insets.bottom + 6 }]}>
            <View style={styles.grabber} />
            
            {/* Header with Clear button */}
            <View style={styles.chatHeaderRow}>
              <View>
                <Text style={styles.chatTitle}>Ask RichesReach</Text>
                <Text style={styles.disclaimer}>
                  Educational only — not financial, tax, or legal advice.
                </Text>
              </View>
              <TouchableOpacity onPress={clearChat} style={styles.clearBtn}>
                <Icon name="trash-2" size={18} color="#fff" />
              </TouchableOpacity>
            </View>

            {/* Messages (scrollable) */}
            <View style={styles.messagesContainer}>
              <FlatList
                ref={listRef}
                data={chatMessages}
                keyExtractor={(m) => m.id}
                renderItem={({ item: m }) => (
                  <View
                    style={[
                      styles.chatBubble,
                      m.role === 'user' ? styles.chatBubbleUser : styles.chatBubbleAssistant,
                    ]}
                  >
                    <Text style={styles.chatBubbleText}>{m.content}</Text>
                    {m.role === 'assistant' && m.sources?.length ? (
                      <View style={{ marginTop: 6 }}>
                        {m.sources.slice(0, 4).map((s, i) => (
                          <Text key={i} style={{ fontSize: 12, textDecorationLine: 'underline' }}>
                            {s.title}
                          </Text>
                        ))}
                      </View>
                    ) : null}
                  </View>
                )}
                contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8 }}
                keyboardShouldPersistTaps="handled"
                showsVerticalScrollIndicator
                onContentSizeChange={() => listRef.current?.scrollToEnd?.({ animated: true })}
              />
            </View>

            {/* Quick prompts grid (small chips, wraps) */}
            <View style={styles.promptGrid}>
              {quickPrompts.map((p) => (
                <TouchableOpacity key={p} style={styles.promptChip} onPress={() => handleChatSend(p)}>
                  <Text style={styles.promptChipText} numberOfLines={1}>
                    {p}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Input row pinned to safe area */}
            <View style={[styles.chatInputRow, { paddingBottom: insets.bottom + 4 }]}>
              <TextInput
                style={styles.chatInput}
                placeholder="What do you need help with?"
                value={chatInput}
                onChangeText={setChatInput}
                multiline
              />
              <TouchableOpacity
                onPress={() => handleChatSend()}
                style={[styles.chatSendBtn, (!chatInput.trim() || chatSending) && { opacity: 0.5 }]}
                disabled={!chatInput.trim() || chatSending}
                accessibilityLabel="Send message"
              >
                {chatSending ? <Icon name="loader" size={18} color="#fff" /> : <Icon name="send" size={18} color="#fff" />}
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

// ---------------- Styles ----------------
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },

  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },

  icon: { fontSize: 24 },
  profileButton: { padding: 4 },
  profileAvatar: { 
    width: 36, 
    height: 36, 
    borderRadius: 18, 
    backgroundColor: '#00cc99', 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  profileAvatarText: { 
    fontSize: 16, 
    fontWeight: 'bold', 
    color: '#fff' 
  },
  youBadge: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 6,
  },
  youBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  logo: { width: 90, height: 90, resizeMode: 'contain' },

  dropdown: {
    position: 'absolute',
    top: 60,
    right: 15,
    backgroundColor: '#f9f9f9',
    padding: 10,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 5,
    zIndex: 20,
  },
  dropdownItem: { fontSize: 16, paddingVertical: 8, paddingHorizontal: 12 },

  feed: { padding: 20, paddingBottom: 140 },
  postCard: { 
    backgroundColor: '#fff', 
    padding: 20, 
    borderRadius: 12, 
    marginBottom: 15, 
    marginHorizontal: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  postHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  userInfo: { flexDirection: 'row', alignItems: 'center', padding: 4, borderRadius: 8 },
  avatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#00cc99', alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  avatarText: { fontSize: 14, fontWeight: 'bold', color: '#fff' },
  author: { fontWeight: 'bold', fontSize: 16, color: '#00cc99', textDecorationLine: 'underline' },
  timestamp: { color: '#666', fontSize: 12 },
  content: { fontSize: 16, marginBottom: 5 },
  postImage: { width: '100%', height: 200, borderRadius: 8, marginTop: 5 },
  loadingContainer: { alignItems: 'center', padding: 40 },
  loadingText: { fontSize: 16, color: '#666' },
  emptyContainer: { alignItems: 'center', padding: 40 },
  emptyText: { fontSize: 16, color: '#666', textAlign: 'center' },
  postActions: { 
    flexDirection: 'row', 
    marginTop: 15, 
    paddingTop: 15, 
    borderTopWidth: 1, 
    borderTopColor: '#f1f3f4',
    justifyContent: 'space-around',
  },
  likeButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
  },
  likeCount: { marginLeft: 5, fontSize: 14, color: '#666', fontWeight: '500' },
  likedText: { color: '#ff4757', fontWeight: 'bold' },
  commentButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
  },
  commentCount: { marginLeft: 5, fontSize: 14, color: '#666', fontWeight: '500' },
  followButton: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
  },
  followText: { marginLeft: 5, fontSize: 14, color: '#666', fontWeight: '500' },
  followingText: { color: '#00cc99', fontWeight: 'bold' },
  commentsSection: { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#eee' },
  commentsList: { marginBottom: 15 },
  commentItem: { 
    backgroundColor: '#f8f9fa', 
    padding: 12, 
    borderRadius: 8, 
    marginBottom: 8 
  },
  commentHeader: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 4 
  },
  commentAuthor: { 
    fontWeight: 'bold', 
    fontSize: 14, 
    color: '#333' 
  },
  commentDate: { 
    fontSize: 12, 
    color: '#666' 
  },
  commentContent: { 
    fontSize: 14, 
    color: '#333', 
    lineHeight: 20 
  },
  commentInputContainer: { flexDirection: 'row', alignItems: 'flex-end' },
  commentInput: { flex: 1, borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 8, marginRight: 10, minHeight: 40 },
  commentSubmitButton: { backgroundColor: '#00cc99', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 6 },
  commentSubmitText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },

  // Post composer styles
  modalContainer: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 10,
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold' },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    backgroundColor: '#f9f9f9',
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  modalInput: {
    flex: 1,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  imageButton: { paddingTop: 10, paddingRight: 10 },
  previewImage: {
    width: '100%',
    height: 200,
    marginTop: 15,
    borderRadius: 10,
  },
  modalPostButton: {
    backgroundColor: '#00cc99',
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
    alignItems: 'center',
  },
  postButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  cancelButton: { marginTop: 10, alignItems: 'center' },
  cancelText: { color: 'gray', fontSize: 16 },

  // FAB
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 30,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#00cc99',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },

  // chatbot sheet
  chatOverlay: { flex: 1, justifyContent: 'flex-end' },
  backdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.35)' },
  chatSheet: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingTop: 8,
    height: '75%',
  },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: '#ddd', marginBottom: 8 },
  chatHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  messagesContainer: {
    flex: 1,
    minHeight: 120,
  },
  chatTitle: { fontSize: 18, fontWeight: '600' },
  disclaimer: { color: '#666', marginTop: 4, fontSize: 12 },

  chatBubble: { padding: 10, borderRadius: 10, marginBottom: 8, maxWidth: '95%' },
  chatBubbleUser: { alignSelf: 'flex-end', backgroundColor: '#eafaf6' },
  chatBubbleAssistant: { alignSelf: 'flex-start', backgroundColor: '#f3f4f6' },
  chatBubbleText: { fontSize: 14 },

  // compact prompt chips (grid)
  promptGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 4,
  },
  promptChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#eef3f9',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    marginBottom: 8,
  },
  promptChipText: { fontSize: 12, color: '#0f172a' },

  // input row pinned to safe area
  chatInputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    backgroundColor: '#fff',
  },
  chatInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#fafafa',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    maxHeight: 120,
  },
  chatSendBtn: {
    backgroundColor: '#00cc99',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clearBtn: { backgroundColor: '#ef4444', padding: 8, borderRadius: 8, marginLeft: 10 },
});