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

const PortfolioLearningScreen = ({ navigation }) => {
  const [currentModule, setCurrentModule] = useState(0);

  const modules = [
    {
      id: 'basics',
      title: 'Portfolio Basics',
      icon: 'pie-chart',
      color: '#007AFF',
      content: {
        overview: 'A well-structured portfolio is the foundation of successful investing. Learn how to build and maintain a diversified investment portfolio that aligns with your financial goals.',
        keyConcepts: [
          'Asset Allocation: Mix of stocks, bonds, and other assets',
          'Diversification: Spread risk across different investments',
          'Risk Tolerance: Your comfort level with market volatility',
          'Time Horizon: How long you plan to invest',
          'Rebalancing: Adjusting your portfolio over time'
        ],
        example: 'A balanced portfolio might include 60% stocks, 30% bonds, and 10% alternatives, adjusted based on your age and risk tolerance.'
      }
    },
    {
      id: 'diversification',
      title: 'Diversification Strategies',
      icon: 'layers',
      color: '#34C759',
      content: {
        overview: 'Diversification is your best defense against market volatility. Learn how to spread your investments across different asset classes, sectors, and geographic regions.',
        keyConcepts: [
          'Asset Class Diversification: Stocks, bonds, real estate, commodities',
          'Sector Diversification: Technology, healthcare, finance, energy',
          'Geographic Diversification: Domestic and international markets',
          'Market Cap Diversification: Large, mid, and small-cap stocks',
          'Style Diversification: Growth, value, and blend investments'
        ],
        example: 'Instead of putting all your money in tech stocks, diversify across healthcare, finance, consumer goods, and international markets to reduce risk.'
      }
    },
    {
      id: 'rebalancing',
      title: 'Portfolio Rebalancing',
      icon: 'refresh-cw',
      color: '#FF9500',
      content: {
        overview: 'Regular rebalancing keeps your portfolio aligned with your investment strategy and risk tolerance as markets fluctuate.',
        keyConcepts: [
          'Target Allocation: Your ideal asset mix percentages',
          'Drift: How your portfolio changes over time',
          'Rebalancing Triggers: Time-based or threshold-based',
          'Tax Considerations: Minimizing capital gains taxes',
          'Market Timing: Avoiding emotional decisions'
        ],
        example: 'If your target is 60% stocks and 40% bonds, but stocks grow to 70%, rebalance by selling some stocks and buying bonds to return to your target.'
      }
    },
    {
      id: 'risk-management',
      title: 'Risk Management',
      icon: 'shield',
      color: '#FF3B30',
      content: {
        overview: 'Understanding and managing investment risk is crucial for long-term success. Learn how to assess and mitigate different types of investment risk.',
        keyConcepts: [
          'Market Risk: Overall market volatility',
          'Company Risk: Individual stock performance',
          'Sector Risk: Industry-specific challenges',
          'Inflation Risk: Purchasing power erosion',
          'Liquidity Risk: Difficulty selling investments'
        ],
        example: 'To manage risk, never put more than 5-10% of your portfolio in any single stock, and maintain an emergency fund equal to 3-6 months of expenses.'
      }
    },
    {
      id: 'monitoring',
      title: 'Performance Monitoring',
      icon: 'bar-chart-2',
      color: '#AF52DE',
      content: {
        overview: 'Regular monitoring helps you track progress toward your goals and make informed decisions about your portfolio adjustments.',
        keyConcepts: [
          'Performance Metrics: Returns, volatility, Sharpe ratio',
          'Benchmark Comparison: How you compare to market indices',
          'Goal Tracking: Progress toward financial objectives',
          'Cost Analysis: Fees and expenses impact',
          'Regular Reviews: Monthly, quarterly, or annual assessments'
        ],
        example: 'Review your portfolio quarterly, comparing your returns to appropriate benchmarks like the S&P 500 for stocks or Bloomberg Bond Index for bonds.'
      }
    },
    {
      id: 'advanced',
      title: 'Advanced Strategies',
      icon: 'target',
      color: '#5856D6',
      content: {
        overview: 'Advanced portfolio management techniques can help optimize returns and manage risk for sophisticated investors.',
        keyConcepts: [
          'Factor Investing: Targeting specific risk factors',
          'Alternative Investments: REITs, commodities, hedge funds',
          'Tax-Loss Harvesting: Offset gains with losses',
          'Dollar-Cost Averaging: Regular, consistent investing',
          'Asset Location: Tax-efficient account placement'
        ],
        example: 'Use tax-loss harvesting by selling losing investments to offset gains, then reinvesting in similar but not identical securities to maintain your strategy.'
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

      {/* Pro Tip for Advanced Module */}
      {module.id === 'advanced' && (
        <View style={styles.tipBox}>
          <Icon name="lightbulb" size={20} color="#FFD700" />
          <Text style={styles.tipText}>
            Pro Tip: Advanced strategies work best when you have a solid foundation in basic portfolio management principles.
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
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Portfolio Management</Text>
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
          <Icon name="chevron-left" size={20} color={currentModule === 0 ? '#ccc' : '#007AFF'} />
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
          <Icon name="chevron-right" size={20} color={currentModule === modules.length - 1 ? '#ccc' : '#007AFF'} />
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
    backgroundColor: '#007AFF',
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
    backgroundColor: '#007AFF',
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
  tipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF8DC',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#FFD700',
    marginTop: 16,
  },
  tipText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#B8860B',
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
    borderColor: '#007AFF',
  },
  navButtonDisabled: {
    borderColor: '#e1e5e9',
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginHorizontal: 8,
  },
  navButtonTextDisabled: {
    color: '#ccc',
  },
});

export default PortfolioLearningScreen;
