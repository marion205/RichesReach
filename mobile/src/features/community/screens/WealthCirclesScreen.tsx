import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator, 
  Alert,
  TextInput
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

export default function WealthCirclesScreen() {
  const [loading, setLoading] = useState(false);
  const [circles, setCircles] = useState([
    {
      id: '1',
      name: 'BIPOC Investment Strategies',
      description: 'Sharing investment strategies and experiences within our community',
      focus_area: 'investment_strategy',
      member_count: 1247,
      cultural_focus: 'BIPOC',
      is_private: false,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: '2',
      name: 'First-Gen Wealth Builders',
      description: 'Supporting first-generation wealth builders on their journey',
      focus_area: 'family_finances',
      member_count: 892,
      cultural_focus: 'First Generation',
      is_private: false,
      created_at: '2024-01-05T00:00:00Z'
    },
    {
      id: '3',
      name: 'Tech Career & Finance',
      description: 'Navigating tech careers while building wealth',
      focus_area: 'career_advice',
      member_count: 634,
      cultural_focus: 'Tech Professionals',
      is_private: false,
      created_at: '2024-01-10T00:00:00Z'
    }
  ]);

  const [recentPosts, setRecentPosts] = useState([
    {
      id: '1',
      title: 'Just hit my first $10K savings goal!',
      content: 'After 6 months of disciplined saving, I finally reached my first major milestone. The key was automating my savings and cutting unnecessary expenses.',
      author: 'Anonymous',
      circle: 'BIPOC Investment Strategies',
      likes: 23,
      replies: 8,
      created_at: '2024-01-15T14:30:00Z',
      is_anonymous: true
    },
    {
      id: '2',
      title: 'Real estate investment advice needed',
      content: 'Looking to buy my first rental property. Any advice on getting started with real estate investing?',
      author: 'Anonymous',
      circle: 'First-Gen Wealth Builders',
      likes: 15,
      replies: 12,
      created_at: '2024-01-15T12:15:00Z',
      is_anonymous: true
    },
    {
      id: '3',
      title: 'Tech stock options strategy',
      content: 'How do you all handle tech stock options? Hold, exercise, or diversify?',
      author: 'Anonymous',
      circle: 'Tech Career & Finance',
      likes: 31,
      replies: 19,
      created_at: '2024-01-15T10:45:00Z',
      is_anonymous: true
    }
  ]);

  const [showCreateCircle, setShowCreateCircle] = useState(false);
  const [newCircleName, setNewCircleName] = useState('');
  const [newCircleDescription, setNewCircleDescription] = useState('');

  const createCircle = () => {
    if (!newCircleName.trim() || !newCircleDescription.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    const newCircle = {
      id: Date.now().toString(),
      name: newCircleName,
      description: newCircleDescription,
      focus_area: 'general',
      member_count: 1,
      cultural_focus: 'Community',
      is_private: false,
      created_at: new Date().toISOString()
    };

    setCircles(prev => [newCircle, ...prev]);
    setNewCircleName('');
    setNewCircleDescription('');
    setShowCreateCircle(false);
    Alert.alert('Success', 'Circle created successfully!');
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes}m ago`;
    }
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['#8B5CF6', '#7C3AED']}
        style={styles.headerGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.headerContent}>
          <Ionicons name="people" size={32} color="#fff" />
          <Text style={styles.headerTitle}>Wealth Circles</Text>
          <Text style={styles.headerSubtitle}>Connect with your community</Text>
        </View>
      </LinearGradient>

      {/* Create Circle Section */}
      <View style={styles.section}>
        <TouchableOpacity 
          style={styles.createButton}
          onPress={() => setShowCreateCircle(!showCreateCircle)}
        >
          <Ionicons name="add-circle" size={24} color="#8B5CF6" />
          <Text style={styles.createButtonText}>Create New Circle</Text>
        </TouchableOpacity>

        {showCreateCircle && (
          <View style={styles.createForm}>
            <TextInput
              style={styles.input}
              placeholder="Circle Name"
              value={newCircleName}
              onChangeText={setNewCircleName}
            />
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Description"
              value={newCircleDescription}
              onChangeText={setNewCircleDescription}
              multiline
              numberOfLines={3}
            />
            <View style={styles.formButtons}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => setShowCreateCircle(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.submitButton}
                onPress={createCircle}
              >
                <Text style={styles.submitButtonText}>Create Circle</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>

      {/* Wealth Circles */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Circles</Text>
        {circles.map((circle) => (
          <TouchableOpacity key={circle.id} style={styles.circleCard}>
            <View style={styles.circleHeader}>
              <View style={styles.circleIcon}>
                <Ionicons name="people-circle" size={24} color="#8B5CF6" />
              </View>
              <View style={styles.circleInfo}>
                <Text style={styles.circleName}>{circle.name}</Text>
                <Text style={styles.circleDescription}>{circle.description}</Text>
                <View style={styles.circleMeta}>
                  <Text style={styles.memberCount}>{circle.member_count} members</Text>
                  <Text style={styles.culturalFocus}>{circle.cultural_focus}</Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#8E8E93" />
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recent Community Posts */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Community Posts</Text>
        {recentPosts.map((post) => (
          <View key={post.id} style={styles.postCard}>
            <View style={styles.postHeader}>
              <View style={styles.postAuthor}>
                <Ionicons name="person-circle" size={20} color="#8B5CF6" />
                <Text style={styles.postAuthorName}>{post.author}</Text>
              </View>
              <Text style={styles.postTime}>{formatTimestamp(post.created_at)}</Text>
            </View>
            <Text style={styles.postTitle}>{post.title}</Text>
            <Text style={styles.postContent}>{post.content}</Text>
            <View style={styles.postFooter}>
              <View style={styles.postStats}>
                <Ionicons name="heart" size={16} color="#FF3B30" />
                <Text style={styles.postStatText}>{post.likes}</Text>
                <Ionicons name="chatbubble" size={16} color="#8E8E93" />
                <Text style={styles.postStatText}>{post.replies}</Text>
              </View>
              <Text style={styles.postCircle}>{post.circle}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Community Guidelines */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Community Guidelines</Text>
        <View style={styles.guidelinesCard}>
          <Text style={styles.guidelineText}>• Be respectful and supportive of all members</Text>
          <Text style={styles.guidelineText}>• Share knowledge and experiences to help others</Text>
          <Text style={styles.guidelineText}>• Maintain confidentiality and respect privacy</Text>
          <Text style={styles.guidelineText}>• Focus on financial education and empowerment</Text>
          <Text style={styles.guidelineText}>• No spam, self-promotion, or harmful advice</Text>
          <Text style={styles.guidelineText}>• Celebrate each other's successes and learn from challenges</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f8f9fa' 
  },
  headerGradient: {
    paddingVertical: 30,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    marginBottom: 20,
    alignItems: 'center',
  },
  headerContent: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
    marginTop: 10,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#e0e0ff',
    marginTop: 5,
    textAlign: 'center',
  },
  
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#8B5CF6',
    borderStyle: 'dashed',
  },
  createButtonText: {
    marginLeft: 10,
    fontSize: 16,
    fontWeight: '600',
    color: '#8B5CF6',
  },
  
  createForm: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
    backgroundColor: '#ffffff',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  formButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  cancelButton: {
    flex: 1,
    padding: 12,
    marginRight: 8,
    borderRadius: 8,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#6b7280',
    fontWeight: '600',
  },
  submitButton: {
    flex: 1,
    padding: 12,
    marginLeft: 8,
    borderRadius: 8,
    backgroundColor: '#8B5CF6',
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  
  circleCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  circleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  circleIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  circleInfo: {
    flex: 1,
  },
  circleName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 4,
  },
  circleDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
    lineHeight: 20,
  },
  circleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  memberCount: {
    fontSize: 12,
    color: '#8B5CF6',
    fontWeight: '600',
    marginRight: 12,
  },
  culturalFocus: {
    fontSize: 12,
    color: '#6b7280',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  
  postCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  postAuthor: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  postAuthorName: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '600',
    color: '#8B5CF6',
  },
  postTime: {
    fontSize: 12,
    color: '#9ca3af',
  },
  postTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 8,
  },
  postContent: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
    marginBottom: 12,
  },
  postFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  postStatText: {
    marginLeft: 4,
    marginRight: 12,
    fontSize: 12,
    color: '#6b7280',
  },
  postCircle: {
    fontSize: 12,
    color: '#8B5CF6',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  
  guidelinesCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  guidelineText: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 22,
    marginBottom: 8,
  },
});
