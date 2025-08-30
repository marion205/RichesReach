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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Icon from 'react-native-vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';
import { gql, useMutation } from '@apollo/client';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// -------- Types --------
type Post = {
  id: number;
  author: string;
  content: string;
  image?: string;
};

type ChatMsg = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: { title: string; url?: string | null; snippet?: string | null }[];
  confidence?: number | null;
};

// -------- GraphQL --------
const SEND_MESSAGE = gql`
  mutation SendMessage($sessionId: ID!, $content: String!) {
    sendMessage(sessionId: $sessionId, content: $content) {
      id
      role
      content
      createdAt
      confidence
      sources { title url snippet }
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
  const [posts, setPosts] = useState<Post[]>([
    { id: 1, author: 'Alice', content: 'Just joined RichesReach! 🚀' },
    { id: 2, author: 'Bob', content: 'Excited about financial freedom! 💰' },
    { id: 3, author: 'Clara', content: 'Investing in crypto and stocks 📈' },
  ]);

  // chatbot
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // chat session id persisted on device
  const [sessionId, setSessionId] = useState<string>('');

  useEffect(() => {
    (async () => {
      const key = 'chat_session_id';
      let sid = await AsyncStorage.getItem(key);
      if (!sid) {
        sid = `session-${Date.now()}`;
        await AsyncStorage.setItem(key, sid);
      }
      setSessionId(sid);
    })();
  }, []);

  const [mutateSendMessage] = useMutation(SEND_MESSAGE);

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
  const handleSubmitPost = () => {
    const content = newPost.trim();
    if (!content && !imageUri) return;

    const newPostData: Post = {
      id: Date.now(),
      author: 'You',
      content,
      image: imageUri || undefined,
    };

    setPosts((prev) => [newPostData, ...prev]);
    resetComposer();
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
      const { data } = await mutateSendMessage({
        variables: { sessionId, content: question },
      });
      const resp = data?.sendMessage;
      if (!resp) return null;
      return {
        id: resp.id ?? `${Date.now()}-a`,
        role: resp.role ?? 'assistant',
        content: resp.content ?? '',
        sources: resp.sources ?? [],
        confidence: resp.confidence ?? null,
      };
    } catch (e: any) {
      console.warn('sendMessage error:', e?.networkError?.result || e?.message || e);
      return null;
    }
  }

  const handleChatSend = async (seed?: string) => {
    const q = (seed ?? chatInput).trim();
    if (!q || chatSending || !sessionId) return;

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
        <TouchableOpacity onPress={() => setShowDropdown((v) => !v)}>
          <Text style={styles.icon}>👤</Text>
        </TouchableOpacity>

        <Image source={require('../assets/whitelogo1.png')} style={styles.logo} />

        <TouchableOpacity onPress={() => setShowPostForm(true)}>
          <Text style={styles.icon}>➕</Text>
        </TouchableOpacity>
      </View>

      {/* Dropdown */}
      {showDropdown && (
        <View style={styles.dropdown}>
          <TouchableOpacity onPress={handleLogout}>
            <Text style={styles.dropdownItem}>🔓 Logout</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Feed */}
      <ScrollView contentContainerStyle={styles.feed}>
        {posts.map((post) => (
          <View key={post.id} style={styles.postCard}>
            <Text style={styles.author}>{post.author}</Text>
            <Text style={styles.content}>{post.content}</Text>
            {!!post.image && <Image source={{ uri: post.image }} style={styles.postImage} />}
          </View>
        ))}
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
  container: { flex: 1, backgroundColor: '#fff' },

  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },

  icon: { fontSize: 24 },
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
  postCard: { backgroundColor: '#f2f2f2', padding: 15, borderRadius: 8, marginBottom: 15, elevation: 2 },
  author: { fontWeight: 'bold', marginBottom: 5 },
  content: { fontSize: 16, marginBottom: 5 },
  postImage: { width: '100%', height: 200, borderRadius: 8, marginTop: 5 },

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
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#00cc99',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 6,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
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