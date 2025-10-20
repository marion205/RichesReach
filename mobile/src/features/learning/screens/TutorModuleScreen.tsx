import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { tutorModule, DynamicContentResponse } from '../../../services/aiClient';

export default function TutorModuleScreen() {
  const [userId] = useState('demo-user');
  const [topic, setTopic] = useState('Risk Management');
  const [data, setData] = useState<DynamicContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [currentSection, setCurrentSection] = useState(0);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [calculatorInputs, setCalculatorInputs] = useState<Record<string, string>>({});
  const [decisionTreePath, setDecisionTreePath] = useState<Record<string, string>>({});
  const [exerciseAnswers, setExerciseAnswers] = useState<Record<string, string>>({});

  // Create a personalized user learning profile
  const createUserProfile = () => {
    return {
      learning_style: 'visual', // visual, auditory, kinesthetic, reading
      current_level: 'intermediate', // beginner, intermediate, advanced
      interests: ['options trading', 'risk management', 'portfolio optimization'],
      weak_areas: ['technical analysis', 'options strategies'],
      strong_areas: ['fundamental analysis', 'market research'],
      learning_pace: 'moderate', // slow, moderate, fast
      time_available: 30, // minutes per session
      investment_experience: '2-5 years',
      risk_tolerance: 'medium',
      preferred_assets: ['stocks', 'options', 'ETFs'],
      current_portfolio_size: '$10,000 - $50,000'
    };
  };

  const load = async () => {
    setLoading(true); setErr(null);
    setExpandedSections(new Set());
    setQuizAnswers({});
    setQuizSubmitted(false);
    setCurrentSection(0);
    setCalculatorInputs({});
    setDecisionTreePath({});
    setExerciseAnswers({});
    
    try {
      // Create user profile if not exists
      if (!userProfile) {
        const profile = createUserProfile();
        setUserProfile(profile);
      }
      
      const res = await tutorModule({ 
        user_id: userId, 
        topic, 
        difficulty: 'beginner',
        user_profile: userProfile || createUserProfile()
      });
      setData(res);
    } catch (e: any) {
      setErr(e?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  const selectQuizAnswer = (questionId: string, answer: string) => {
    if (quizSubmitted) return;
    setQuizAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const submitQuiz = () => {
    setQuizSubmitted(true);
    const totalQuestions = data?.quiz?.questions?.length || 0;
    const correctAnswers = Object.values(quizAnswers).filter(answer => answer).length;
    const score = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;
    
    Alert.alert(
      'Quiz Complete!',
      `You scored ${correctAnswers}/${totalQuestions} (${score.toFixed(0)}%)`,
      [{ text: 'OK' }]
    );
  };

  const nextSection = () => {
    const totalSections = data?.sections?.length || 0;
    if (currentSection < totalSections - 1) {
      setCurrentSection(currentSection + 1);
    }
  };

  const prevSection = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1);
    }
  };

  // Interactive element handlers
  const updateCalculatorInput = (sectionId: string, variable: string, value: string) => {
    setCalculatorInputs(prev => ({
      ...prev,
      [`${sectionId}_${variable}`]: value
    }));
  };

  const calculateResult = (section: any) => {
    const calc = section.interactive_elements?.calculator;
    if (!calc) return 'N/A';
    
    try {
      // Simple calculation logic - in real app, you'd use a proper math parser
      const formula = calc.formula.toLowerCase();
      const variables = calc.variables || [];
      
      let result = formula;
      variables.forEach((varName: string) => {
        const value = calculatorInputs[`${section.id || 'calc'}_${varName}`] || '0';
        result = result.replace(new RegExp(varName.toLowerCase(), 'g'), value);
      });
      
      // Basic math evaluation (in production, use a proper math library)
      return eval(result).toFixed(2);
    } catch (e) {
      return 'Invalid input';
    }
  };

  const selectDecisionTreeOption = (sectionId: string, choice: string) => {
    setDecisionTreePath(prev => ({
      ...prev,
      [sectionId]: choice
    }));
  };

  const updateExerciseAnswer = (sectionId: string, answer: string) => {
    setExerciseAnswers(prev => ({
      ...prev,
      [sectionId]: answer
    }));
  };

  const renderInteractiveElement = (section: any) => {
    const interactive = section.interactive_elements;
    if (!interactive) return null;

    if (interactive.calculator) {
      const calc = interactive.calculator;
      return (
        <View style={styles.calculatorContainer}>
          <Text style={styles.calculatorTitle}>🧮 {calc.description}</Text>
          <Text style={styles.calculatorFormula}>Formula: {calc.formula}</Text>
          
          {calc.variables?.map((variable: string) => (
            <View key={variable} style={styles.calculatorInputRow}>
              <Text style={styles.calculatorLabel}>{variable}:</Text>
              <TextInput
                style={styles.calculatorInput}
                value={calculatorInputs[`${section.id || 'calc'}_${variable}`] || ''}
                onChangeText={(value) => updateCalculatorInput(section.id || 'calc', variable, value)}
                placeholder="Enter value"
                keyboardType="numeric"
              />
            </View>
          ))}
          
          <View style={styles.calculatorResult}>
            <Text style={styles.calculatorResultLabel}>Result:</Text>
            <Text style={styles.calculatorResultValue}>{calculateResult(section)}</Text>
          </View>
        </View>
      );
    }

    if (interactive.decision_tree) {
      const tree = interactive.decision_tree;
      const selectedChoice = decisionTreePath[section.id || 'tree'];
      
      return (
        <View style={styles.decisionTreeContainer}>
          <Text style={styles.decisionTreeTitle}>🌳 {tree.question}</Text>
          
          {tree.options?.map((option: any, index: number) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.decisionTreeOption,
                selectedChoice === option.choice && styles.decisionTreeOptionSelected
              ]}
              onPress={() => selectDecisionTreeOption(section.id || 'tree', option.choice)}
            >
              <Text style={[
                styles.decisionTreeOptionText,
                selectedChoice === option.choice && styles.decisionTreeOptionTextSelected
              ]}>
                {option.choice}
              </Text>
            </TouchableOpacity>
          ))}
          
          {selectedChoice && (
            <View style={styles.decisionTreeOutcome}>
              <Text style={styles.decisionTreeOutcomeText}>
                {tree.options?.find((opt: any) => opt.choice === selectedChoice)?.outcome}
              </Text>
            </View>
          )}
        </View>
      );
    }

    if (interactive.exercise) {
      const exercise = interactive.exercise;
      return (
        <View style={styles.exerciseContainer}>
          <Text style={styles.exerciseTitle}>💪 {exercise.instructions}</Text>
          
          {exercise.steps?.map((step: string, index: number) => (
            <Text key={index} style={styles.exerciseStep}>
              {index + 1}. {step}
            </Text>
          ))}
          
          <TextInput
            style={styles.exerciseInput}
            value={exerciseAnswers[section.id || 'exercise'] || ''}
            onChangeText={(value) => updateExerciseAnswer(section.id || 'exercise', value)}
            placeholder="Your answer here..."
            multiline
          />
          
          {exercise.hints?.length > 0 && (
            <View style={styles.exerciseHints}>
              <Text style={styles.exerciseHintsTitle}>💡 Hints:</Text>
              {exercise.hints.map((hint: string, index: number) => (
                <Text key={index} style={styles.exerciseHint}>• {hint}</Text>
              ))}
            </View>
          )}
        </View>
      );
    }

    if (interactive.challenge) {
      const challenge = interactive.challenge;
      return (
        <View style={styles.challengeContainer}>
          <Text style={styles.challengeTitle}>🎯 Challenge: {challenge.scenario}</Text>
          
          <View style={styles.challengeGoals}>
            <Text style={styles.challengeGoalsTitle}>Goals:</Text>
            {challenge.goals?.map((goal: string, index: number) => (
              <Text key={index} style={styles.challengeGoal}>• {goal}</Text>
            ))}
          </View>
          
          <View style={styles.challengeConstraints}>
            <Text style={styles.challengeConstraintsTitle}>Constraints:</Text>
            {challenge.constraints?.map((constraint: string, index: number) => (
              <Text key={index} style={styles.challengeConstraint}>• {constraint}</Text>
            ))}
          </View>
          
          <View style={styles.challengeSuccess}>
            <Text style={styles.challengeSuccessTitle}>Success Criteria:</Text>
            {challenge.success_criteria?.map((criteria: string, index: number) => (
              <Text key={index} style={styles.challengeCriterion}>✓ {criteria}</Text>
            ))}
          </View>
        </View>
      );
    }

    return null;
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{data?.title || `Module: ${topic}`}</Text>
      
      {/* Topic Input */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>Topic:</Text>
        <View style={styles.inputRow}>
          <TextInput 
            style={styles.input} 
            value={topic} 
            onChangeText={setTopic} 
            placeholder="Enter topic..." 
            placeholderTextColor="#9ca3af"
          />
          <TouchableOpacity onPress={load} style={styles.button} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" size="small" /> : <Text style={styles.buttonText}>Generate</Text>}
          </TouchableOpacity>
        </View>
      </View>

      {err ? <Text style={styles.err}>{err}</Text> : null}

      {data && (
        <>
          {/* Module Info */}
          <View style={styles.infoCard}>
            <View style={styles.meta}>
              {data.difficulty ? <Text style={styles.metaText}>📊 {data.difficulty}</Text> : null}
              {data.estimated_time ? <Text style={styles.metaText}>⏱️ {data.estimated_time} min</Text> : null}
              {data.sections?.length ? <Text style={styles.metaText}>📚 {data.sections.length} sections</Text> : null}
            </View>
            {data.description && <Text style={styles.description}>{data.description}</Text>}
          </View>

          {/* Progress Indicator */}
          {data.sections?.length > 1 && (
            <View style={styles.progressContainer}>
              <Text style={styles.progressText}>Section {currentSection + 1} of {data.sections.length}</Text>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${((currentSection + 1) / data.sections.length) * 100}%` }]} />
              </View>
            </View>
          )}

          {/* Sections */}
          {(data.sections || []).map((s: any, idx: number) => (
            <View key={idx} style={[styles.section, currentSection === idx && styles.activeSection]}>
              <TouchableOpacity 
                style={styles.sectionHeader} 
                onPress={() => toggleSection(idx)}
                activeOpacity={0.7}
              >
                <View style={styles.sectionHeaderLeft}>
                  <Text style={styles.sectionNumber}>{idx + 1}</Text>
                  <Text style={styles.sectionTitle}>{s.title}</Text>
                </View>
                <Text style={styles.expandIcon}>
                  {expandedSections.has(idx) ? '▼' : '▶'}
                </Text>
              </TouchableOpacity>
              
              {expandedSections.has(idx) && (
                <View style={styles.sectionContent}>
                  <Text style={styles.sectionText}>{s.content}</Text>
                  
                  {s.key_points && s.key_points.length > 0 && (
                    <View style={styles.keyPoints}>
                      <Text style={styles.keyPointsTitle}>Key Points:</Text>
                      {s.key_points.map((point: string, i: number) => (
                        <Text key={i} style={styles.keyPoint}>• {point}</Text>
                      ))}
                    </View>
                  )}
                  
                  {s.examples && s.examples.length > 0 && (
                    <View style={styles.examples}>
                      <Text style={styles.examplesTitle}>Examples:</Text>
                      {s.examples.map((example: string, i: number) => (
                        <Text key={i} style={styles.example}>• {example}</Text>
                      ))}
                    </View>
                  )}

                  {/* Interactive Elements */}
                  {renderInteractiveElement(s)}
                </View>
              )}
            </View>
          ))}

          {/* Navigation Buttons */}
          {data.sections?.length > 1 && (
            <View style={styles.navigationContainer}>
              <TouchableOpacity 
                style={[styles.navButton, currentSection === 0 && styles.navButtonDisabled]} 
                onPress={prevSection}
                disabled={currentSection === 0}
              >
                <Text style={[styles.navButtonText, currentSection === 0 && styles.navButtonTextDisabled]}>← Previous</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.navButton, currentSection === (data.sections?.length || 0) - 1 && styles.navButtonDisabled]} 
                onPress={nextSection}
                disabled={currentSection === (data.sections?.length || 0) - 1}
              >
                <Text style={[styles.navButtonText, currentSection === (data.sections?.length || 0) - 1 && styles.navButtonTextDisabled]}>Next →</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Interactive Quiz */}
          {data.quiz?.questions?.length ? (
            <View style={styles.quizSection}>
              <Text style={styles.quizTitle}>📝 Knowledge Check</Text>
              <Text style={styles.quizSubtitle}>Test your understanding</Text>
              
              {data.quiz.questions.map((q: any, qIdx: number) => (
                <View key={q.id} style={styles.questionCard}>
                  <Text style={styles.questionText}>{qIdx + 1}. {q.question}</Text>
                  
                  {q.options && q.options.map((option: string, oIdx: number) => (
                    <TouchableOpacity
                      key={oIdx}
                      style={[
                        styles.optionButton,
                        quizAnswers[q.id] === option && styles.optionSelected,
                        quizSubmitted && q.correct_answer === option && styles.optionCorrect,
                        quizSubmitted && quizAnswers[q.id] === option && q.correct_answer !== option && styles.optionIncorrect
                      ]}
                      onPress={() => selectQuizAnswer(q.id, option)}
                      disabled={quizSubmitted}
                    >
                      <Text style={[
                        styles.optionText,
                        quizAnswers[q.id] === option && styles.optionTextSelected,
                        quizSubmitted && q.correct_answer === option && styles.optionTextCorrect,
                        quizSubmitted && quizAnswers[q.id] === option && q.correct_answer !== option && styles.optionTextIncorrect
                      ]}>
                        {String.fromCharCode(65 + oIdx)}. {option}
                      </Text>
                    </TouchableOpacity>
                  ))}
                  
                  {quizSubmitted && q.explanation && (
                    <Text style={styles.explanation}>{q.explanation}</Text>
                  )}
                </View>
              ))}
              
              <TouchableOpacity 
                style={[styles.submitButton, quizSubmitted && styles.submitButtonDisabled]} 
                onPress={submitQuiz}
                disabled={quizSubmitted}
              >
                <Text style={styles.submitButtonText}>
                  {quizSubmitted ? 'Quiz Completed!' : 'Submit Quiz'}
                </Text>
              </TouchableOpacity>
            </View>
          ) : null}

          {/* Practical Application */}
          {data.practical_application && (
            <View style={styles.practicalApplicationSection}>
              <Text style={styles.practicalApplicationTitle}>🎯 Apply What You've Learned</Text>
              
              <View style={styles.practicalApplicationCard}>
                <Text style={styles.practicalApplicationScenario}>
                  <Text style={styles.practicalApplicationLabel}>Real-world scenario:</Text>{'\n'}
                  {data.practical_application.real_world_scenario}
                </Text>
                
                <Text style={styles.practicalApplicationSituation}>
                  <Text style={styles.practicalApplicationLabel}>Your situation:</Text>{'\n'}
                  {data.practical_application.your_situation}
                </Text>
                
                <View style={styles.practicalApplicationActionPlan}>
                  <Text style={styles.practicalApplicationActionPlanTitle}>Action Plan:</Text>
                  {data.practical_application.action_plan?.map((action: string, index: number) => (
                    <Text key={index} style={styles.practicalApplicationAction}>
                      {index + 1}. {action}
                    </Text>
                  ))}
                </View>
                
                <View style={styles.practicalApplicationNextSteps}>
                  <Text style={styles.practicalApplicationNextStepsTitle}>Next Steps:</Text>
                  {data.practical_application.next_steps?.map((step: string, index: number) => (
                    <Text key={index} style={styles.practicalApplicationStep}>
                      ✓ {step}
                    </Text>
                  ))}
                </View>
                
                {data.practical_application.resources?.length > 0 && (
                  <View style={styles.practicalApplicationResources}>
                    <Text style={styles.practicalApplicationResourcesTitle}>Resources:</Text>
                    {data.practical_application.resources.map((resource: string, index: number) => (
                      <Text key={index} style={styles.practicalApplicationResource}>
                        📚 {resource}
                      </Text>
                    ))}
                  </View>
                )}
              </View>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { color: '#1f2937', fontSize: 20, marginBottom: 16, fontWeight: '700', textAlign: 'center' },
  
  // Input Section
  inputContainer: { marginBottom: 16 },
  inputLabel: { color: '#374151', fontSize: 14, fontWeight: '600', marginBottom: 8 },
  inputRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  input: { 
    flex: 1, 
    backgroundColor: '#ffffff', 
    color: '#1f2937', 
    padding: 12, 
    borderRadius: 8, 
    borderWidth: 1, 
    borderColor: '#d1d5db',
    fontSize: 16
  },
  button: { backgroundColor: '#a855f7', padding: 12, borderRadius: 8, alignItems: 'center', minWidth: 100 },
  buttonText: { color: '#ffffff', fontWeight: '700', fontSize: 14 },
  err: { color: '#ef4444', marginBottom: 8, textAlign: 'center' },
  
  // Module Info
  infoCard: { backgroundColor: '#ffffff', padding: 16, borderRadius: 12, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2 },
  meta: { flexDirection: 'row', gap: 16, marginBottom: 12, flexWrap: 'wrap' },
  metaText: { color: '#6b7280', fontSize: 14, fontWeight: '500' },
  description: { color: '#374151', fontSize: 16, lineHeight: 24 },
  
  // Progress
  progressContainer: { marginBottom: 16 },
  progressText: { color: '#6b7280', fontSize: 14, marginBottom: 8, textAlign: 'center' },
  progressBar: { height: 6, backgroundColor: '#e5e7eb', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#a855f7', borderRadius: 3 },
  
  // Sections
  section: { backgroundColor: '#ffffff', borderRadius: 12, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1, overflow: 'hidden' },
  activeSection: { borderWidth: 2, borderColor: '#a855f7' },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, backgroundColor: '#f9fafb' },
  sectionHeaderLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  sectionNumber: { 
    backgroundColor: '#a855f7', 
    color: '#ffffff', 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    textAlign: 'center', 
    lineHeight: 24, 
    fontSize: 12, 
    fontWeight: '700', 
    marginRight: 12 
  },
  sectionTitle: { color: '#1f2937', fontWeight: '700', fontSize: 16, flex: 1 },
  expandIcon: { color: '#6b7280', fontSize: 16, fontWeight: 'bold' },
  sectionContent: { padding: 16 },
  sectionText: { color: '#374151', lineHeight: 24, fontSize: 15, marginBottom: 12 },
  
  // Key Points & Examples
  keyPoints: { backgroundColor: '#f0f9ff', padding: 12, borderRadius: 8, marginBottom: 12 },
  keyPointsTitle: { color: '#1e40af', fontWeight: '700', marginBottom: 8, fontSize: 14 },
  keyPoint: { color: '#1e40af', lineHeight: 20, marginBottom: 4, fontSize: 14 },
  examples: { backgroundColor: '#f0fdf4', padding: 12, borderRadius: 8, marginBottom: 12 },
  examplesTitle: { color: '#166534', fontWeight: '700', marginBottom: 8, fontSize: 14 },
  example: { color: '#166534', lineHeight: 20, marginBottom: 4, fontSize: 14 },
  
  // Navigation
  navigationContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20, gap: 12 },
  navButton: { backgroundColor: '#3b82f6', padding: 12, borderRadius: 8, flex: 1, alignItems: 'center' },
  navButtonDisabled: { backgroundColor: '#e5e7eb' },
  navButtonText: { color: '#ffffff', fontWeight: '700', fontSize: 14 },
  navButtonTextDisabled: { color: '#9ca3af' },
  
  // Quiz
  quizSection: { backgroundColor: '#ffffff', padding: 16, borderRadius: 12, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2 },
  quizTitle: { color: '#1f2937', fontSize: 18, fontWeight: '700', marginBottom: 4, textAlign: 'center' },
  quizSubtitle: { color: '#6b7280', fontSize: 14, marginBottom: 16, textAlign: 'center' },
  questionCard: { marginBottom: 16, padding: 16, backgroundColor: '#f9fafb', borderRadius: 8 },
  questionText: { color: '#1f2937', fontSize: 16, fontWeight: '600', marginBottom: 12, lineHeight: 22 },
  optionButton: { 
    backgroundColor: '#ffffff', 
    padding: 12, 
    borderRadius: 8, 
    marginBottom: 8, 
    borderWidth: 1, 
    borderColor: '#d1d5db' 
  },
  optionSelected: { backgroundColor: '#dbeafe', borderColor: '#3b82f6' },
  optionCorrect: { backgroundColor: '#dcfce7', borderColor: '#22c55e' },
  optionIncorrect: { backgroundColor: '#fef2f2', borderColor: '#ef4444' },
  optionText: { color: '#374151', fontSize: 14, lineHeight: 20 },
  optionTextSelected: { color: '#1e40af', fontWeight: '600' },
  optionTextCorrect: { color: '#166534', fontWeight: '600' },
  optionTextIncorrect: { color: '#dc2626', fontWeight: '600' },
  explanation: { 
    marginTop: 12, 
    padding: 12, 
    backgroundColor: '#f0f9ff', 
    borderRadius: 6, 
    color: '#1e40af', 
    fontSize: 14, 
    lineHeight: 20 
  },
  submitButton: { backgroundColor: '#22c55e', padding: 16, borderRadius: 8, alignItems: 'center', marginTop: 8 },
  submitButtonDisabled: { backgroundColor: '#e5e7eb' },
  submitButtonText: { color: '#ffffff', fontWeight: '700', fontSize: 16 },
  
  // Interactive Elements
  calculatorContainer: { backgroundColor: '#f0f9ff', padding: 16, borderRadius: 8, marginTop: 12, borderWidth: 1, borderColor: '#bfdbfe' },
  calculatorTitle: { color: '#1e40af', fontSize: 16, fontWeight: '700', marginBottom: 8 },
  calculatorFormula: { color: '#1e40af', fontSize: 14, fontFamily: 'Menlo', marginBottom: 12, backgroundColor: '#ffffff', padding: 8, borderRadius: 4 },
  calculatorInputRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  calculatorLabel: { color: '#1e40af', fontSize: 14, fontWeight: '600', width: 80 },
  calculatorInput: { flex: 1, backgroundColor: '#ffffff', color: '#1f2937', padding: 8, borderRadius: 4, borderWidth: 1, borderColor: '#bfdbfe' },
  calculatorResult: { backgroundColor: '#ffffff', padding: 12, borderRadius: 6, marginTop: 8, borderWidth: 2, borderColor: '#22c55e' },
  calculatorResultLabel: { color: '#166534', fontSize: 14, fontWeight: '600' },
  calculatorResultValue: { color: '#166534', fontSize: 18, fontWeight: '700', marginTop: 4 },
  
  decisionTreeContainer: { backgroundColor: '#f0fdf4', padding: 16, borderRadius: 8, marginTop: 12, borderWidth: 1, borderColor: '#bbf7d0' },
  decisionTreeTitle: { color: '#166534', fontSize: 16, fontWeight: '700', marginBottom: 12 },
  decisionTreeOption: { backgroundColor: '#ffffff', padding: 12, borderRadius: 6, marginBottom: 8, borderWidth: 1, borderColor: '#d1d5db' },
  decisionTreeOptionSelected: { backgroundColor: '#dcfce7', borderColor: '#22c55e' },
  decisionTreeOptionText: { color: '#374151', fontSize: 14 },
  decisionTreeOptionTextSelected: { color: '#166534', fontWeight: '600' },
  decisionTreeOutcome: { backgroundColor: '#ffffff', padding: 12, borderRadius: 6, marginTop: 8, borderWidth: 1, borderColor: '#22c55e' },
  decisionTreeOutcomeText: { color: '#166534', fontSize: 14, lineHeight: 20 },
  
  exerciseContainer: { backgroundColor: '#fef3c7', padding: 16, borderRadius: 8, marginTop: 12, borderWidth: 1, borderColor: '#fbbf24' },
  exerciseTitle: { color: '#92400e', fontSize: 16, fontWeight: '700', marginBottom: 12 },
  exerciseStep: { color: '#92400e', fontSize: 14, marginBottom: 6, lineHeight: 20 },
  exerciseInput: { backgroundColor: '#ffffff', color: '#1f2937', padding: 12, borderRadius: 6, marginTop: 8, borderWidth: 1, borderColor: '#fbbf24', minHeight: 80 },
  exerciseHints: { backgroundColor: '#ffffff', padding: 12, borderRadius: 6, marginTop: 8 },
  exerciseHintsTitle: { color: '#92400e', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  exerciseHint: { color: '#92400e', fontSize: 13, marginBottom: 4 },
  
  challengeContainer: { backgroundColor: '#fce7f3', padding: 16, borderRadius: 8, marginTop: 12, borderWidth: 1, borderColor: '#f9a8d4' },
  challengeTitle: { color: '#be185d', fontSize: 16, fontWeight: '700', marginBottom: 12 },
  challengeGoals: { marginBottom: 12 },
  challengeGoalsTitle: { color: '#be185d', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  challengeGoal: { color: '#be185d', fontSize: 13, marginBottom: 4 },
  challengeConstraints: { marginBottom: 12 },
  challengeConstraintsTitle: { color: '#be185d', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  challengeConstraint: { color: '#be185d', fontSize: 13, marginBottom: 4 },
  challengeSuccess: { marginBottom: 8 },
  challengeSuccessTitle: { color: '#be185d', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  challengeCriterion: { color: '#be185d', fontSize: 13, marginBottom: 4 },
  
  // Practical Application
  practicalApplicationSection: { marginTop: 20 },
  practicalApplicationTitle: { color: '#1f2937', fontSize: 18, fontWeight: '700', marginBottom: 16, textAlign: 'center' },
  practicalApplicationCard: { backgroundColor: '#ffffff', padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 2 },
  practicalApplicationScenario: { color: '#374151', fontSize: 14, lineHeight: 20, marginBottom: 12 },
  practicalApplicationSituation: { color: '#374151', fontSize: 14, lineHeight: 20, marginBottom: 16 },
  practicalApplicationLabel: { fontWeight: '700', color: '#1f2937' },
  practicalApplicationActionPlan: { marginBottom: 16 },
  practicalApplicationActionPlanTitle: { color: '#1f2937', fontSize: 16, fontWeight: '700', marginBottom: 8 },
  practicalApplicationAction: { color: '#374151', fontSize: 14, marginBottom: 6, lineHeight: 20 },
  practicalApplicationNextSteps: { marginBottom: 16 },
  practicalApplicationNextStepsTitle: { color: '#1f2937', fontSize: 16, fontWeight: '700', marginBottom: 8 },
  practicalApplicationStep: { color: '#374151', fontSize: 14, marginBottom: 6, lineHeight: 20 },
  practicalApplicationResources: { marginBottom: 8 },
  practicalApplicationResourcesTitle: { color: '#1f2937', fontSize: 16, fontWeight: '700', marginBottom: 8 },
  practicalApplicationResource: { color: '#374151', fontSize: 14, marginBottom: 6, lineHeight: 20 },
});
