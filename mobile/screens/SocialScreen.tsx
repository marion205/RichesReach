import React, { useState, useEffect, useRef } from 'react';
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';

import SocialNav from '../components/SocialNav';
import RedditDiscussionCard from '../components/RedditDiscussionCard';


// GraphQL Queries
const GET_TRENDING_DISCUSSIONS = gql`
  query GetTrendingDiscussions {
    stockDiscussions {
      id
      title
      content
      discussionType
      visibility
      createdAt
      score
      commentCount
      user {
        id
        name
        profilePic
        followersCount
        followingCount
        isFollowingUser
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

const GET_SOCIAL_FEED = gql`
  query GetSocialFeed {
    socialFeed {
      id
      title
      content
      discussionType
      visibility
      createdAt
      score
      commentCount
      user {
        id
        name
        profilePic
        followersCount
        followingCount
        isFollowingUser
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

const GET_SUGGESTED_USERS = gql`
  query GetSuggestedUsers {
    suggestedUsers {
      id
      name
      profilePic
      followersCount
      followingCount
      isFollowingUser
    }
  }
`;

const GET_FOLLOWING_USERS = gql`
  query GetFollowingUsers {
    followingUsers {
      id
      name
      profilePic
      followersCount
      followingCount
      isFollowingUser
    }
  }
`;


const COMMENT_ON_DISCUSSION = gql`
  mutation CreateDiscussionComment($discussionId: ID!, $content: String!) {
    createDiscussionComment(discussionId: $discussionId, content: $content) {
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
  mutation CreateStockDiscussion($title: String!, $content: String!, $stockSymbol: String, $discussionType: String, $visibility: String) {
    createStockDiscussion(title: $title, content: $content, stockSymbol: $stockSymbol, discussionType: $discussionType, visibility: $visibility) {
      success
      message
      discussion {
        id
        title
        content
        discussionType
        visibility
        createdAt
        score
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

const UPVOTE_DISCUSSION = gql`
  mutation UpvoteDiscussion($discussionId: ID!) {
    voteDiscussion(discussionId: $discussionId, voteType: "upvote") {
      success
      message
      discussion {
        id
        score
      }
    }
  }
`;

const DOWNVOTE_DISCUSSION = gql`
  mutation DownvoteDiscussion($discussionId: ID!) {
    voteDiscussion(discussionId: $discussionId, voteType: "downvote") {
      success
      message
      discussion {
        id
        score
      }
    }
  }
`;

const TOGGLE_FOLLOW = gql`
  mutation ToggleFollow($userId: ID!) {
    toggleFollow(userId: $userId) {
      success
      following
      user {
        id
        name
        followersCount
        followingCount
        isFollowingUser
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
  const [createVisibility, setCreateVisibility] = useState<'public' | 'followers'>('followers');
  
  // Media state
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null);
  
  // TextInput refs
  const contentInputRef = useRef<TextInput>(null);
  
  // Comment modal state
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [commentContent, setCommentContent] = useState('');
  const [selectedDiscussionId, setSelectedDiscussionId] = useState('');
  const [isCommenting, setIsCommenting] = useState(false);
  
  // Discussion detail modal state
  const [showDiscussionDetail, setShowDiscussionDetail] = useState(false);
  const [discussionDetail, setDiscussionDetail] = useState<any>(null);
  
  // Feed type state
  const [feedType, setFeedType] = useState<'trending' | 'following'>('trending');
  
  // User following state
  const [showUserModal, setShowUserModal] = useState(false);
  const [userModalType, setUserModalType] = useState<'suggested' | 'following'>('suggested');

  const client = useApolloClient();
  
  // GraphQL queries and mutations
  const { data: discussionsData, loading: discussionsLoading, refetch: refetchDiscussions } = useQuery(
    feedType === 'trending' ? GET_TRENDING_DISCUSSIONS : GET_SOCIAL_FEED
  );
  
  const { data: suggestedUsersData, refetch: refetchSuggestedUsers } = useQuery(GET_SUGGESTED_USERS);
  const { data: followingUsersData, refetch: refetchFollowingUsers } = useQuery(GET_FOLLOWING_USERS);

  const [commentOnDiscussion] = useMutation(COMMENT_ON_DISCUSSION);
  const [createStockDiscussion] = useMutation(CREATE_DISCUSSION);
  const [upvoteDiscussion] = useMutation(UPVOTE_DISCUSSION);
  const [downvoteDiscussion] = useMutation(DOWNVOTE_DISCUSSION);
  const [toggleFollow] = useMutation(TOGGLE_FOLLOW);


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


  const handleUpvote = async (discussionId: string) => {
    try {
      console.log('🔼 Upvoting discussion:', discussionId);
      const result = await upvoteDiscussion({ variables: { discussionId } });
      console.log('✅ Upvote result:', result);
      
      // Refetch discussions to update score
      await refetchDiscussions();
      console.log('🔄 Discussions refetched after upvote');
    } catch (error) {
      console.error('❌ Failed to upvote discussion:', error);
      Alert.alert('Error', 'Failed to upvote discussion. Please try again.');
    }
  };

  const handleDownvote = async (discussionId: string) => {
    try {
      console.log('🔽 Downvoting discussion:', discussionId);
      const result = await downvoteDiscussion({ variables: { discussionId } });
      console.log('✅ Downvote result:', result);
      
      // Refetch discussions to update score
      await refetchDiscussions();
      console.log('🔄 Discussions refetched after downvote');
    } catch (error) {
      console.error('❌ Failed to downvote discussion:', error);
      Alert.alert('Error', 'Failed to downvote discussion. Please try again.');
    }
  };

  const handleToggleFollow = async (userId: string) => {
    try {
      console.log('👥 Toggling follow for user:', userId);
      const result = await toggleFollow({
        variables: { userId }
      });
      console.log('👥 Follow result:', result);
      
      if (result.data?.toggleFollow?.success) {
        console.log('✅ Follow toggle successful');
        // Refetch all relevant data
        await Promise.all([
          refetchDiscussions(),
          refetchSuggestedUsers(),
          refetchFollowingUsers()
        ]);
        console.log('🔄 All data refetched after follow toggle');
      } else {
        console.log('❌ Follow toggle failed');
      }
    } catch (error) {
      console.error('❌ Follow toggle error:', error);
    }
  };

  // Helper function to determine if submit button should be disabled
  const isSubmitDisabled = () => {
    const hasMedia = selectedImage || selectedVideo;
    const hasContent = createContent.trim().length > 0;
    const hasValidTitle = createTitle.trim().length >= 5;
    
    // Must have a valid title
    if (!hasValidTitle) return true;
    
    // Must have either content (with min length) or media
    if (!hasMedia && !hasContent) return true;
    if (hasContent && createContent.trim().length < 10) return true;
    
    return false;
  };

  const handleDiscussionComment = (discussionId: string) => {
    console.log('💬 COMMENT BUTTON CLICKED');
    console.log('📊 Comment button data:', {
      discussionId: discussionId,
      discussionsData: discussionsData,
      stockDiscussions: discussionsData?.stockDiscussions
    });
    
    // Open discussion detail instead of comment modal (X-style)
    const discussion = discussionsData?.stockDiscussions?.find((d: any) => d.id === discussionId);
    console.log('🔍 Found discussion:', discussion);
    
    if (discussion) {
      console.log('✅ Discussion found, opening detail modal');
      console.log('📋 Discussion details:', {
        id: discussion.id,
        title: discussion.title,
        score: discussion.score,
        commentCount: discussion.commentCount
      });
      
      setDiscussionDetail(discussion);
      setSelectedDiscussionId(discussionId);
      setCommentContent(''); // Reset comment input
      setShowCommentModal(false); // Close comment modal if open
      setShowDiscussionDetail(true); // Open discussion detail modal
      
      console.log('🔄 Modal state updated:', {
        discussionDetail: discussion,
        selectedDiscussionId: discussionId,
        showCommentModal: false,
        showDiscussionDetail: true
      });
    } else {
      console.log('❌ Discussion not found for ID:', discussionId);
    }
  };

  const handleCommentSubmit = async () => {
    console.log('🚀 COMMENT SUBMISSION STARTED');
    console.log('📊 Current state:', {
      commentContent: commentContent,
      commentContentLength: commentContent?.length || 0,
      selectedDiscussionId: selectedDiscussionId,
      isCommenting: isCommenting,
      showCommentModal: showCommentModal
    });

    if (!commentContent.trim()) {
      console.log('❌ No comment content provided');
      Alert.alert('Error', 'Please enter a comment');
      return;
    }

    console.log('💬 Starting comment submission...');
    console.log('📝 Comment data:', {
      discussionId: selectedDiscussionId,
      content: commentContent.trim(),
      contentLength: commentContent.trim().length
    });

    console.log('🔍 Testing backend connection before comment...');
    try {
      const testResponse = await fetch('http://192.168.1.151:8000/graphql/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: '{ __typename }'
        })
      });
      console.log('🌐 Backend connection test status:', testResponse.status);
      if (testResponse.ok) {
        console.log('✅ Backend is reachable for comment');
      } else {
        console.log('❌ Backend connection failed for comment');
      }
    } catch (testError) {
      console.log('❌ Backend connection test failed:', testError);
    }

    setIsCommenting(true);
    console.log('🔄 Set isCommenting to true');
    
    try {
      console.log('📤 Sending comment GraphQL mutation...');
      console.log('🔗 Comment mutation variables:', { 
        discussionId: selectedDiscussionId, 
        content: commentContent.trim() 
      });
      
      const result = await commentOnDiscussion({ 
        variables: { 
          discussionId: selectedDiscussionId, 
          content: commentContent.trim() 
        } 
      });
      
      console.log('✅ Comment mutation completed successfully!');
      console.log('📊 Comment result:', result);
      console.log('📊 Comment result data:', result.data);
      console.log('📊 Comment result data.createDiscussionComment:', result.data?.createDiscussionComment);
      
      if (result.data?.createDiscussionComment?.success) {
        console.log('🎉 Comment creation was successful!');
        console.log('📋 Created comment:', result.data.createDiscussionComment.comment);
      } else {
        console.log('⚠️ Comment creation returned success: false');
        console.log('📋 Error message:', result.data?.createDiscussionComment?.message);
      }
      
      // Refetch discussions to update comment count
      console.log('🔄 Refetching discussions to update comment count...');
      console.log('📊 Before refetch - discussionsData:', discussionsData?.stockDiscussions?.map((d: any) => ({
        id: d.id,
        title: d.title,
        commentCount: d.commentCount
      })));
      
      // Add a small delay to ensure backend has processed the comment
      console.log('⏳ Waiting 500ms for backend to process comment...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const refetchResult = await refetchDiscussions();
      console.log('📊 Refetch result:', refetchResult);
      
      console.log('📊 After refetch - discussionsData:', discussionsData?.stockDiscussions?.map((d: any) => ({
        id: d.id,
        title: d.title,
        commentCount: d.commentCount
      })));
      console.log('✅ Discussions refetched after comment');
      
      // Close modal and reset
      console.log('🧹 Closing modal and resetting form...');
      setShowCommentModal(false);
      setCommentContent('');
      setSelectedDiscussionId('');
      console.log('✅ Modal closed and form reset');
      
      Alert.alert('Success', 'Comment added successfully!');
      console.log('🎉 Comment submission completed successfully!');
    } catch (error) {
      console.error('💥 COMMENT SUBMISSION FAILED');
      console.error('❌ Failed to add comment:', error);
      console.error('❌ Error message:', (error as any)?.message);
      console.error('❌ Error stack:', (error as any)?.stack);
      console.error('❌ Error details:', JSON.stringify(error, null, 2));
      
      if ((error as any)?.networkError) {
        console.error('🌐 Network error details:', (error as any).networkError);
      }
      if ((error as any)?.graphQLErrors) {
        console.error('📊 GraphQL errors:', (error as any).graphQLErrors);
      }
      
      Alert.alert('Error', 'Failed to add comment. Please try again.');
    } finally {
      console.log('🏁 Comment submission process finished');
      setIsCommenting(false);
      console.log('🔄 Set isCommenting to false');
    }
  };

  // Media picker functions
  const pickImage = async () => {
    console.log('📸 Picking image...');
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [16, 9],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        console.log('✅ Image selected:', result.assets[0].uri);
        setSelectedImage(result.assets[0].uri);
        setSelectedVideo(null);
        setMediaType('image');
      } else {
        console.log('❌ Image selection cancelled');
      }
    } catch (error) {
      console.error('❌ Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const pickVideo = async () => {
    console.log('🎥 Picking video...');
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: true,
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        console.log('✅ Video selected:', result.assets[0].uri);
        setSelectedVideo(result.assets[0].uri);
        setSelectedImage(null);
        setMediaType('video');
      } else {
        console.log('❌ Video selection cancelled');
      }
    } catch (error) {
      console.error('❌ Error picking video:', error);
      Alert.alert('Error', 'Failed to pick video');
    }
  };

  const removeMedia = () => {
    console.log('🗑️ Removing media...');
    setSelectedImage(null);
    setSelectedVideo(null);
    setMediaType(null);
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
          const freshDiscussion = discussionsData?.stockDiscussions?.find((d: any) => d.id === selectedDiscussionId);
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
    const discussion = discussionsData?.stockDiscussions?.find((d: any) => d.id === discussionId);
    if (discussion) {
      setDiscussionDetail(discussion);
      setSelectedDiscussionId(discussionId);
      setCommentContent(''); // Reset comment input for new discussion
      setShowCommentModal(false); // Close comment modal if open
      setShowDiscussionDetail(true); // Open discussion detail modal
    }
  };

  const handleCreateSubmit = async () => {
    console.log('🚀 Starting discussion creation process...');
    console.log('📝 Form data:', {
      title: createTitle,
      titleLength: createTitle.trim().length,
      content: createContent,
      contentLength: createContent.trim().length,
      stock: createStock,
      stockLength: createStock.trim().length
    });

    // Test backend connection first
    try {
      console.log('🔍 Testing backend connection...');
      const response = await fetch('http://192.168.1.151:8000/graphql/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: '{ __schema { types { name } } }'
        })
      });
      console.log('🌐 Backend connection test status:', response.status);
      if (response.ok) {
        console.log('✅ Backend is reachable');
      } else {
        console.log('❌ Backend connection failed:', response.status);
      }
    } catch (error) {
      console.log('❌ Backend connection error:', error);
    }

    // Use the helper function for validation
    if (isSubmitDisabled()) {
      console.log('❌ Validation failed: Form validation failed');
      Alert.alert('Error', 'Please check your input and try again');
      return;
    }

    // Validate minimum length requirements
    if (createTitle.trim().length < 5) {
      console.log('❌ Validation failed: Title too short');
      Alert.alert('Error', 'Title must be at least 5 characters long');
      return;
    }

    console.log('✅ Validation passed, proceeding with GraphQL mutation...');

    try {
      // Prepare content with media information
      let finalContent = createContent.trim();
      
      // Add media information to content if media is selected
      if (selectedImage) {
        finalContent += `\n\n[IMAGE: ${selectedImage}]`;
        console.log('📸 Adding image to content:', selectedImage);
      }
      
      if (selectedVideo) {
        finalContent += `\n\n[VIDEO: ${selectedVideo}]`;
        console.log('🎥 Adding video to content:', selectedVideo);
      }
      
      // Creating discussion
      const variables = {
        title: createTitle.trim(),
        content: finalContent,
        stockSymbol: createStock.trim() || null, // Optional - like Reddit posts
        discussionType: 'general', // Default to general discussion
        visibility: createVisibility // Public or followers only
      };
      
      console.log('📤 Sending GraphQL mutation with variables:', variables);
      console.log('🔗 GraphQL mutation query:', CREATE_DISCUSSION.loc?.source?.body);
      console.log('🌐 Apollo Client URI:', 'http://192.168.1.151:8000/graphql/');
      console.log('🔐 Auth token available:', !!await AsyncStorage.getItem('token'));
      
      const result = await createStockDiscussion({
        variables: variables
      });
      
      console.log('📥 Received GraphQL response:', result);
      console.log('📊 Response data:', result.data);
      console.log('📊 CreateStockDiscussion result:', result.data?.createStockDiscussion);
      
      // Discussion created successfully
      
      if (result.data?.createStockDiscussion?.success) {
        console.log('✅ Discussion created successfully!');
        console.log('📋 Created discussion:', result.data.createStockDiscussion.discussion);
        Alert.alert('Success', 'Discussion created successfully!');
        
        // Refetch discussions to show the new item
        console.log('🔄 Refetching discussions...');
        await refetchDiscussions();
        console.log('✅ Discussions refetched');
        
        setShowCreateModal(false);
        setCreateTitle('');
        setCreateContent('');
        setCreateStock('');
        setCreateVisibility('followers'); // Reset to default
        // Clear media
        setSelectedImage(null);
        setSelectedVideo(null);
        setMediaType(null);
        console.log('🧹 Form cleared and modal closed');
      } else {
        console.log('❌ Discussion creation failed:', result.data?.createStockDiscussion?.message);
        Alert.alert('Error', result.data?.createStockDiscussion?.message || 'Failed to create discussion');
      }
    } catch (error) {
      console.error('💥 Failed to create discussion - Full error:', error);
      console.error('💥 Error message:', (error as any)?.message);
      console.error('💥 Error stack:', (error as any)?.stack);
      console.error('💥 Error details:', JSON.stringify(error, null, 2));
      Alert.alert('Error', `Failed to create discussion: ${(error as any)?.message || 'Unknown error'}`);
    }
  };

  const renderContent = () => {
    console.log('🎨 RENDERING CONTENT');
    console.log('📊 Render data:', {
      discussionsData: discussionsData,
      stockDiscussions: discussionsData?.stockDiscussions,
      discussionsCount: discussionsData?.stockDiscussions?.length || 0,
      loading: discussionsLoading
    });
    
    return (
      <View>
        {discussionsData?.stockDiscussions?.map((discussion: any) => {
          console.log('🔄 Rendering RedditDiscussionCard for discussion:', {
            id: discussion.id,
            title: discussion.title,
            score: discussion.score,
            commentCount: discussion.commentCount
          });
          
          return (
            <RedditDiscussionCard
              key={discussion.id}
              discussion={discussion}
              onUpvote={() => {
                console.log('🔼 Upvote button clicked for discussion:', discussion.id);
                handleUpvote(discussion.id);
              }}
              onDownvote={() => {
                console.log('🔽 Downvote button clicked for discussion:', discussion.id);
                handleDownvote(discussion.id);
              }}
              onComment={() => {
                console.log('💬 Comment button clicked for discussion:', discussion.id);
                handleDiscussionComment(discussion.id);
              }}
              onPress={() => {
                console.log('👆 Discussion card pressed for discussion:', discussion.id);
                handleDiscussionPress(discussion.id);
              }}
              onFollow={(userId) => {
                console.log('👥 Follow button clicked for user:', userId);
                handleToggleFollow(userId);
              }}
            />
          );
        }) || (
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
              <SocialNav 
                feedType={feedType}
                onFeedTypeChange={setFeedType}
              />

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
        onShow={() => {
          console.log('📱 Create discussion modal opened');
          console.log('📊 Initial form state:', {
            title: createTitle,
            content: createContent,
            stock: createStock
          });
        }}
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

            <ScrollView style={styles.modalBody} keyboardShouldPersistTaps="handled">
              {(
                <>
                  <Text style={styles.modalLabel}>Title</Text>
                  <TextInput
                    style={styles.textInput}
                    value={createTitle}
                    onChangeText={(text) => {
                      console.log('📝 Title changed:', text, 'Length:', text.length);
                      setCreateTitle(text);
                    }}
                    placeholder="Enter discussion title"
                  />

                  <Text style={styles.modalLabel}>Stock Symbol (Optional)</Text>
                  <TextInput
                    style={styles.textInput}
                    value={createStock}
                    onChangeText={(text) => {
                      console.log('📈 Stock symbol changed:', text, 'Length:', text.length);
                      setCreateStock(text);
                    }}
                    placeholder="e.g., AAPL (leave blank for general discussion)"
                    autoCapitalize="characters"
                  />

                  <Text style={styles.modalLabel}>Post Visibility</Text>
                  <View style={styles.visibilityContainer}>
                    <TouchableOpacity
                      style={[
                        styles.visibilityOption,
                        createVisibility === 'public' && styles.visibilityOptionSelected
                      ]}
                      onPress={() => {
                        console.log('🌍 Public visibility selected');
                        setCreateVisibility('public');
                      }}
                    >
                      <Icon 
                        name="globe" 
                        size={16} 
                        color={createVisibility === 'public' ? '#FFFFFF' : '#007AFF'} 
                      />
                      <Text style={[
                        styles.visibilityOptionText,
                        createVisibility === 'public' && styles.visibilityOptionTextSelected
                      ]}>
                        Public
                      </Text>
                      <Text style={[
                        styles.visibilityOptionSubtext,
                        createVisibility === 'public' && styles.visibilityOptionSubtextSelected
                      ]}>
                        Everyone can see
                      </Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity
                      style={[
                        styles.visibilityOption,
                        createVisibility === 'followers' && styles.visibilityOptionSelected
                      ]}
                      onPress={() => {
                        console.log('👥 Followers visibility selected');
                        setCreateVisibility('followers');
                      }}
                    >
                      <Icon 
                        name="users" 
                        size={16} 
                        color={createVisibility === 'followers' ? '#FFFFFF' : '#007AFF'} 
                      />
                      <Text style={[
                        styles.visibilityOptionText,
                        createVisibility === 'followers' && styles.visibilityOptionTextSelected
                      ]}>
                        Followers Only
                      </Text>
                      <Text style={[
                        styles.visibilityOptionSubtext,
                        createVisibility === 'followers' && styles.visibilityOptionSubtextSelected
                      ]}>
                        Only followers can see
                      </Text>
                    </TouchableOpacity>
                  </View>

                  <Text style={styles.modalLabel}>Description</Text>
                  <TextInput
                    ref={contentInputRef}
                    style={[styles.textInput, styles.textArea]}
                    value={createContent}
                    onChangeText={(text) => {
                      console.log('📄 Content changed:', text, 'Length:', text.length);
                      setCreateContent(text);
                    }}
                    placeholder="Share your thoughts, analysis, or questions (optional if you upload media). You can include links to images, videos, or articles!"
                    multiline
                    numberOfLines={4}
                    autoCapitalize="sentences"
                    autoCorrect={true}
                    spellCheck={true}
                    keyboardType="default"
                    returnKeyType="default"
                    blurOnSubmit={false}
                    textContentType="none"
                    autoComplete="off"
                    dataDetectorTypes="all"
                    selectTextOnFocus={false}
                    clearButtonMode="never"
                    onContentSizeChange={(event) => {
                      // Allow dynamic height for multiline
                      console.log('📏 Content size changed:', event.nativeEvent.contentSize);
                    }}
                    onSelectionChange={(event) => {
                      console.log('📍 Selection changed:', event.nativeEvent.selection);
                    }}
                    onFocus={() => {
                      console.log('🎯 Content TextInput focused');
                    }}
                    onBlur={() => {
                      console.log('👁️ Content TextInput blurred');
                    }}
                    contextMenuHidden={false}
                    allowFontScaling={true}
                    maxLength={2000}
                    editable={true}
                    caretHidden={false}
                    importantForAutofill="no"
                  />

                  {/* Media Upload Section */}
                  <Text style={styles.modalLabel}>Add Media (Optional)</Text>
                  <View style={styles.mediaUploadContainer}>
                    <TouchableOpacity 
                      style={[
                        styles.mediaButton,
                        selectedImage && styles.mediaButtonSelected
                      ]} 
                      onPress={pickImage}
                    >
                      <Icon 
                        name="image" 
                        size={20} 
                        color={selectedImage ? "#FFFFFF" : "#007AFF"} 
                      />
                      <Text style={[
                        styles.mediaButtonText,
                        selectedImage && styles.mediaButtonTextSelected
                      ]}>
                        Photo
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[
                        styles.mediaButton,
                        selectedVideo && styles.mediaButtonSelected
                      ]} 
                      onPress={pickVideo}
                    >
                      <Icon 
                        name="video" 
                        size={20} 
                        color={selectedVideo ? "#FFFFFF" : "#007AFF"} 
                      />
                      <Text style={[
                        styles.mediaButtonText,
                        selectedVideo && styles.mediaButtonTextSelected
                      ]}>
                        Video
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {/* Media Attachment Indicator */}
                  {(selectedImage || selectedVideo) && (
                    <View style={styles.mediaAttachmentIndicator}>
                      <View style={styles.mediaAttachmentContent}>
                        <Icon 
                          name={selectedImage ? "image" : "video"} 
                          size={16} 
                          color="#007AFF" 
                        />
                        <Text style={styles.mediaAttachmentText}>
                          {selectedImage ? "Image attached" : "Video attached"}
                        </Text>
                        <TouchableOpacity 
                          onPress={removeMedia} 
                          style={styles.removeAttachmentButton}
                        >
                          <Icon name="x" size={14} color="#8E8E93" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  )}
                </>
              )}
            </ScrollView>

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
                  isSubmitDisabled() && styles.submitButtonDisabled
                ]}
                onPress={() => {
                  console.log('🔘 Create button pressed');
                  console.log('📊 Button state check:', {
                    hasTitle: !!createTitle.trim(),
                    hasContent: !!createContent.trim(),
                    hasMedia: selectedImage || selectedVideo,
                    titleLength: createTitle.trim().length,
                    contentLength: createContent.trim().length,
                    titleValid: createTitle.trim().length >= 5,
                    contentValid: createContent.trim().length >= 10,
                    buttonDisabled: isSubmitDisabled()
                  });
                  handleCreateSubmit();
                }}
                disabled={isSubmitDisabled()}
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
                onPress={() => handleUpvote(discussionDetail?.id)}
              >
                <Text style={styles.submitButtonText}>
                  🔼 {discussionDetail?.score || 0} Score
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
  descriptionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  // Media upload styles
  mediaUploadContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  mediaButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F2F2F7',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    gap: 8,
  },
  mediaButtonText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  mediaButtonSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  mediaButtonTextSelected: {
    color: '#FFFFFF',
  },
  mediaPreview: {
    marginBottom: 16,
  },
  mediaPreviewLabel: {
    fontSize: 14,
    color: '#1C1C1E',
    marginBottom: 8,
    fontWeight: '500',
  },
  mediaPreviewItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  mediaPreviewText: {
    flex: 1,
    fontSize: 14,
    color: '#1C1C1E',
  },
  removeMediaButton: {
    padding: 4,
    marginLeft: 8,
  },
  mediaAttachmentIndicator: {
    marginBottom: 16,
    backgroundColor: '#F0F8FF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  mediaAttachmentContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
  },
  mediaAttachmentText: {
    flex: 1,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
    marginLeft: 8,
  },
  removeAttachmentButton: {
    padding: 4,
    marginLeft: 8,
  },
  visibilityContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 12,
  },
  visibilityOption: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E5EA',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  visibilityOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#007AFF',
  },
  visibilityOptionText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginTop: 8,
    marginBottom: 4,
  },
  visibilityOptionTextSelected: {
    color: '#FFFFFF',
  },
  visibilityOptionSubtext: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
  },
  visibilityOptionSubtextSelected: {
    color: '#FFFFFF',
  },
});

export default SocialScreen;
