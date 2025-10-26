// Advanced Live Streaming Component with Polls, Q&A, and Screen Sharing
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  FlatList,
  TextInput,
  Alert,
  Dimensions,
  ActivityIndicator,
  ScrollView,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withSequence,
} from 'react-native-reanimated';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface AdvancedLiveStreamingProps {
  visible: boolean;
  onClose: () => void;
  circleId: string;
  isHost: boolean;
  circleName: string;
}

interface Poll {
  id: string;
  question: string;
  options: PollOption[];
  is_multiple_choice: boolean;
  total_votes: number;
  expires_at?: string;
  created_at: string;
}

interface PollOption {
  id: string;
  text: string;
  votes: number;
  order: number;
}

interface QAQuestion {
  id: string;
  question: string;
  user: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  status: 'pending' | 'answered' | 'dismissed';
  answer?: string;
  answered_by?: {
    id: string;
    username: string;
  };
  upvotes: number;
  created_at: string;
}

interface ScreenShare {
  id: string;
  share_type: 'screen' | 'window' | 'tab';
  title: string;
  is_active: boolean;
  started_at: string;
}

export default function AdvancedLiveStreaming({
  visible,
  onClose,
  circleId,
  isHost,
  circleName,
}: AdvancedLiveStreamingProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [viewerCount, setViewerCount] = useState(0);
  const [streamDuration, setStreamDuration] = useState(0);
  const [streamStartTime, setStreamStartTime] = useState<Date | null>(null);
  const [streamCategory, setStreamCategory] = useState<'market-analysis' | 'portfolio-review' | 'qa' | 'general'>('general');
  
  // Advanced Features State
  const [activePolls, setActivePolls] = useState<Poll[]>([]);
  const [qaQuestions, setQAQuestions] = useState<QAQuestion[]>([]);
  const [activeScreenShare, setActiveScreenShare] = useState<ScreenShare | null>(null);
  const [showPolls, setShowPolls] = useState(false);
  const [showQA, setShowQA] = useState(false);
  const [showScreenShare, setShowScreenShare] = useState(false);
  
  // Poll Creation State
  const [creatingPoll, setCreatingPoll] = useState(false);
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['', '']);
  const [pollMultipleChoice, setPollMultipleChoice] = useState(false);
  const [pollExpiresIn, setPollExpiresIn] = useState(5); // minutes
  
  // Q&A State
  const [qaSessionActive, setQASessionActive] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');
  const [selectedQuestion, setSelectedQuestion] = useState<QAQuestion | null>(null);
  const [questionAnswer, setQuestionAnswer] = useState('');
  
  // Screen Share State
  const [screenShareType, setScreenShareType] = useState<'screen' | 'window' | 'tab'>('screen');
  const [screenShareTitle, setScreenShareTitle] = useState('');
  
  // Animation values
  const fadeAnim = useSharedValue(1);
  const slideAnim = useSharedValue(0);
  const pollScaleAnim = useSharedValue(0);
  const qaScaleAnim = useSharedValue(0);
  
  // Stream duration timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isStreaming && streamStartTime) {
      interval = setInterval(() => {
        const now = new Date();
        const duration = Math.floor((now.getTime() - streamStartTime.getTime()) / 1000);
        setStreamDuration(duration);
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isStreaming, streamStartTime]);

  // Load advanced features data
  useEffect(() => {
    if (visible && isStreaming) {
      loadPolls();
      loadQAQuestions();
      loadScreenShareStatus();
    }
  }, [visible, isStreaming]);

  // Format stream duration
  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // API Functions
  const loadPolls = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/polls/`);
      if (response.ok) {
        const data = await response.json();
        setActivePolls(data.data || []);
      }
    } catch (error) {
      console.error('Error loading polls:', error);
    }
  };

  const loadQAQuestions = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/qa/questions/`);
      if (response.ok) {
        const data = await response.json();
        setQAQuestions(data.data || []);
      }
    } catch (error) {
      console.error('Error loading Q&A questions:', error);
    }
  };

  const loadScreenShareStatus = async () => {
    // This would check if screen sharing is active
    // For now, we'll simulate it
    setActiveScreenShare(null);
  };

  // Poll Functions
  const createPoll = async () => {
    if (!pollQuestion.trim() || pollOptions.filter(opt => opt.trim()).length < 2) {
      Alert.alert('Error', 'Please provide a question and at least 2 options');
      return;
    }

    setCreatingPoll(true);
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/polls/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: pollQuestion,
          options: pollOptions.filter(opt => opt.trim()),
          is_multiple_choice: pollMultipleChoice,
          expires_in: pollExpiresIn,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setActivePolls(prev => [data.data, ...prev]);
        setPollQuestion('');
        setPollOptions(['', '']);
        setCreatingPoll(false);
        setShowPolls(false);
        Alert.alert('Success', 'Poll created successfully!');
      } else {
        throw new Error('Failed to create poll');
      }
    } catch (error) {
      console.error('Error creating poll:', error);
      Alert.alert('Error', 'Failed to create poll');
    } finally {
      setCreatingPoll(false);
    }
  };

  const votePoll = async (pollId: string, optionIds: string[]) => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/polls/${pollId}/vote/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          option_ids: optionIds,
        }),
      });

      if (response.ok) {
        // Refresh polls to show updated vote counts
        loadPolls();
        Alert.alert('Success', 'Vote recorded!');
      } else {
        throw new Error('Failed to vote');
      }
    } catch (error) {
      console.error('Error voting:', error);
      Alert.alert('Error', 'Failed to vote on poll');
    }
  };

  // Q&A Functions
  const startQASession = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/qa/start/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setQASessionActive(true);
        Alert.alert('Success', 'Q&A session started!');
      } else {
        throw new Error('Failed to start Q&A');
      }
    } catch (error) {
      console.error('Error starting Q&A:', error);
      Alert.alert('Error', 'Failed to start Q&A session');
    }
  };

  const submitQuestion = async () => {
    if (!newQuestion.trim()) {
      Alert.alert('Error', 'Please enter a question');
      return;
    }

    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/qa/questions/submit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: newQuestion,
        }),
      });

      if (response.ok) {
        setNewQuestion('');
        loadQAQuestions();
        Alert.alert('Success', 'Question submitted!');
      } else {
        throw new Error('Failed to submit question');
      }
    } catch (error) {
      console.error('Error submitting question:', error);
      Alert.alert('Error', 'Failed to submit question');
    }
  };

  const answerQuestion = async (questionId: string) => {
    if (!questionAnswer.trim()) {
      Alert.alert('Error', 'Please provide an answer');
      return;
    }

    try {
      // This would be a separate endpoint for answering questions
      // For now, we'll simulate it
      setQAQuestions(prev => prev.map(q => 
        q.id === questionId 
          ? { ...q, status: 'answered' as const, answer: questionAnswer }
          : q
      ));
      setQuestionAnswer('');
      setSelectedQuestion(null);
      Alert.alert('Success', 'Question answered!');
    } catch (error) {
      console.error('Error answering question:', error);
      Alert.alert('Error', 'Failed to answer question');
    }
  };

  // Screen Share Functions
  const startScreenShare = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/screen-share/start/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          share_type: screenShareType,
          title: screenShareTitle,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setActiveScreenShare(data.data);
        setShowScreenShare(false);
        Alert.alert('Success', 'Screen sharing started!');
      } else {
        throw new Error('Failed to start screen sharing');
      }
    } catch (error) {
      console.error('Error starting screen share:', error);
      Alert.alert('Error', 'Failed to start screen sharing');
    }
  };

  const stopScreenShare = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/live-streams/${circleId}/screen-share/stop/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setActiveScreenShare(null);
        Alert.alert('Success', 'Screen sharing stopped!');
      } else {
        throw new Error('Failed to stop screen sharing');
      }
    } catch (error) {
      console.error('Error stopping screen share:', error);
      Alert.alert('Error', 'Failed to stop screen sharing');
    }
  };

  // Animation functions
  const showPollsPanel = () => {
    setShowPolls(true);
    pollScaleAnim.value = withSpring(1);
  };

  const hidePollsPanel = () => {
    pollScaleAnim.value = withTiming(0, {}, () => {
      setShowPolls(false);
    });
  };

  const showQAPanel = () => {
    setShowQA(true);
    qaScaleAnim.value = withSpring(1);
  };

  const hideQAPanel = () => {
    qaScaleAnim.value = withTiming(0, {}, () => {
      setShowQA(false);
    });
  };

  // Render functions
  const renderPoll = ({ item }: { item: Poll }) => (
    <View style={styles.pollCard}>
      <Text style={styles.pollQuestion}>{item.question}</Text>
      <Text style={styles.pollMeta}>
        {item.total_votes} votes • {item.is_multiple_choice ? 'Multiple choice' : 'Single choice'}
      </Text>
      
      {item.options.map((option) => (
        <TouchableOpacity
          key={option.id}
          style={styles.pollOption}
          onPress={() => votePoll(item.id, [option.id])}
        >
          <Text style={styles.pollOptionText}>{option.text}</Text>
          <Text style={styles.pollVoteCount}>{option.votes}</Text>
        </TouchableOpacity>
      ))}
      
      {item.expires_at && (
        <Text style={styles.pollExpiry}>
          Expires: {new Date(item.expires_at).toLocaleTimeString()}
        </Text>
      )}
    </View>
  );

  const renderQuestion = ({ item }: { item: QAQuestion }) => (
    <TouchableOpacity
      style={[
        styles.questionCard,
        item.status === 'answered' && styles.answeredQuestion,
      ]}
      onPress={() => setSelectedQuestion(item)}
    >
      <View style={styles.questionHeader}>
        <Text style={styles.questionUser}>{item.user.username}</Text>
        <View style={styles.questionStatus}>
          <Text style={[
            styles.statusText,
            item.status === 'answered' && styles.answeredStatus,
          ]}>
            {item.status.toUpperCase()}
          </Text>
        </View>
      </View>
      
      <Text style={styles.questionText}>{item.question}</Text>
      
      {item.answer && (
        <View style={styles.answerContainer}>
          <Text style={styles.answerLabel}>Answer:</Text>
          <Text style={styles.answerText}>{item.answer}</Text>
        </View>
      )}
      
      <View style={styles.questionFooter}>
        <Text style={styles.questionTime}>
          {new Date(item.created_at).toLocaleTimeString()}
        </Text>
        <Text style={styles.upvoteCount}>👍 {item.upvotes}</Text>
      </View>
    </TouchableOpacity>
  );

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <StatusBar barStyle="light-content" hidden />
      <View style={styles.container}>
        {/* Main Stream View */}
        <View style={styles.streamContainer}>
          <LinearGradient
            colors={['rgba(0,0,0,0.3)', 'rgba(26,26,26,0.8)']}
            style={styles.streamGradient}
          >
            <Text style={styles.streamTitle}>
              {isHost ? '🎥 Live Stream' : '📺 Watching Live'}
            </Text>
            <Text style={styles.streamSubtitle}>
              {circleName} • {viewerCount} viewers • {formatDuration(streamDuration)}
            </Text>
          </LinearGradient>
        </View>

        {/* Stream Info Header */}
        <View style={styles.streamInfoHeader}>
          <View style={styles.streamInfoLeft}>
            <View style={styles.liveIndicator}>
              <View style={styles.liveDot} />
              <Text style={styles.liveText}>LIVE</Text>
            </View>
            <Text style={styles.streamCategory}>
              {streamCategory === 'market-analysis' ? '📈 Market Analysis' :
               streamCategory === 'portfolio-review' ? '💼 Portfolio Review' :
               streamCategory === 'qa' ? '❓ Q&A Session' : '💬 General Discussion'}
            </Text>
          </View>
          <View style={styles.streamInfoRight}>
            <Text style={styles.viewerCount}>{viewerCount} watching</Text>
          </View>
        </View>

        {/* Advanced Features Toolbar */}
        <View style={styles.featuresToolbar}>
          <TouchableOpacity style={styles.featureButton} onPress={showPollsPanel}>
            <Ionicons name="bar-chart" size={20} color="#ffffff" />
            <Text style={styles.featureButtonText}>Polls</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.featureButton} onPress={showQAPanel}>
            <Ionicons name="help-circle" size={20} color="#ffffff" />
            <Text style={styles.featureButtonText}>Q&A</Text>
          </TouchableOpacity>
          
          {isHost && (
            <TouchableOpacity 
              style={styles.featureButton} 
              onPress={() => setShowScreenShare(true)}
            >
              <Ionicons name="desktop" size={20} color="#ffffff" />
              <Text style={styles.featureButtonText}>Share</Text>
            </TouchableOpacity>
          )}
          
          <TouchableOpacity style={styles.featureButton} onPress={onClose}>
            <Ionicons name="close" size={20} color="#ffffff" />
            <Text style={styles.featureButtonText}>End</Text>
          </TouchableOpacity>
        </View>

        {/* Polls Panel */}
        {showPolls && (
          <Animated.View style={[styles.panel, { transform: [{ scale: pollScaleAnim }] }]}>
            <View style={styles.panelHeader}>
              <Text style={styles.panelTitle}>Live Polls</Text>
              <TouchableOpacity onPress={hidePollsPanel}>
                <Ionicons name="close" size={24} color="#ffffff" />
              </TouchableOpacity>
            </View>
            
            {isHost && (
              <View style={styles.createPollSection}>
                <Text style={styles.sectionTitle}>Create New Poll</Text>
                <TextInput
                  style={styles.pollInput}
                  placeholder="Enter poll question..."
                  placeholderTextColor="#666"
                  value={pollQuestion}
                  onChangeText={setPollQuestion}
                />
                
                {pollOptions.map((option, index) => (
                  <TextInput
                    key={index}
                    style={styles.pollInput}
                    placeholder={`Option ${index + 1}`}
                    placeholderTextColor="#666"
                    value={option}
                    onChangeText={(text) => {
                      const newOptions = [...pollOptions];
                      newOptions[index] = text;
                      setPollOptions(newOptions);
                    }}
                  />
                ))}
                
                <TouchableOpacity
                  style={styles.addOptionButton}
                  onPress={() => setPollOptions([...pollOptions, ''])}
                >
                  <Text style={styles.addOptionText}>+ Add Option</Text>
                </TouchableOpacity>
                
                <View style={styles.pollSettings}>
                  <TouchableOpacity
                    style={[styles.checkbox, pollMultipleChoice && styles.checkboxChecked]}
                    onPress={() => setPollMultipleChoice(!pollMultipleChoice)}
                  >
                    <Text style={styles.checkboxText}>Multiple Choice</Text>
                  </TouchableOpacity>
                </View>
                
                <TouchableOpacity
                  style={styles.createPollButton}
                  onPress={createPoll}
                  disabled={creatingPoll}
                >
                  {creatingPoll ? (
                    <ActivityIndicator color="#ffffff" />
                  ) : (
                    <Text style={styles.createPollButtonText}>Create Poll</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}
            
            <FlatList
              data={activePolls}
              renderItem={renderPoll}
              keyExtractor={(item) => item.id}
              style={styles.pollsList}
              showsVerticalScrollIndicator={false}
            />
          </Animated.View>
        )}

        {/* Q&A Panel */}
        {showQA && (
          <Animated.View style={[styles.panel, { transform: [{ scale: qaScaleAnim }] }]}>
            <View style={styles.panelHeader}>
              <Text style={styles.panelTitle}>Q&A Session</Text>
              <TouchableOpacity onPress={hideQAPanel}>
                <Ionicons name="close" size={24} color="#ffffff" />
              </TouchableOpacity>
            </View>
            
            {isHost && !qaSessionActive && (
              <TouchableOpacity style={styles.startQAButton} onPress={startQASession}>
                <Text style={styles.startQAButtonText}>Start Q&A Session</Text>
              </TouchableOpacity>
            )}
            
            {qaSessionActive && (
              <View style={styles.submitQuestionSection}>
                <TextInput
                  style={styles.questionInput}
                  placeholder="Ask a question..."
                  placeholderTextColor="#666"
                  value={newQuestion}
                  onChangeText={setNewQuestion}
                  multiline
                />
                <TouchableOpacity style={styles.submitQuestionButton} onPress={submitQuestion}>
                  <Text style={styles.submitQuestionButtonText}>Submit</Text>
                </TouchableOpacity>
              </View>
            )}
            
            <FlatList
              data={qaQuestions}
              renderItem={renderQuestion}
              keyExtractor={(item) => item.id}
              style={styles.questionsList}
              showsVerticalScrollIndicator={false}
            />
          </Animated.View>
        )}

        {/* Screen Share Modal */}
        <Modal
          visible={showScreenShare}
          transparent
          animationType="fade"
          onRequestClose={() => setShowScreenShare(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Start Screen Sharing</Text>
              
              <TextInput
                style={styles.modalInput}
                placeholder="Share title (optional)"
                placeholderTextColor="#666"
                value={screenShareTitle}
                onChangeText={setScreenShareTitle}
              />
              
              <View style={styles.shareTypeButtons}>
                <TouchableOpacity
                  style={[styles.shareTypeButton, screenShareType === 'screen' && styles.shareTypeButtonActive]}
                  onPress={() => setScreenShareType('screen')}
                >
                  <Text style={styles.shareTypeButtonText}>Full Screen</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.shareTypeButton, screenShareType === 'window' && styles.shareTypeButtonActive]}
                  onPress={() => setScreenShareType('window')}
                >
                  <Text style={styles.shareTypeButtonText}>Window</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.shareTypeButton, screenShareType === 'tab' && styles.shareTypeButtonActive]}
                  onPress={() => setScreenShareType('tab')}
                >
                  <Text style={styles.shareTypeButtonText}>Browser Tab</Text>
                </TouchableOpacity>
              </View>
              
              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.modalButton}
                  onPress={() => setShowScreenShare(false)}
                >
                  <Text style={styles.modalButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.modalButtonPrimary]}
                  onPress={startScreenShare}
                >
                  <Text style={[styles.modalButtonText, styles.modalButtonPrimaryText]}>Start Sharing</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

        {/* Question Answer Modal */}
        <Modal
          visible={!!selectedQuestion}
          transparent
          animationType="fade"
          onRequestClose={() => setSelectedQuestion(null)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Answer Question</Text>
              
              {selectedQuestion && (
                <>
                  <Text style={styles.questionPreview}>{selectedQuestion.question}</Text>
                  
                  <TextInput
                    style={styles.answerInput}
                    placeholder="Enter your answer..."
                    placeholderTextColor="#666"
                    value={questionAnswer}
                    onChangeText={setQuestionAnswer}
                    multiline
                  />
                  
                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.modalButton}
                      onPress={() => setSelectedQuestion(null)}
                    >
                      <Text style={styles.modalButtonText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.modalButton, styles.modalButtonPrimary]}
                      onPress={() => answerQuestion(selectedQuestion.id)}
                    >
                      <Text style={[styles.modalButtonText, styles.modalButtonPrimaryText]}>Answer</Text>
                    </TouchableOpacity>
                  </View>
                </>
              )}
            </View>
          </View>
        </Modal>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  streamContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  streamGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  streamTitle: {
    fontSize: 24,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  streamSubtitle: {
    fontSize: 16,
    color: '#ffffff',
    opacity: 0.8,
  },
  streamInfoHeader: {
    position: 'absolute',
    top: 60,
    left: 16,
    right: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    zIndex: 10,
  },
  streamInfoLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  streamInfoRight: {
    alignItems: 'flex-end',
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF3B30',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 12,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ffffff',
    marginRight: 4,
  },
  liveText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  streamCategory: {
    color: '#ffffff',
    fontSize: 12,
    opacity: 0.8,
  },
  viewerCount: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  featuresToolbar: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: 25,
    paddingVertical: 12,
    zIndex: 10,
  },
  featureButton: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  featureButtonText: {
    color: '#ffffff',
    fontSize: 12,
    marginTop: 4,
  },
  panel: {
    position: 'absolute',
    top: 120,
    left: 16,
    right: 16,
    bottom: 200,
    backgroundColor: 'rgba(0,0,0,0.9)',
    borderRadius: 16,
    padding: 16,
    zIndex: 20,
  },
  panelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  panelTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  createPollSection: {
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  sectionTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  pollInput: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    marginBottom: 8,
  },
  addOptionButton: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  addOptionText: {
    color: '#ffffff',
    fontSize: 14,
  },
  pollSettings: {
    marginBottom: 12,
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#007AFF',
  },
  checkboxText: {
    color: '#ffffff',
    fontSize: 14,
    marginLeft: 8,
  },
  createPollButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  createPollButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  pollsList: {
    flex: 1,
  },
  pollCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  pollQuestion: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  pollMeta: {
    color: '#ffffff',
    fontSize: 12,
    opacity: 0.7,
    marginBottom: 12,
  },
  pollOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  pollOptionText: {
    color: '#ffffff',
    fontSize: 14,
    flex: 1,
  },
  pollVoteCount: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  pollExpiry: {
    color: '#ffffff',
    fontSize: 12,
    opacity: 0.7,
    marginTop: 8,
  },
  startQAButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  startQAButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  submitQuestionSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  questionInput: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    marginBottom: 8,
    minHeight: 60,
  },
  submitQuestionButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  submitQuestionButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  questionsList: {
    flex: 1,
  },
  questionCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  answeredQuestion: {
    backgroundColor: 'rgba(0,255,0,0.1)',
  },
  questionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  questionUser: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  questionStatus: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '600',
  },
  answeredStatus: {
    color: '#00FF00',
  },
  questionText: {
    color: '#ffffff',
    fontSize: 14,
    marginBottom: 8,
  },
  answerContainer: {
    backgroundColor: 'rgba(0,255,0,0.1)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  answerLabel: {
    color: '#00FF00',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  answerText: {
    color: '#ffffff',
    fontSize: 14,
  },
  questionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  questionTime: {
    color: '#ffffff',
    fontSize: 12,
    opacity: 0.7,
  },
  upvoteCount: {
    color: '#ffffff',
    fontSize: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  modalInput: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    marginBottom: 16,
  },
  shareTypeButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  shareTypeButton: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    flex: 1,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  shareTypeButtonActive: {
    backgroundColor: '#007AFF',
  },
  shareTypeButtonText: {
    color: '#ffffff',
    fontSize: 12,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    flex: 1,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  modalButtonPrimary: {
    backgroundColor: '#007AFF',
  },
  modalButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalButtonPrimaryText: {
    color: '#ffffff',
  },
  questionPreview: {
    color: '#ffffff',
    fontSize: 14,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  answerInput: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    marginBottom: 16,
    minHeight: 80,
  },
});
