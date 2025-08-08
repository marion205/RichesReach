import React, { useState, useLayoutEffect } from 'react';
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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Icon from 'react-native-vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';

type Post = {
  id: number;
  author: string;
  content: string;
  image?: string;
};

export default function HomeScreen() {
  const navigation = useNavigation();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showPostForm, setShowPostForm] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [posts, setPosts] = useState<Post[]>([
    { id: 1, author: 'Alice', content: 'Just joined RichesReach! 🚀' },
    { id: 2, author: 'Bob', content: 'Excited about financial freedom! 💰' },
    { id: 3, author: 'Clara', content: 'Investing in crypto and stocks 📈' },
  ]);

  useLayoutEffect(() => {
    navigation.setOptions({ headerShown: false });
  }, [navigation]);

  const handleLogout = async () => {
    await AsyncStorage.removeItem('token');
    Alert.alert('Logged out');
    navigation.replace('Login');
  };

  const handleSubmitPost = () => {
    if (newPost.trim()) {
      const newPostData: Post = {
        id: Date.now(),
        author: 'You',
        content: newPost.trim(),
        image: imageUri || undefined,
      };
      setPosts([newPostData, ...posts]);
      setNewPost('');
      setImageUri(null);
      setShowPostForm(false);
    }
  };

  const closeModal = () => {
    setNewPost('');
    setImageUri(null);
    setShowPostForm(false);
  };

  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      alert('Permission to access media library is required!');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 1,
    });

    if (!result.canceled && result.assets.length > 0) {
      setImageUri(result.assets[0].uri);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerBar}>
        <TouchableOpacity onPress={() => setShowDropdown(!showDropdown)}>
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
            {post.image && <Image source={{ uri: post.image }} style={styles.postImage} />}
          </View>
        ))}
      </ScrollView>

      {/* Modal */}
      <Modal visible={showPostForm} animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={closeModal}>
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

          {imageUri && (
            <Image source={{ uri: imageUri }} style={styles.previewImage} />
          )}

          <TouchableOpacity style={styles.modalPostButton} onPress={handleSubmitPost}>
            <Text style={styles.postButtonText}>Post</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={closeModal} style={styles.cancelButton}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </View>
  );
}

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

  logo: {
    width: 90,
    height: 90,
    resizeMode: 'contain',
  },

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
  },

  dropdownItem: {
    fontSize: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },

  feed: {
    padding: 20,
    paddingBottom: 100,
  },

  postCard: {
    backgroundColor: '#f2f2f2',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    elevation: 2,
  },

  author: {
    fontWeight: 'bold',
    marginBottom: 5,
  },

  content: {
    fontSize: 16,
    marginBottom: 5,
  },

  postImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    marginTop: 5,
  },

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

  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },

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
    padding: 10,
  },

  imageButton: {
    paddingTop: 10,
    paddingRight: 10,
  },

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

  cancelButton: {
    marginTop: 10,
    alignItems: 'center',
  },

  cancelText: {
    color: 'gray',
    fontSize: 16,
  },

  postButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});