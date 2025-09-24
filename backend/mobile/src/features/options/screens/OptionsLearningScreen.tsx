import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

const OptionsLearningScreen = ({ navigation }) => {
  const [currentModule, setCurrentModule] = useState(0);

  const modules = [
    {
      id: 'basics',
      title: 'Options Basics',
      icon: 'book-open',
      color: '#00cc99',
      content: {
        overview: 'Options are financial contracts that give you the right, but not the obligation, to buy or sell an underlying asset at a specific price within a certain time frame.',
        keyConcepts: [
          'Call Options: Right to BUY at strike price',
          'Put Options: Right to SELL at strike price',
          'Strike Price: The price at which you can exercise',
          'Expiration Date: When the option expires',
          'Premium: The cost to buy the option'
        ],
        example: 'If you buy a $150 AAPL call option expiring in 30 days for $5, you can buy 100 shares of AAPL at $150 anytime before expiration.'
      }
    },
    {
      id: 'greeks',
      title: 'Understanding Greeks',
      icon: 'trending-up',
      color: '#007AFF',
      content: {
        overview: 'Greeks measure how sensitive an option\'s price is to various factors. They help you understand risk and potential profit.',
        keyConcepts: [
          'Delta (Δ): Price change per $1 move in underlying',
          'Gamma (Γ): Rate of change of Delta',
          'Theta (Θ): Time decay per day',
          'Vega: Sensitivity to volatility changes',
          'Rho: Sensitivity to interest rate changes'
        ],
        example: 'A Delta of 0.5 means the option price will change by $0.50 for every $1 move in the stock price.'
      }
    },
    {
      id: 'strategies',
      title: 'Basic Strategies',
      icon: 'target',
      color: '#FF6B6B',
      content: {
        overview: 'Learn fundamental options strategies that every trader should know.',
        keyConcepts: [
          'Long Call: Bullish strategy, buy calls',
          'Long Put: Bearish strategy, buy puts',
          'Covered Call: Sell calls against owned stock',
          'Protective Put: Buy puts to hedge stock',
          'Straddle: Buy call and put at same strike'
        ],
        example: 'A covered call strategy involves owning 100 shares of stock and selling a call option, generating income while limiting upside potential.'
      }
    },
    {
      id: 'risks',
      title: 'Risk Management',
      icon: 'shield',
      color: '#FFA500',
      content: {
        overview: 'Options trading involves significant risk. Learn how to manage and mitigate these risks.',
        keyConcepts: [
          'Time Decay: Options lose value as expiration approaches',
          'Volatility Risk: Price swings affect option values',
          'Liquidity Risk: Difficulty buying/selling options',
          'Assignment Risk: Early exercise of options',
          'Position Sizing: Never risk more than you can afford'
        ],
        example: 'Never invest more than 5-10% of your portfolio in options, and always have an exit strategy before entering a trade.'
      }
    }
  ];

  const renderModuleContent = (module) => (
    <View style={styles.moduleContent}>
      <View style={[styles.moduleHeader, { backgroundColor: module.color }]}>
        <Icon name={module.icon} size={32} color="#fff" />
        <Text style={styles.moduleTitle}>{module.title}</Text>
      </View>
      
      <View style={styles.contentSection}>
        <Text style={styles.sectionTitle}>Overview</Text>
        <Text style={styles.sectionText}>{module.content.overview}</Text>
      </View>

      <View style={styles.contentSection}>
        <Text style={styles.sectionTitle}>Key Concepts</Text>
        {module.content.keyConcepts.map((concept, index) => (
          <View key={index} style={styles.conceptItem}>
            <Icon name="check-circle" size={16} color={module.color} />
            <Text style={styles.conceptText}>{concept}</Text>
          </View>
        ))}
      </View>

      <View style={styles.contentSection}>
        <Text style={styles.sectionTitle}>Example</Text>
        <View style={styles.exampleBox}>
          <Text style={styles.exampleText}>{module.content.example}</Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-left" size={24} color="#00cc99" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Options Learning</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Progress Indicator */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill, 
              { width: `${((currentModule + 1) / modules.length) * 100}%` }
            ]} 
          />
        </View>
        <Text style={styles.progressText}>
          Module {currentModule + 1} of {modules.length}
        </Text>
      </View>

      {/* Module Navigation */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.moduleNav}
        contentContainerStyle={styles.moduleNavContent}
      >
        {modules.map((module, index) => (
          <TouchableOpacity
            key={module.id}
            style={[
              styles.moduleTab,
              currentModule === index && styles.activeModuleTab,
              { borderColor: module.color }
            ]}
            onPress={() => setCurrentModule(index)}
          >
            <Icon 
              name={module.icon} 
              size={20} 
              color={currentModule === index ? '#fff' : module.color} 
            />
            <Text style={[
              styles.moduleTabText,
              currentModule === index && styles.activeModuleTabText
            ]}>
              {module.title}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Module Content */}
      <ScrollView style={styles.contentContainer}>
        {renderModuleContent(modules[currentModule])}
      </ScrollView>

      {/* Navigation Buttons */}
      <View style={styles.navigationContainer}>
        <TouchableOpacity
          style={[
            styles.navButton,
            currentModule === 0 && styles.navButtonDisabled
          ]}
          onPress={() => setCurrentModule(Math.max(0, currentModule - 1))}
          disabled={currentModule === 0}
        >
          <Icon name="chevron-left" size={20} color={currentModule === 0 ? '#ccc' : '#00cc99'} />
          <Text style={[
            styles.navButtonText,
            currentModule === 0 && styles.navButtonTextDisabled
          ]}>
            Previous
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.navButton,
            currentModule === modules.length - 1 && styles.navButtonDisabled
          ]}
          onPress={() => setCurrentModule(Math.min(modules.length - 1, currentModule + 1))}
          disabled={currentModule === modules.length - 1}
        >
          <Text style={[
            styles.navButtonText,
            currentModule === modules.length - 1 && styles.navButtonTextDisabled
          ]}>
            Next
          </Text>
          <Icon name="chevron-right" size={20} color={currentModule === modules.length - 1 ? '#ccc' : '#00cc99'} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  placeholder: {
    width: 40,
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e1e5e9',
    borderRadius: 2,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00cc99',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  moduleNav: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  moduleNavContent: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  moduleTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 20,
    borderWidth: 1,
    backgroundColor: '#fff',
  },
  activeModuleTab: {
    backgroundColor: '#00cc99',
  },
  moduleTabText: {
    marginLeft: 6,
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  activeModuleTabText: {
    color: '#fff',
  },
  contentContainer: {
    flex: 1,
    paddingHorizontal: 20,
  },
  moduleContent: {
    paddingVertical: 20,
  },
  moduleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  moduleTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginLeft: 12,
  },
  contentSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  sectionText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#4a4a4a',
  },
  conceptItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  conceptText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#4a4a4a',
    marginLeft: 8,
    flex: 1,
  },
  exampleBox: {
    backgroundColor: '#f0f8ff',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  exampleText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#1a1a1a',
    fontStyle: 'italic',
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e1e5e9',
  },
  navButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00cc99',
  },
  navButtonDisabled: {
    borderColor: '#e1e5e9',
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#00cc99',
    marginHorizontal: 8,
  },
  navButtonTextDisabled: {
    color: '#ccc',
  },
});

export default OptionsLearningScreen;
