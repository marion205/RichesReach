import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { tutorQuiz, tutorRegimeAdaptiveQuiz, QuizResponse } from '../../../services/aiClient';

// Map regime types to simple labels
function getRegimeLabel(regime: string): string {
  const normalized = regime?.toLowerCase() || '';
  if (normalized.includes('bull') || normalized.includes('calm')) return 'Calm';
  if (normalized.includes('bear') || normalized.includes('storm')) return 'Storm';
  if (normalized.includes('sideways') || normalized.includes('choppy') || normalized.includes('volatile')) return 'Choppy';
  return 'Choppy'; // Default
}

export default function TutorQuizScreen() {
  const [userId] = useState('demo-user');
  const [topic, setTopic] = useState('Options Basics');
  const [quiz, setQuiz] = useState<QuizResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string,string>>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [isRegimeAdaptive, setIsRegimeAdaptive] = useState(false);

  const loadQuiz = async () => {
    setLoading(true);
    setSubmitted(false);
    setAnswers({});
    try {
      let res: QuizResponse;
      
      if (isRegimeAdaptive) {
        // Generate regime-adaptive quiz
        res = await tutorRegimeAdaptiveQuiz({ 
          user_id: userId, 
          difficulty: 'beginner', 
          num_questions: 4 
        });
      } else {
        // Generate regular topic-based quiz
        res = await tutorQuiz({ user_id: userId, topic, difficulty: 'beginner', num_questions: 4 });
      }
      
      // Fallback: If quiz is incomplete or has no options, use mock quiz
      if (!res.questions || res.questions.length === 0 || 
          res.questions.some(q => !q.options || q.options.length === 0)) {
        const mockQuiz = {
          topic: topic,
          difficulty: 'beginner',
          questions: [
            {
              id: 'q1',
              question: 'What is an option in financial markets?',
              question_type: 'multiple_choice',
              options: [
                'A contract that gives the right to buy or sell an asset at a specific price',
                'A type of stock that pays dividends',
                'A government bond with fixed interest',
                'A cryptocurrency token'
              ],
              correct_answer: 'A contract that gives the right to buy or sell an asset at a specific price',
              explanation: 'An option is a financial contract that gives the holder the right (but not the obligation) to buy or sell an underlying asset at a predetermined price within a specific time period.',
              hints: ['Think about rights vs obligations', 'Consider predetermined prices']
            },
            {
              id: 'q2',
              question: 'What is the difference between a call option and a put option?',
              question_type: 'multiple_choice',
              options: [
                'Call gives right to buy, Put gives right to sell',
                'Call gives right to sell, Put gives right to buy',
                'Both give the same rights',
                'Call is for stocks, Put is for bonds'
              ],
              correct_answer: 'Call gives right to buy, Put gives right to sell',
              explanation: 'A call option gives the holder the right to buy the underlying asset, while a put option gives the holder the right to sell the underlying asset.',
              hints: ['Call = Buy', 'Put = Sell']
            },
            {
              id: 'q3',
              question: 'What happens to an option when it expires?',
              question_type: 'multiple_choice',
              options: [
                'It becomes worthless if not exercised',
                'It automatically converts to stock',
                'It gets renewed for another period',
                'It pays out dividends'
              ],
              correct_answer: 'It becomes worthless if not exercised',
              explanation: 'When an option expires, if it is not exercised (used), it becomes worthless and expires. The holder loses the premium paid for the option.',
              hints: ['Think about time limits', 'Consider what happens if you don\'t use it']
            },
            {
              id: 'q4',
              question: 'What is the strike price of an option?',
              question_type: 'multiple_choice',
              options: [
                'The predetermined price at which the option can be exercised',
                'The current market price of the underlying asset',
                'The price you pay to buy the option',
                'The price you receive when selling the option'
              ],
              correct_answer: 'The predetermined price at which the option can be exercised',
              explanation: 'The strike price (or exercise price) is the predetermined price at which the holder of an option can buy (call) or sell (put) the underlying asset.',
              hints: ['Think predetermined', 'Consider exercise price']
            }
          ],
          generated_at: new Date().toISOString()
        };
        setQuiz(mockQuiz);
      } else {
        setQuiz(res);
      }
    } finally {
      setLoading(false);
    }
  };

  const correctCount = quiz?.questions.reduce((acc, q) => acc + (answers[q.id] && answers[q.id] === q.correct_answer ? 1 : 0), 0) || 0;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>
        {isRegimeAdaptive ? 'Regime-Adaptive Quiz' : `Quiz: ${topic}`}
      </Text>
      
      {/* Regime-Adaptive Toggle */}
      <View style={styles.toggleContainer}>
        <TouchableOpacity 
          style={[styles.toggle, isRegimeAdaptive && styles.toggleActive]}
          onPress={() => setIsRegimeAdaptive(!isRegimeAdaptive)}
        >
          <Text style={[styles.toggleText, isRegimeAdaptive && styles.toggleTextActive]}>
            {isRegimeAdaptive ? '🎯 Regime-Adaptive' : '📚 Topic-Based'}
          </Text>
        </TouchableOpacity>
        {isRegimeAdaptive && (
          <Text style={styles.toggleDescription}>
            Quiz adapts to current market conditions using AI regime detection
          </Text>
        )}
      </View>

      <TouchableOpacity testID="start-options-quiz-button" onPress={loadQuiz} style={styles.button} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Load Quiz</Text>}
      </TouchableOpacity>

      {/* Regime Context Display */}
      {quiz?.regime_context && (
        <View style={styles.regimeContext}>
          <Text style={styles.regimeTitle}>📊 Today's Conditions</Text>
          <Text style={styles.regimeName}>{getRegimeLabel(quiz.regime_context.current_regime)}</Text>
          <Text style={styles.regimeDescription}>{quiz.regime_context.regime_description}</Text>
          <Text style={styles.regimeConfidence}>
            Confidence: {(quiz.regime_context.regime_confidence * 100).toFixed(1)}%
          </Text>
          
          <View style={styles.regimeStrategies}>
            <Text style={styles.regimeSubtitle}>🎯 Relevant Strategies:</Text>
            {quiz.regime_context.relevant_strategies.map((strategy, idx) => (
              <Text key={idx} style={styles.regimeItem}>• {strategy}</Text>
            ))}
          </View>
          
          <View style={styles.regimeMistakes}>
            <Text style={styles.regimeSubtitle}>⚠️ Common Mistakes:</Text>
            {quiz.regime_context.common_mistakes.map((mistake, idx) => (
              <Text key={idx} style={styles.regimeItem}>• {mistake}</Text>
            ))}
          </View>
        </View>
      )}

      {quiz?.questions?.map((q) => (
        <View key={q.id} style={styles.card}>
          <Text style={styles.qtext}>{q.question}</Text>
          {(q.options || []).map((opt) => (
            <TouchableOpacity
              key={opt}
              testID={opt.toLowerCase().includes('call') ? 'call-option-answer' : opt.toLowerCase().includes('put') ? 'put-option-answer' : `option-${opt.substring(0, 10).replace(/\s/g, '-').toLowerCase()}`}
              style={[styles.opt, answers[q.id]===opt && styles.optActive]}
              onPress={() => !submitted && setAnswers({ ...answers, [q.id]: opt })}
            >
              <Text style={styles.optText}>{opt}</Text>
            </TouchableOpacity>
          ))}
          {submitted && (
            <Text style={answers[q.id]===q.correct_answer? styles.correct: styles.incorrect}>
              {answers[q.id]===q.correct_answer? 'Correct ✅' : `Incorrect ❌  (Answer: ${q.correct_answer || 'n/a'})`}
            </Text>
          )}
          {submitted && q.explanation ? <Text style={styles.explain}>{q.explanation}</Text> : null}
        </View>
      ))}

      {quiz?.questions?.length ? (
        <View style={{ marginBottom: 24 }}>
          <TouchableOpacity testID="show-results-button" onPress={() => setSubmitted(true)} style={[styles.button, { backgroundColor: '#3b82f6' }]}>
            <Text style={styles.buttonText}>{submitted ? 'Regrade' : 'Submit Answers'}</Text>
          </TouchableOpacity>
          {submitted ? <Text style={styles.score}>Score: {correctCount}/{quiz.questions.length}</Text> : null}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { color: '#1f2937', fontSize: 18, marginBottom: 12, fontWeight: '600' },
  
  // Toggle styles
  toggleContainer: { marginBottom: 16 },
  toggle: { 
    backgroundColor: '#e5e7eb', 
    padding: 12, 
    borderRadius: 12, 
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent'
  },
  toggleActive: { 
    backgroundColor: '#dbeafe', 
    borderColor: '#3b82f6' 
  },
  toggleText: { 
    color: '#6b7280', 
    fontWeight: '600',
    fontSize: 16
  },
  toggleTextActive: { 
    color: '#1d4ed8' 
  },
  toggleDescription: { 
    color: '#6b7280', 
    fontSize: 12, 
    marginTop: 4, 
    textAlign: 'center',
    fontStyle: 'italic'
  },
  
  // Regime context styles
  regimeContext: {
    backgroundColor: '#f0f9ff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6'
  },
  regimeTitle: { 
    color: '#1e40af', 
    fontSize: 16, 
    fontWeight: '700', 
    marginBottom: 8 
  },
  regimeName: { 
    color: '#1d4ed8', 
    fontSize: 18, 
    fontWeight: '800', 
    marginBottom: 4 
  },
  regimeDescription: { 
    color: '#374151', 
    fontSize: 14, 
    marginBottom: 8 
  },
  regimeConfidence: { 
    color: '#059669', 
    fontSize: 12, 
    fontWeight: '600', 
    marginBottom: 12 
  },
  regimeStrategies: { 
    marginBottom: 12 
  },
  regimeMistakes: { 
    marginBottom: 0 
  },
  regimeSubtitle: { 
    color: '#1f2937', 
    fontSize: 14, 
    fontWeight: '600', 
    marginBottom: 4 
  },
  regimeItem: { 
    color: '#4b5563', 
    fontSize: 13, 
    marginLeft: 8, 
    marginBottom: 2 
  },
  
  button: { backgroundColor: '#22c55e', padding: 10, borderRadius: 10, alignItems: 'center', marginBottom: 12 },
  buttonText: { color: '#ffffff', fontWeight: '700' },
  card: { backgroundColor: '#ffffff', padding: 12, borderRadius: 10, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  qtext: { color: '#1f2937', marginBottom: 8, fontWeight: '600' },
  opt: { backgroundColor: '#f3f4f6', padding: 10, borderRadius: 8, marginVertical: 4 },
  optActive: { backgroundColor: '#dbeafe' },
  optText: { color: '#374151' },
  correct: { color: '#22c55e', marginTop: 8 },
  incorrect: { color: '#ef4444', marginTop: 8 },
  explain: { color: '#6b7280', marginTop: 6 },
  score: { color: '#374151', marginTop: 8, fontWeight: '600' },
});
