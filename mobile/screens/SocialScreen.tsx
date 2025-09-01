import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useApolloClient } from '@apollo/client';
import { gql, useQuery, useMutation } from '@apollo/client';

import SocialNav from '../components/SocialNav';
import DiscussionCard from '../components/DiscussionCard';


// GraphQL Queries
const GET_TRENDING_DISCUSSIONS = gql`
  query GetTrendingDiscussions {
    trendingDiscussions {
      id
      title
      content
      discussionType
      createdAt
      likeCount
      commentCount
      user {
        name
        profilePic
      }
      stock {
        symbol
        companyName
      }
      comments {
        id
        content
        createdAt
        user {
          name
        }
      }
    }
  }
`;

const LIKE_DISCUSSION = gql`
  mutation LikeDiscussion($discussionId: ID!) {
    likeDiscussion(discussionId: $discussionId) {
      success
      message
      discussion {
        id
        likeCount
      }
    }
  }
`;

const COMMENT_ON_DISCUSSION = gql`
  mutation CommentOnDiscussion($discussionId: ID!, $content: String!) {
    commentOnDiscussion(discussionId: $discussionId, content: $content) {
      success
      message
      comment {
        id
        content
        user {
          name
        }
      }
    }
  }
`;

const CREATE_DISCUSSION = gql`
  mutation CreateStockDiscussion($title: String!, $content: String!, $stockSymbol: String!, $discussionType: String) {
    createStockDiscussion(title: $title, content: $content, stockSymbol: $stockSymbol, discussionType: $discussionType) {
      success
      message
      discussion {
        id
        title
        content
        discussionType
        createdAt
        likeCount
        commentCount
        user {
          name
          profilePic
        }
        stock {
          symbol
          companyName
        }
      }
    }
  }
`;





// Real data will be fetched from GraphQL queries

// Real data will be fetched from GraphQL queries

// Real data will be fetched from GraphQL queries

