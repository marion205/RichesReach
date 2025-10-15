import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

const SBLOCLearningScreen = ({ navigation }) => {
  const [currentModule, setCurrentModule] = useState(0);

  const modules = [
    {
      id: 'basics',
      title: 'SBLOC Basics',
      icon: 'credit-card',
      color: '#8B5CF6',
      content: {
        overview: 'A Securities-Based Line of Credit (SBLOC) allows you to borrow money using your investment portfolio as collateral, without selling your investments.',
        keyConcepts: [
          'Collateral: Your investment portfolio secures the loan',
          'No Tax Impact: Borrowing doesn\'t trigger capital gains',
          'Flexible Access: Draw funds as needed, pay back anytime',
          'Interest Only: Pay only interest, not principal',
          'Margin Requirements: Maintain minimum portfolio value'
        ],
        example: 'If you have $500,000 in stocks, you might qualify for a $250,000 SBLOC at 4% interest, giving you cash without selling shares.'
      }
    },
    {
      id: 'benefits',
      title: 'Benefits & Uses',
      icon: 'trending-up',
      color: '#10B981',
      content: {
        overview: 'SBLOCs offer unique advantages for sophisticated investors who want to leverage their portfolio without selling assets.',
        keyConcepts: [
          'Tax Efficiency: Avoid capital gains taxes on sales',
          'Investment Continuity: Keep your portfolio intact',
          'Quick Access: Funds available within days',
          'Flexible Terms: Use for any purpose',
          'Lower Rates: Often better than personal loans'
        ],
        example: 'Use SBLOC funds for real estate down payments, business investments, or major purchases while keeping your stock portfolio growing.'
      }
    },
    {
      id: 'risks',
      title: 'Risks & Considerations',
      icon: 'alert-triangle',
      color: '#F59E0B',
      content: {
        overview: 'SBLOCs carry significant risks, especially during market downturns. Understanding these risks is crucial.',
        keyConcepts: [
          'Market Risk: Portfolio value can decline rapidly',
          'Margin Calls: Forced to add cash or sell investments',
          'Interest Rate Risk: Variable rates can increase',
          'Liquidation Risk: Broker can sell your securities',
          'Over-leverage: Don\'t borrow more than you can handle'
        ],
        example: 'If your $500K portfolio drops to $300K and you\'ve borrowed $250K, you may face a margin call requiring immediate payment.'
      }
    },
    {
      id: 'qualification',
      title: 'Qualification & Setup',
      icon: 'user-check',
      color: '#3B82F6',
      content: {
        overview: 'SBLOCs have specific qualification requirements and setup processes that vary by broker.',
        keyConcepts: [
          'Minimum Portfolio: Usually $100K-$250K required',
          'Credit Check: Good credit history needed',
          'Diversification: Portfolio must meet broker requirements',
          'Documentation: Income verification and financial statements',
          'Ongoing Monitoring: Regular portfolio value checks'
        ],
        example: 'Most brokers require a minimum portfolio value of $250K, good credit score (680+), and diversified holdings across multiple sectors.'
      }
    },
    {
      id: 'strategies',
      title: 'Smart Strategies',
      icon: 'target',
      color: '#EF4444',
      content: {
        overview: 'Learn how to use SBLOCs strategically while managing risk effectively.',
        keyConcepts: [
          'Conservative Borrowing: Never borrow more than 30-40%',
          'Diversification: Maintain well-diversified portfolio',
          'Emergency Fund: Keep cash reserves for margin calls',
          'Regular Monitoring: Track portfolio value daily',
          'Exit Strategy: Plan for market downturns'
        ],
        example: 'A smart strategy: Borrow only 25% of portfolio value, maintain 6 months of interest payments in cash, and have a plan to reduce borrowing during market stress.'
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

      {/* Risk Warning for SBLOC */}
      {module.id === 'risks' && (
        <View style={styles.warningBox}>
          <Icon name="alert-triangle" size={20} color="#F59E0B" />
          <Text style={styles.warningText}>
            SBLOCs are complex financial products that can result in significant losses. 
            Only experienced investors should consider them.
          </Text>
        </View>
      )}
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
          <Icon name="arrow-left" size={24} color="#8B5CF6" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>SBLOC Learning</Text>
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
          <Icon name="chevron-left" size={20} color={currentModule === 0 ? '#ccc' : '#8B5CF6'} />
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
          <Icon name="chevron-right" size={20} color={currentModule === modules.length - 1 ? '#ccc' : '#8B5CF6'} />
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
    backgroundColor: '#8B5CF6',
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
    backgroundColor: '#8B5CF6',
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
    borderLeftColor: '#3B82F6',
  },
  exampleText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#1a1a1a',
    fontStyle: 'italic',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF3C7',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
    marginTop: 16,
  },
  warningText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#92400E',
    marginLeft: 8,
    flex: 1,
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
    borderColor: '#8B5CF6',
  },
  navButtonDisabled: {
    borderColor: '#e1e5e9',
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8B5CF6',
    marginHorizontal: 8,
  },
  navButtonTextDisabled: {
    color: '#ccc',
  },
});

export default SBLOCLearningScreen;
