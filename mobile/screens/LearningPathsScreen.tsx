import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Modal,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LEARNING_PATHS, LearningModule } from '../data/learningPaths';
import EducationalTooltip from '../components/EducationalTooltip';
import { getTermExplanation } from '../data/financialTerms';

const { width } = Dimensions.get('window');

const LearningPathsScreen: React.FC = () => {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [selectedModule, setSelectedModule] = useState<LearningModule | null>(null);
  const [showModuleModal, setShowModuleModal] = useState(false);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<{[key: string]: number}>({});

  const handlePathSelect = (pathId: string) => {
    // Convert path ID to the correct key format
    const pathKey = pathId.toUpperCase().replace(/-/g, '_');
    setSelectedPath(pathKey);
  };

  const handleModuleSelect = (module: LearningModule) => {
    if (module?.locked) {
      Alert.alert(
        'Module Locked',
        'Complete the previous modules to unlock this one.',
        [{ text: 'OK' }]
      );
      return;
    }
    
    setSelectedModule(module);
    setCurrentSectionIndex(0);
    setUserAnswers({});
    setShowModuleModal(true);
  };

  const handleModuleComplete = () => {
    if (selectedModule) {
      selectedModule.completed = true;
      // In a real app, you'd save this to local storage or backend
      Alert.alert(
        'Module Completed! 🎉',
        'Great job! You\'ve completed this module.',
        [
          {
            text: 'Continue',
            onPress: () => {
              setShowModuleModal(false);
              setSelectedModule(null);
            }
          }
        ]
      );
    }
  };

  const handleQuizAnswer = (questionId: string, answerIndex: number) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answerIndex
    }));
  };

  const renderPathCard = (path: any) => (
    <TouchableOpacity
      key={path?.id}
      style={styles.pathCard}
      onPress={() => handlePathSelect(path?.id || '')}
    >
      <View style={styles.pathHeader}>
        <View style={[styles.pathIcon, { backgroundColor: path?.color || '#007AFF' }]}>
          <Icon name={path?.icon || 'book'} size={24} color="#FFFFFF" />
        </View>
        <View style={styles.pathInfo}>
          <Text style={styles.pathTitle}>{path?.title || 'Untitled Path'}</Text>
          <Text style={styles.pathDescription}>{path?.description || 'No description available'}</Text>
          <View style={styles.pathMeta}>
            <Text style={styles.pathModules}>{path?.totalModules || 0} modules</Text>
            <Text style={styles.pathTime}>{path?.estimatedTime || 'Unknown duration'}</Text>
          </View>
        </View>
        <Icon name="chevron-right" size={20} color="#8E8E93" />
      </View>
      
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill, 
              { 
                width: `${(path?.modules?.filter((m: any) => m.completed).length || 0) / (path?.totalModules || 1) * 100}%`,
                backgroundColor: path?.color || '#007AFF' 
              }
            ]} 
          />
        </View>
        <Text style={styles.progressText}>
          {path?.modules?.filter((m: any) => m.completed).length || 0}/{path?.totalModules || 0} completed
        </Text>
      </View>
    </TouchableOpacity>
  );

  const renderModuleCard = (module: LearningModule) => (
    <TouchableOpacity
      key={module?.id}
      style={[
        styles.moduleCard,
        module?.locked && styles.moduleCardLocked
      ]}
      onPress={() => handleModuleSelect(module)}
    >
      <View style={styles.moduleHeader}>
        <View style={[
          styles.moduleIcon, 
          { backgroundColor: module?.color || '#007AFF' },
          module?.locked && styles.moduleIconLocked
        ]}>
          <Icon 
            name={module?.locked ? 'lock' : (module?.icon || 'book')} 
            size={20} 
            color={module?.locked ? '#8E8E93' : '#FFFFFF'} 
          />
        </View>
        <View style={styles.moduleInfo}>
          <Text style={[
            styles.moduleTitle,
            module?.locked && styles.moduleTitleLocked
          ]}>
            {module?.title || 'Untitled Module'}
          </Text>
          <Text style={styles.moduleDescription}>{module?.description || 'No description available'}</Text>
          <View style={styles.moduleMeta}>
            <Text style={styles.moduleDuration}>{module?.duration || 'Unknown duration'}</Text>
            <View style={[
              styles.difficultyBadge,
              { backgroundColor: getDifficultyColor(module?.difficulty || 'Beginner') }
            ]}>
              <Text style={styles.difficultyText}>{module?.difficulty || 'Beginner'}</Text>
            </View>
          </View>
        </View>
        {module?.completed && (
          <View style={styles.completedBadge}>
            <Icon name="check" size={16} color="#34C759" />
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderSection = (section: any) => {
    switch (section.type) {
      case 'text':
        return (
          <View key={section.id} style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>{section?.title || 'Untitled Section'}</Text>
            <Text style={styles.sectionContent}>{section?.content || 'No content available'}</Text>
          </View>
        );
      
      case 'quiz':
        return (
          <View key={section?.id} style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>{section?.title || 'Untitled Quiz'}</Text>
            {section?.quizData?.map((question: any) => (
              <View key={question?.id} style={styles.quizContainer}>
                <Text style={styles.questionText}>{question?.question || 'No question available'}</Text>
                {question?.options?.map((option: string, index: number) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.optionButton,
                      userAnswers[question?.id] === index && styles.optionButtonSelected
                    ]}
                    onPress={() => handleQuizAnswer(question?.id || '', index)}
                  >
                    <Text style={[
                      styles.optionText,
                      userAnswers[question?.id] === index && styles.optionTextSelected
                    ]}>
                      {option}
                    </Text>
                  </TouchableOpacity>
                ))}
                {userAnswers[question?.id] !== undefined && (
                  <View style={styles.explanationContainer}>
                    <Text style={[
                      styles.explanationText,
                      { color: userAnswers[question?.id] === question?.correctAnswer ? '#34C759' : '#FF3B30' }
                    ]}>
                      {userAnswers[question?.id] === question?.correctAnswer ? '✓ Correct!' : '✗ Incorrect'}
                    </Text>
                    <Text style={styles.explanationDetail}>{question?.explanation || 'No explanation available'}</Text>
                  </View>
                )}
              </View>
            ))}
          </View>
        );
      
      case 'example':
        return (
          <View key={section?.id} style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>{section?.title || 'Untitled Example'}</Text>
            <View style={styles.exampleContainer}>
              <Text style={styles.exampleTitle}>{section?.exampleData?.title || 'Example'}</Text>
              <Text style={styles.exampleScenario}>{section?.exampleData?.scenario || 'No scenario available'}</Text>
              <View style={styles.exampleCalculation}>
                <Text style={styles.calculationLabel}>Calculation:</Text>
                <Text style={styles.calculationText}>{section?.exampleData?.calculation || 'No calculation available'}</Text>
              </View>
              <View style={styles.exampleResult}>
                <Text style={styles.resultLabel}>Result:</Text>
                <Text style={styles.resultText}>{section?.exampleData?.result || 'No result available'}</Text>
              </View>
              <Text style={styles.exampleExplanation}>{section?.exampleData?.explanation || 'No explanation available'}</Text>
            </View>
          </View>
        );
      
      default:
        return null;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return '#34C759';
      case 'Intermediate': return '#FF9500';
      case 'Advanced': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  if (selectedPath) {
    const path = LEARNING_PATHS[selectedPath as keyof typeof LEARNING_PATHS];
    
    if (!path) {
      return (
        <View style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setSelectedPath(null)}
            >
              <Icon name="arrow-left" size={24} color="#007AFF" />
            </TouchableOpacity>
            <View style={styles.headerInfo}>
              <Text style={styles.headerTitle}>Path Not Found</Text>
              <Text style={styles.headerDescription}>The selected learning path could not be found.</Text>
            </View>
          </View>
        </View>
      );
    }
    
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setSelectedPath(null)}
          >
            <Icon name="arrow-left" size={24} color="#007AFF" />
          </TouchableOpacity>
          <View style={styles.headerInfo}>
            <Text style={styles.headerTitle}>{path?.title || 'Learning Path'}</Text>
            <Text style={styles.headerDescription}>{path?.description || 'No description available'}</Text>
          </View>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.pathOverview}>
            <View style={styles.overviewCard}>
              <View style={styles.overviewHeader}>
                <Icon name="info" size={20} color="#007AFF" />
                <Text style={styles.overviewTitle}>Learning Path Overview</Text>
              </View>
              <Text style={styles.overviewText}>
                This learning path will teach you the fundamentals of investing through {path?.totalModules || 0} interactive modules. 
                Complete each module in order to unlock the next one.
              </Text>
              <View style={styles.overviewMeta}>
                <View style={styles.metaItem}>
                  <Icon name="clock" size={16} color="#8E8E93" />
                  <Text style={styles.metaText}>{path?.estimatedTime || 'Unknown duration'}</Text>
                </View>
                <View style={styles.metaItem}>
                  <Icon name="book" size={16} color="#8E8E93" />
                  <Text style={styles.metaText}>{path?.totalModules || 0} modules</Text>
                </View>
              </View>
            </View>
          </View>

          <View style={styles.modulesContainer}>
            <Text style={styles.modulesTitle}>Modules</Text>
            {path.modules?.map(renderModuleCard) || []}
          </View>
        </ScrollView>

        {/* Module Modal */}
        <Modal
          visible={showModuleModal}
          animationType="slide"
          presentationStyle="pageSheet"
        >
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowModuleModal(false)}
              >
                <Icon name="x" size={24} color="#8E8E93" />
              </TouchableOpacity>
              <Text style={styles.modalTitle}>{selectedModule?.title || 'Learning Module'}</Text>
              <TouchableOpacity
                style={styles.modalCompleteButton}
                onPress={handleModuleComplete}
              >
                <Text style={styles.completeButtonText}>Complete</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
              {selectedModule?.content?.sections?.map(renderSection) || []}
            </ScrollView>
          </View>
        </Modal>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>Learning Paths</Text>
          <Text style={styles.headerDescription}>
            Master investing with structured, beginner-friendly courses
          </Text>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.pathsContainer}>
          {Object.values(LEARNING_PATHS).map(renderPathCard)}
        </View>
      </ScrollView>
    </View>
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
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  headerDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
  content: {
    flex: 1,
  },
  pathsContainer: {
    padding: 20,
    gap: 16,
  },
  pathCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  pathHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  pathIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  pathInfo: {
    flex: 1,
  },
  pathTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  pathDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 8,
  },
  pathMeta: {
    flexDirection: 'row',
    gap: 16,
  },
  pathModules: {
    fontSize: 12,
    color: '#8E8E93',
  },
  pathTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  progressContainer: {
    marginTop: 8,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
    marginBottom: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  pathOverview: {
    padding: 20,
  },
  overviewCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  overviewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  overviewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginLeft: 8,
  },
  overviewText: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 16,
  },
  overviewMeta: {
    flexDirection: 'row',
    gap: 20,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  modulesContainer: {
    paddingHorizontal: 20,
  },
  modulesTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  moduleCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  moduleCardLocked: {
    opacity: 0.6,
  },
  moduleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  moduleIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  moduleIconLocked: {
    backgroundColor: '#E5E5EA',
  },
  moduleInfo: {
    flex: 1,
  },
  moduleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  moduleTitleLocked: {
    color: '#8E8E93',
  },
  moduleDescription: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
    marginBottom: 8,
  },
  moduleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  moduleDuration: {
    fontSize: 12,
    color: '#8E8E93',
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  completedBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E8F5E8',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalCloseButton: {
    padding: 8,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 20,
  },
  modalCompleteButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  completeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  sectionContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  sectionContent: {
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 22,
  },
  quizContainer: {
    marginBottom: 20,
  },
  questionText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  optionButton: {
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  optionButtonSelected: {
    backgroundColor: '#007AFF',
  },
  optionText: {
    fontSize: 14,
    color: '#1C1C1E',
  },
  optionTextSelected: {
    color: '#FFFFFF',
  },
  explanationContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  explanationText: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  explanationDetail: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  exampleContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 16,
  },
  exampleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  exampleScenario: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 12,
  },
  exampleCalculation: {
    backgroundColor: '#FFFFFF',
    borderRadius: 6,
    padding: 12,
    marginBottom: 8,
  },
  calculationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 4,
  },
  calculationText: {
    fontSize: 14,
    color: '#1C1C1E',
    fontFamily: 'monospace',
  },
  exampleResult: {
    backgroundColor: '#E8F5E8',
    borderRadius: 6,
    padding: 12,
    marginBottom: 12,
  },
  resultLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#34C759',
    marginBottom: 4,
  },
  resultText: {
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
  exampleExplanation: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
});

export default LearningPathsScreen;