const SocialScreen: React.FC = () => {

  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [createTitle, setCreateTitle] = useState('');
  const [createContent, setCreateContent] = useState('');
  const [createStock, setCreateStock] = useState('');
  
  // Comment modal state
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [commentContent, setCommentContent] = useState('');
  const [selectedDiscussionId, setSelectedDiscussionId] = useState('');
  const [isCommenting, setIsCommenting] = useState(false);
  
  // Discussion detail modal state
  const [showDiscussionDetail, setShowDiscussionDetail] = useState(false);
  const [discussionDetail, setDiscussionDetail] = useState<any>(null);

  const client = useApolloClient();
  
  // GraphQL queries and mutations
  const { data: discussionsData, loading: discussionsLoading } = useQuery(GET_TRENDING_DISCUSSIONS);

  const [likeDiscussion] = useMutation(LIKE_DISCUSSION);
  const [commentOnDiscussion] = useMutation(COMMENT_ON_DISCUSSION);
  const [createStockDiscussion] = useMutation(CREATE_DISCUSSION);


  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await client.refetchQueries({
        include: ['GetTrendingDiscussions'],
      });
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };



  const handleCreatePress = () => {
    setShowCreateModal(true);
  };

  const handleDiscussionLike = async (discussionId: string) => {
    try {
      // Attempting to like discussion
      const result = await likeDiscussion({ variables: { discussionId } });
      // Like operation completed successfully
      
      // Refetch discussions to update like count
      await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
      // Refetch completed
    } catch (error) {
      console.error('Failed to like discussion:', error);
      Alert.alert('Error', 'Failed to like discussion. Please try again.');
    }
  };

  const handleDiscussionComment = (discussionId: string) => {
    // Open discussion detail instead of comment modal (X-style)
    const discussion = discussionsData?.trendingDiscussions?.find((d: any) => d.id === discussionId);
    if (discussion) {
      setDiscussionDetail(discussion);
      setSelectedDiscussionId(discussionId);
      setCommentContent(''); // Reset comment input
      setShowCommentModal(false); // Close comment modal if open
      setShowDiscussionDetail(true); // Open discussion detail modal
    }
  };

  const handleCommentSubmit = async () => {
    if (!commentContent.trim()) {
      Alert.alert('Error', 'Please enter a comment');
      return;
    }

    setIsCommenting(true);
    try {
      await commentOnDiscussion({ 
        variables: { 
          discussionId: selectedDiscussionId, 
          content: commentContent.trim() 
        } 
      });
      
      // Refetch discussions to update comment count
      await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
      
      // Close modal and reset
      setShowCommentModal(false);
      setCommentContent('');
      setSelectedDiscussionId('');
      
      Alert.alert('Success', 'Comment added successfully!');
    } catch (error) {
      console.error('Failed to add comment:', error);
      Alert.alert('Error', 'Failed to add comment. Please try again.');
    } finally {
      setIsCommenting(false);
    }
  };

  const handleInlineCommentSubmit = async () => {
    if (!commentContent.trim()) {
      Alert.alert('Error', 'Please enter a comment');
      return;
    }

    setIsCommenting(true);
    try {
      await commentOnDiscussion({ 
        variables: { 
          discussionId: selectedDiscussionId, 
          content: commentContent.trim() 
        } 
      });
      
      // Refetch discussions to update comment count and comments
      await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
      
      // Clear comment input but keep modal open
      setCommentContent('');
      
      // Update local discussion detail with new comment immediately
      if (discussionDetail) {
        const newComment = {
          id: Date.now().toString(), // Temporary ID
          content: commentContent.trim(),
          createdAt: new Date().toISOString(),
          user: { name: 'Test User' } // Use current user name
        };
        
        setDiscussionDetail({
          ...discussionDetail,
          comments: [...(discussionDetail.comments || []), newComment],
          commentCount: (discussionDetail.commentCount || 0) + 1
        });
      }
      
      // Refetch data in background to get real comment data
      setTimeout(async () => {
        try {
          await client.refetchQueries({ include: ['GetTrendingDiscussions'] });
          // Update discussion detail with fresh data from server
          const freshDiscussion = discussionsData?.trendingDiscussions?.find((d: any) => d.id === selectedDiscussionId);
          if (freshDiscussion) {
            setDiscussionDetail(freshDiscussion);
          }
        } catch (error) {
          console.error('Failed to refresh discussion:', error);
        }
      }, 1000);
    } catch (error) {
      console.error('Failed to add comment:', error);
      Alert.alert('Error', 'Failed to add comment. Please try again.');
    } finally {
      setIsCommenting(false);
    }
  };

  const handleDiscussionPress = (discussionId: string) => {
    // Find the discussion from the current data
    const discussion = discussionsData?.trendingDiscussions?.find((d: any) => d.id === discussionId);
    if (discussion) {
      setDiscussionDetail(discussion);
      setSelectedDiscussionId(discussionId);
      setCommentContent(''); // Reset comment input for new discussion
      setShowCommentModal(false); // Close comment modal if open
      setShowDiscussionDetail(true); // Open discussion detail modal
    }
  };

  const handleCreateSubmit = async () => {
    if (!createTitle.trim() || !createContent.trim() || !createStock.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      // Creating discussion
      
      const result = await createStockDiscussion({
        variables: {
          title: createTitle.trim(),
          content: createContent.trim(),
          stockSymbol: createStock.trim(),
          discussionType: 'analysis' // Default to analysis
        }
      });
      
      // Discussion created successfully
      
      if (result.data?.createStockDiscussion?.success) {
        Alert.alert('Success', 'Discussion created successfully!');
        
        // Refetch discussions to show the new item
        await client.refetchQueries({
          include: ['GetTrendingDiscussions']
        });
        
        setShowCreateModal(false);
        setCreateTitle('');
        setCreateContent('');
        setCreateStock('');
      } else {
        Alert.alert('Error', result.data?.createStockDiscussion?.message || 'Failed to create discussion');
      }
    } catch (error) {
      console.error('Failed to create discussion:', error);
      Alert.alert('Error', `Failed to create discussion: ${(error as any)?.message || 'Unknown error'}`);
    }
  };

  const renderContent = () => {
    return (
      <View>
        {discussionsData?.trendingDiscussions?.map((discussion: any) => (
          <DiscussionCard
            key={discussion.id}
            discussion={discussion}
            onLike={() => handleDiscussionLike(discussion.id)}
            onComment={() => handleDiscussionComment(discussion.id)}
            onPress={() => handleDiscussionPress(discussion.id)}
          />
        )) || (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No discussions yet</Text>
            <Text style={styles.emptyStateSubtext}>Be the first to start a discussion!</Text>
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Discussion Hub</Text>
        <TouchableOpacity style={styles.createButton} onPress={handleCreatePress}>
          <Icon name="plus" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Navigation */}
              <SocialNav />

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderContent()}
      </ScrollView>

      {/* Create Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create New Discussion</Text>
              <TouchableOpacity
                onPress={() => setShowCreateModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              {(
                <>
                  <Text style={styles.modalLabel}>Title</Text>
                  <TextInput
                    style={styles.textInput}
                    value={createTitle}
                    onChangeText={setCreateTitle}
                    placeholder="Enter discussion title"
                  />

                  <Text style={styles.modalLabel}>Stock Symbol</Text>
                  <TextInput
                    style={styles.textInput}
                    value={createStock}
                    onChangeText={setCreateStock}
                    placeholder="e.g., AAPL"
                    autoCapitalize="characters"
                  />

                  <Text style={styles.modalLabel}>Description</Text>
                  <TextInput
                    style={[styles.textInput, styles.textArea]}
                    value={createContent}
                    onChangeText={setCreateContent}
                    placeholder="Enter discussion description"
                    multiline
                    numberOfLines={4}
                  />
                </>
              )}
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowCreateModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  (!createTitle.trim() || !createContent.trim() || !createStock.trim()) && styles.submitButtonDisabled
                ]}
                onPress={handleCreateSubmit}
                disabled={!createTitle.trim() || !createContent.trim() || !createStock.trim()}
              >
                <Text style={styles.submitButtonText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Comment Modal */}
      <Modal
        visible={showCommentModal}
        animationType="slide"
        transparent={true}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Comment</Text>
              <TouchableOpacity
                onPress={() => setShowCommentModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.modalLabel}>Comment</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                value={commentContent}
                onChangeText={setCommentContent}
                placeholder="Enter your comment..."
                multiline
                numberOfLines={4}
              />
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowCommentModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  !commentContent.trim() && styles.submitButtonDisabled
                ]}
                onPress={handleCommentSubmit}
                disabled={!commentContent.trim() || isCommenting}
              >
                <Text style={styles.submitButtonText}>
                  {isCommenting ? 'Adding...' : 'Add Comment'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Discussion Detail Modal */}
      <Modal
        visible={showDiscussionDetail}
        animationType="slide"
        transparent={true}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{discussionDetail?.title}</Text>
              <TouchableOpacity
                onPress={() => setShowDiscussionDetail(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
              <Text style={styles.modalLabel}>Content</Text>
              <Text style={styles.discussionContent}>{discussionDetail?.content}</Text>
              
              <Text style={styles.modalLabel}>Stock</Text>
              <Text style={styles.discussionStock}>
                {discussionDetail?.stock?.companyName} ({discussionDetail?.stock?.symbol})
              </Text>
              
              <Text style={styles.modalLabel}>Created By</Text>
              <Text style={styles.discussionUser}>{discussionDetail?.user?.name}</Text>
              
              <Text style={styles.modalLabel}>Created At</Text>
              <Text style={styles.discussionDate}>
                {discussionDetail?.createdAt ? new Date(discussionDetail.createdAt).toLocaleDateString() : ''}
              </Text>
              
              <Text style={styles.modalLabel}>Comments ({discussionDetail?.commentCount || 0})</Text>
              <View style={styles.commentsSection}>
                {discussionDetail?.comments?.length > 0 ? (
                  discussionDetail.comments.map((comment: any, index: number) => (
                    <View key={index} style={styles.commentItem}>
                      <Text style={styles.commentUser}>{comment.user?.name}</Text>
                      <Text style={styles.commentContent}>{comment.content}</Text>
                      <Text style={styles.commentDate}>
                        {comment.createdAt ? new Date(comment.createdAt).toLocaleDateString() : ''}
                      </Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.noComments}>No comments yet. Be the first to comment!</Text>
                )}
              </View>
              
              <View style={styles.inlineCommentSection}>
                <Text style={styles.modalLabel}>Add Comment</Text>
                <View style={styles.commentInputContainer}>
                  <TextInput
                    style={styles.commentInput}
                    value={commentContent}
                    onChangeText={setCommentContent}
                    placeholder="💬 Write your comment here..."
                    placeholderTextColor="#8E8E93"
                    multiline
                    numberOfLines={3}
                  />
                  <TouchableOpacity
                    style={[
                      styles.commentSubmitButton,
                      !commentContent.trim() && styles.commentSubmitButtonDisabled
                    ]}
                    onPress={handleInlineCommentSubmit}
                    disabled={!commentContent.trim() || isCommenting}
                  >
                    <Text style={styles.commentSubmitText}>
                      {isCommenting ? 'Posting...' : 'Post'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
              
              {/* Add bottom padding for better scrolling */}
              <View style={styles.bottomPadding} />
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowDiscussionDetail(false)}
              >
                <Text style={styles.cancelButtonText}>Close</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.submitButton}
                onPress={() => handleDiscussionLike(discussionDetail?.id)}
              >
                <Text style={styles.submitButtonText}>
                  ❤️ {discussionDetail?.likeCount || 0} Likes
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    paddingTop: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  createButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 34,
    maxHeight: '90%',
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 4,
  },
  modalBody: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    flex: 1,
  },
  modalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
    marginTop: 16,
  },

  textInput: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#FFFFFF',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F2F2F7',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  submitButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#34C759',
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  discussionContent: {
    fontSize: 16,
    color: '#1C1C1E',
    marginBottom: 12,
    lineHeight: 22,
  },
  discussionStock: {
    fontSize: 14,
    color: '#007AFF',
    marginBottom: 12,
  },
  discussionUser: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  discussionDate: {
    fontSize: 12,
    color: '#999',
    marginBottom: 16,
  },
  commentsSection: {
    marginBottom: 16,
  },
  commentItem: {
    backgroundColor: '#F2F2F7',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  commentUser: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  commentContent: {
    fontSize: 14,
    color: '#1C1C1E',
    marginBottom: 4,
  },
  commentDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
  noComments: {
    fontSize: 14,
    color: '#8E8E93',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  addCommentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F2F2F7',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  addCommentText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  bottomPadding: {
    height: 100,
  },
  inlineCommentSection: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  commentInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 12,
    marginTop: 12,
  },
  commentInput: {
    flex: 1,
    borderWidth: 2,
    borderColor: '#34C759',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#FFFFFF',
    minHeight: 44,
    maxHeight: 100,
    textAlignVertical: 'top',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  commentSubmitButton: {
    backgroundColor: '#34C759',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    minWidth: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  commentSubmitButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  commentSubmitText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default SocialScreen;
