import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation, useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

// GraphQL Queries
const GET_USER_PROFILE = gql`
  query GetUserProfile {
    me {
      id
      name
      email
      incomeProfile {
        incomeBracket
        age
        investmentGoals
        riskTolerance
        investmentHorizon
      }
    }
  }
`;

const GET_AI_RECOMMENDATIONS = gql`
  query GetAIRecommendations($userId: ID!) {
    aiPortfolioRecommendations(userId: $userId) {
      id
      riskProfile
      portfolioAllocation
      recommendedStocks {
        symbol
        companyName
        allocation
        reasoning
        riskLevel
        expectedReturn
      }
      expectedPortfolioReturn
      riskAssessment
      createdAt
    }
  }
`;

const CREATE_INCOME_PROFILE = gql`
  mutation CreateIncomeProfile(
    $incomeBracket: String!
    $age: Int!
    $investmentGoals: [String!]!
    $riskTolerance: String!
    $investmentHorizon: String!
  ) {
    createIncomeProfile(
      incomeBracket: $incomeBracket
      age: $age
      investmentGoals: $investmentGoals
      riskTolerance: $riskTolerance
      investmentHorizon: $investmentHorizon
    ) {
      success
      message
      incomeProfile {
        id
        incomeBracket
        age
        investmentGoals
        riskTolerance
        investmentHorizon
      }
    }
  }
`;

const GENERATE_AI_RECOMMENDATIONS = gql`
  mutation GenerateAIRecommendations {
    generateAiRecommendations {
      success
      message
      recommendations {
        id
        riskProfile
        portfolioAllocation
        recommendedStocks {
          symbol
          companyName
          allocation
          reasoning
          riskLevel
          expectedReturn
        }
        expectedPortfolioReturn
        riskAssessment
      }
    }
  }
`;

// Types
interface IncomeProfile {
  id: string;
  incomeBracket: string;
  age: number;
  investmentGoals: string[];
  riskTolerance: string;
  investmentHorizon: string;
}

interface StockRecommendation {
  symbol: string;
  companyName: string;
  allocation: number;
  reasoning: string;
  riskLevel: string;
  expectedReturn: string;
}

interface PortfolioRecommendation {
  id: string;
  riskProfile: string;
  portfolioAllocation: {
    stocks: number;
    bonds: number;
    etfs: number;
    cash: number;
  };
  recommendedStocks: StockRecommendation[];
  expectedPortfolioReturn: string;
  riskAssessment: string;
  createdAt: string;
}

interface AIPortfolioScreenProps {
  navigateTo?: (screen: string) => void;
}

export default function AIPortfolioScreen({ navigateTo }: AIPortfolioScreenProps) {
  // Debug logging
  // AIPortfolioScreen props received
  
  // Provide default navigateTo function if not passed
  const safeNavigateTo = navigateTo || (() => {});
  
  // State
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);
  
  // Form state
  const [incomeBracket, setIncomeBracket] = useState('');
  const [age, setAge] = useState('');
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [riskTolerance, setRiskTolerance] = useState('');
  const [investmentHorizon, setInvestmentHorizon] = useState('');

  // Queries
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(GET_USER_PROFILE);
  const { data: recommendationsData, loading: recommendationsLoading, refetch: refetchRecommendations } = useQuery(
    GET_AI_RECOMMENDATIONS,
    { 
      variables: { userId: userData?.me?.id },
      skip: !userData?.me?.id 
    }
  );

  // Mutations
  const [createIncomeProfile] = useMutation(CREATE_INCOME_PROFILE);
  const [generateAIRecommendations] = useMutation(GENERATE_AI_RECOMMENDATIONS);

  // Constants
  const incomeBrackets = [
    'Under $30,000',
    '$30,000 - $50,000',
    '$50,000 - $75,000',
    '$75,000 - $100,000',
    '$100,000 - $150,000',
    'Over $150,000'
  ];

  const investmentGoals = [
    'Retirement Savings',
    'Buy a Home',
    'Emergency Fund',
    'Wealth Building',
    'Passive Income',
    'Tax Benefits',
    'College Fund',
    'Travel Fund'
  ];

  const riskToleranceOptions = [
    'Conservative',
    'Moderate',
    'Aggressive'
  ];

  const investmentHorizonOptions = [
    '1-3 years',
    '3-5 years',
    '5-10 years',
    '10+ years'
  ];

  // Handlers
  const handleGoalToggle = (goal: string) => {
    if (selectedGoals.includes(goal)) {
      setSelectedGoals(selectedGoals.filter(g => g !== goal));
    } else {
      setSelectedGoals([...selectedGoals, goal]);
    }
  };

  const handleCreateProfile = async () => {
    if (!incomeBracket || !age || selectedGoals.length === 0 || !riskTolerance || !investmentHorizon) {
      Alert.alert('Missing Information', 'Please fill in all fields.');
      return;
    }

    // Debug logging to see what values are being sent
    console.log('📝 Creating profile with values:', {
      incomeBracket,
      age: parseInt(age),
      investmentGoals: selectedGoals,
      riskTolerance,
      investmentHorizon
    });

    try {
      const result = await createIncomeProfile({
        variables: {
          incomeBracket,
          age: parseInt(age),
          investmentGoals: selectedGoals,
          riskTolerance,
          investmentHorizon
        }
      });

      if (result.data?.createIncomeProfile?.success) {
        console.log('SUCCESS: Profile created successfully with risk level:', riskTolerance);
        Alert.alert('Success', 'Income profile created successfully!');
        setShowProfileForm(false);
        
        // Force refresh user data first
        await refetchUser();
        console.log('🔄 User data refreshed, waiting for update...');
        
        // Small delay to ensure user data is updated
        setTimeout(async () => {
          console.log('🔄 Auto-updating recommendations due to profile change...');
          console.log('🔄 New risk level for recommendations:', riskTolerance);
          await handleGenerateRecommendations();
        }, 1000);
      } else {
        Alert.alert('Error', result.data?.createIncomeProfile?.message || 'Failed to create profile');
      }
    } catch (error) {
      console.error('ERROR: Error creating profile:', error);
      Alert.alert('Error', 'Failed to create profile. Please try again.');
    }
  };

  const handleGenerateRecommendations = async () => {
    setIsGeneratingRecommendations(true);
    try {
      console.log(' Generating AI recommendations...');
      console.log(' Current user profile:', userData?.me?.incomeProfile);
      console.log(' Current risk tolerance:', userData?.me?.incomeProfile?.riskTolerance);
      
      const result = await generateAIRecommendations();
      
      if (result.data?.generateAiRecommendations?.success) {
        console.log('SUCCESS: Recommendations generated successfully');
        refetchRecommendations();
      } else {
        console.log('ERROR: Failed to generate recommendations:', result.data?.generateAiRecommendations?.message);
        Alert.alert('Error', result.data?.generateAiRecommendations?.message || 'Failed to generate recommendations');
      }
    } catch (error) {
      console.error('ERROR: Error generating recommendations:', error);
      Alert.alert('Error', 'Failed to generate recommendations. Please try again.');
    } finally {
      setIsGeneratingRecommendations(false);
    }
  };

  // Auto-update recommendations when profile form is closed (indicating profile was updated)
  useEffect(() => {
    if (!showProfileForm && userData?.me?.incomeProfile && recommendationsData) {
      // Small delay to ensure profile data is fully updated
      const timer = setTimeout(() => {
        console.log('🔄 Auto-updating recommendations after profile edit...');
        handleGenerateRecommendations();
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [showProfileForm, userData?.me?.incomeProfile]);

  const renderIncomeProfileForm = () => (
    <View style={styles.formContainer}>
      <Text style={styles.formTitle}>Create Your Financial Profile</Text>
      
      {/* Income Bracket */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Annual Income</Text>
        <View style={styles.optionsGrid}>
          {incomeBrackets.map((bracket) => (
            <TouchableOpacity
              key={bracket}
              style={[
                styles.optionButton,
                incomeBracket === bracket && styles.selectedOption
              ]}
              onPress={() => setIncomeBracket(bracket)}
            >
              <Text style={[
                styles.optionText,
                incomeBracket === bracket && styles.selectedOptionText
              ]}>
                {bracket}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Age */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Age</Text>
        <TextInput
          style={styles.input}
          value={age}
          onChangeText={setAge}
          placeholder="Enter your age"
          keyboardType="numeric"
        />
      </View>

      {/* Investment Goals */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Investment Goals (Select all that apply)</Text>
        <View style={styles.optionsGrid}>
          {investmentGoals.map((goal) => (
            <TouchableOpacity
              key={goal}
              style={[
                styles.optionButton,
                selectedGoals.includes(goal) && styles.selectedOption
              ]}
              onPress={() => handleGoalToggle(goal)}
            >
              <Text style={[
                styles.optionText,
                selectedGoals.includes(goal) && styles.selectedOptionText
              ]}>
                {goal}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Risk Tolerance */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Risk Tolerance</Text>
        <View style={styles.optionsGrid}>
          {riskToleranceOptions.map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.optionButton,
                riskTolerance === option && styles.selectedOption
              ]}
              onPress={() => setRiskTolerance(option)}
            >
              <Text style={[
                styles.optionText,
                riskTolerance === option && styles.selectedOptionText
              ]}>
                {option}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Investment Horizon */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Investment Time Horizon</Text>
        <View style={styles.optionsGrid}>
          {investmentHorizonOptions.map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.optionButton,
                investmentHorizon === option && styles.selectedOption
              ]}
              onPress={() => setInvestmentHorizon(option)}
            >
              <Text style={[
                styles.optionText,
                investmentHorizon === option && styles.selectedOptionText
              ]}>
                {option}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.formActions}>
        <TouchableOpacity style={styles.cancelButton} onPress={() => setShowProfileForm(false)}>
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.saveButton} onPress={handleCreateProfile}>
          <Text style={styles.saveButtonText}>Save Profile</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderRecommendations = () => {
    const recommendations = recommendationsData?.aiPortfolioRecommendations;
    
    if (!recommendations || recommendations.length === 0) {
      return (
        <View style={styles.emptyState}>
          <Icon name="cpu" size={64} color="#9CA3AF" />
          <Text style={styles.emptyTitle}>No AI Recommendations Yet</Text>
          <Text style={styles.emptySubtitle}>
            Generate personalized quantitative AI portfolio recommendations based on your financial profile
          </Text>
          <TouchableOpacity 
            style={styles.generateButton} 
            onPress={handleGenerateRecommendations}
            disabled={isGeneratingRecommendations}
          >
            <Text style={styles.generateButtonText}>
              {isGeneratingRecommendations ? 'Generating...' : 'Generate Quantitative AI Recommendations'}
            </Text>
          </TouchableOpacity>
        </View>
      );
    }

    const latestRecommendation = recommendations[0];
    
    return (
      <View style={styles.recommendationsContainer}>
        <View style={styles.recommendationHeader}>
          <Text style={styles.recommendationTitle}>Quantitative AI Portfolio Analysis</Text>
        </View>

        {/* Quantitative Portfolio Summary */}
        <View style={styles.portfolioSummary}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Risk Profile</Text>
            <Text style={styles.summaryValue}>{latestRecommendation.riskProfile}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Expected Return</Text>
            <Text style={styles.summaryValue}>{latestRecommendation.expectedPortfolioReturn}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Analysis Type</Text>
            <Text style={styles.summaryValue}>Quantitative</Text>
          </View>
        </View>

        {/* Advanced Risk Metrics */}
        <View style={styles.riskMetricsSection}>
          <Text style={styles.sectionTitle}>Risk Analysis</Text>
          <View style={styles.riskMetricsGrid}>
            <View style={styles.riskMetricItem}>
              <Icon name="trending-up" size={20} color="#EF4444" />
              <Text style={styles.riskMetricLabel}>Volatility</Text>
              <Text style={styles.riskMetricValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '8.2%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '12.8%' : '18.5%'}
              </Text>
              <TouchableOpacity 
                style={styles.infoButtonBottomRight}
                onPress={() => Alert.alert(
                  'Volatility',
                  'How much your portfolio value fluctuates over time. Lower volatility means more stable, predictable returns. Your conservative profile shows 8.2% volatility, which is excellent for stability.'
                )}
              >
                <Icon name="info" size={14} color="#6B7280" />
              </TouchableOpacity>
            </View>
            <View style={styles.riskMetricItem}>
              <Icon name="alert-circle" size={20} color="#F59E0B" />
              <Text style={styles.riskMetricLabel}>Max Drawdown</Text>
              <Text style={styles.riskMetricValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '15.0%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '32.0%' : 'N/A'}
              </Text>
              <TouchableOpacity 
                style={styles.infoButtonBottomRight}
                onPress={() => Alert.alert(
                  'Max Drawdown',
                  'The worst-case decline your portfolio could experience from its peak value. Lower max drawdown means less risk of significant losses. Your conservative profile shows 15.0% max drawdown, which is very safe compared to moderate (32.0%) or aggressive portfolios.'
                )}
              >
                <Icon name="info" size={14} color="#6B7280" />
              </TouchableOpacity>
            </View>
            <View style={styles.riskMetricItem}>
              <Icon name="lock" size={20} color="#10B981" />
              <Text style={styles.riskMetricLabel}>Risk Level</Text>
              <Text style={styles.riskMetricValue}>
                {userData?.me?.incomeProfile?.riskTolerance || 'N/A'}
              </Text>
              <TouchableOpacity 
                style={styles.infoButtonBottomRight}
                onPress={() => Alert.alert(
                  'Risk Level',
                  'Your investment risk tolerance determines how your portfolio is balanced. Conservative means lower risk with more bonds and stable returns. Moderate balances stocks and bonds. Aggressive focuses on stocks for higher potential returns but more risk.'
                )}
              >
                <Icon name="info" size={14} color="#6B7280" />
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Portfolio Allocation */}
        <View style={styles.allocationSection}>
          <Text style={styles.sectionTitle}>Asset Allocation</Text>
          <View style={styles.allocationGrid}>
            <View style={styles.allocationItem}>
              <Text style={styles.allocationLabel}>Stocks</Text>
              <Text style={styles.allocationValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '30%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '60%' : '80%'}
              </Text>
            </View>
            <View style={styles.allocationItem}>
              <Text style={styles.allocationLabel}>Bonds</Text>
              <Text style={styles.allocationValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '50%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '30%' : '15%'}
              </Text>
            </View>
            <View style={styles.allocationItem}>
              <Text style={styles.allocationLabel}>ETFs</Text>
              <Text style={styles.allocationValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '15%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '8%' : '3%'}
              </Text>
            </View>
            <View style={styles.allocationItem}>
              <Text style={styles.allocationLabel}>Cash</Text>
              <Text style={styles.allocationValue}>
                {userData?.me?.incomeProfile?.riskTolerance === 'Conservative' ? '5%' : 
                 userData?.me?.incomeProfile?.riskTolerance === 'Moderate' ? '2%' : '2%'}
              </Text>
            </View>
          </View>
        </View>

        {/* Sector Weights (if available) */}
        {latestRecommendation.portfolioAllocation.sectorWeights && (
          <View style={styles.sectorSection}>
            <Text style={styles.sectionTitle}>Sector Allocation</Text>
            <View style={styles.sectorGrid}>
              {Object.entries(latestRecommendation.portfolioAllocation.sectorWeights).map(([sector, weight]) => (
                <View key={sector} style={styles.sectorItem}>
                  <Text style={styles.sectorLabel}>{sector.charAt(0).toUpperCase() + sector.slice(1)}</Text>
                  <Text style={styles.sectorValue}>{String(weight)}%</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Quantitative Stock Recommendations */}
        <View style={styles.stocksSection}>
          <Text style={styles.sectionTitle}>Quantitative Stock Picks</Text>
          {latestRecommendation.recommendedStocks.map((stock: any, index: number) => (
            <View key={index} style={styles.stockCard}>
              <View style={styles.stockHeader}>
                <View style={styles.stockInfo}>
                  <Text style={styles.stockSymbol}>{stock.symbol}</Text>
                  <Text style={styles.companyName}>{stock.companyName}</Text>
                </View>
                <View style={styles.stockMetrics}>
                  <Text style={styles.allocationText}>{stock.allocation}%</Text>
                  <Text style={styles.expectedReturn}>{stock.expectedReturn}</Text>
                </View>
              </View>
              <Text style={styles.reasoning}>{stock.reasoning}</Text>
              <View style={styles.stockTags}>
                <View style={[styles.tag, { backgroundColor: getRiskColor(stock.riskLevel) }]}>
                  <Text style={styles.tagText}>{stock.riskLevel}</Text>
                </View>
                <View style={[styles.tag, { backgroundColor: '#6366F1' }]}>
                  <Text style={styles.tagText}>Quantitative</Text>
                </View>
              </View>
            </View>
          ))}
        </View>

        {/* Analysis Methodology */}
        <View style={styles.methodologySection}>
          <Text style={styles.sectionTitle}>Analysis Methodology</Text>
          <View style={styles.methodologyGrid}>
            <View style={styles.methodologyItem}>
              <Icon name="bar-chart-2" size={16} color="#6366F1" />
              <Text style={styles.methodologyLabel}>Technical Analysis</Text>
            </View>
            <View style={styles.methodologyItem}>
              <Icon name="trending-up" size={16} color="#10B981" />
              <Text style={styles.methodologyLabel}>Fundamental Analysis</Text>
            </View>
            <View style={styles.methodologyItem}>
              <Icon name="trending-up" size={16} color="#F59E0B" />
              <Text style={styles.methodologyLabel}>Risk Metrics</Text>
            </View>
            <View style={styles.methodologyItem}>
              <Icon name="crosshair" size={16} color="#EF4444" />
              <Text style={styles.methodologyLabel}>Portfolio Optimization</Text>
            </View>
          </View>
        </View>
      </View>
    );
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return '#10B981';
      case 'medium':
        return '#F59E0B';
      case 'high':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  if (userLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Icon name="refresh-cw" size={32} color="#00cc99" />
          <Text style={styles.loadingText}>Loading your profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const user = userData?.me;
  const hasIncomeProfile = user?.incomeProfile;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTitleContainer}>
          <Icon name="trending-up" size={24} color="#00cc99" style={styles.headerIcon} />
          <Text style={styles.headerTitle}>AI Portfolio Advisor</Text>
        </View>
        <TouchableOpacity 
          style={[
            styles.profileButton,
            showProfileForm && styles.profileButtonActive
          ]}
          onPress={() => setShowProfileForm(!showProfileForm)}
          activeOpacity={0.7}
        >
          <View style={styles.profileButtonContent}>
            <Icon 
              name={showProfileForm ? "x" : "user"} 
              size={20} 
              color={showProfileForm ? "#EF4444" : "#00cc99"} 
            />
            <Text style={[
              styles.profileButtonText,
              showProfileForm && styles.profileButtonTextActive
            ]}>
              {showProfileForm ? 'Close Form' : 'Edit Profile'}
            </Text>
          </View>
          {!showProfileForm && (
            <View style={styles.profileButtonHint}>
              <Icon name="chevron-down" size={12} color="#00cc99" />
              <Text style={styles.profileButtonHintText} numberOfLines={2}>
                Tap to edit your financial profile
              </Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {/* Profile Status */}
        <View style={styles.profileStatus}>
          {hasIncomeProfile ? (
            <View style={styles.profileComplete}>
              <Icon name="check" size={24} color="#10B981" />
              <Text style={styles.profileCompleteText}>Profile Complete</Text>
              <Text style={styles.profileDetails}>
                {user.incomeProfile.incomeBracket} • {user.incomeProfile.age} years old • {user.incomeProfile.riskTolerance}
              </Text>
            </View>
          ) : (
            <View style={styles.profileIncomplete}>
              <Icon name="alert-circle" size={24} color="#F59E0B" />
              <Text style={styles.profileIncompleteText}>Complete Your Profile</Text>
              <Text style={styles.profileIncompleteSubtext}>
                Create your financial profile to get personalized AI recommendations
              </Text>
              <TouchableOpacity 
                style={styles.createProfileButton}
                onPress={() => setShowProfileForm(true)}
              >
                <Text style={styles.createProfileButtonText}>Create Profile</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Profile Form */}
        {showProfileForm && renderIncomeProfileForm()}

        {/* AI Recommendations */}
        {hasIncomeProfile && renderRecommendations()}
      </ScrollView>
    </SafeAreaView>
  );


}

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
    paddingVertical: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    gap: 8,
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 8,
  },
  headerIcon: {
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  profileButton: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    minWidth: 110,
    maxWidth: 120,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  profileButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    width: '100%',
    marginBottom: 2,
  },
  profileButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#00cc99',
    textAlign: 'center',
  },
  profileButtonHint: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    marginTop: 3,
    width: '100%',
  },
  profileButtonHintText: {
    fontSize: 9,
    color: '#6B7280',
    fontStyle: 'italic',
    textAlign: 'center',
    flexShrink: 1,
  },
  profileButtonActive: {
    backgroundColor: '#FEF2F2',
    borderColor: '#EF4444',
    transform: [{ scale: 1.05 }],
  },
  profileButtonTextActive: {
    color: '#EF4444',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  profileStatus: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  profileComplete: {
    alignItems: 'center',
  },
  profileCompleteText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#10B981',
    marginTop: 8,
    marginBottom: 4,
  },
  profileDetails: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  riskLevelDisplay: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  riskLevelHighlight: {
    fontWeight: 'bold',
    color: '#00cc99',
  },
  profileIncomplete: {
    alignItems: 'center',
  },
  profileIncompleteText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#F59E0B',
    marginTop: 8,
    marginBottom: 4,
  },
  profileIncompleteSubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 16,
  },
  createProfileButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  createProfileButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  formContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  formTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 20,
    textAlign: 'center',
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectedOption: {
    backgroundColor: '#00cc99',
    borderColor: '#00cc99',
  },
  optionText: {
    fontSize: 14,
    color: '#374151',
  },
  selectedOptionText: {
    color: '#fff',
    fontWeight: '600',
  },
  formActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: '#00cc99',
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 24,
  },
  generateButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 8,
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  recommendationsContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    marginBottom: 20,
    gap: 12,
    paddingLeft: 0,
  },
  recommendationTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
    flex: 1,
    marginRight: 12,
  },

  portfolioSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 16,
  },
  allocationSection: {
    marginBottom: 24,
  },
  allocationGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  allocationItem: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  allocationLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  allocationValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  stocksSection: {
    marginBottom: 20,
  },
  stockCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  stockInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  companyName: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  stockMetrics: {
    alignItems: 'flex-end',
  },
  allocationText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  expectedReturn: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  reasoning: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 12,
  },
  stockTags: {
    flexDirection: 'row',
    gap: 8,
  },
  tag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
  },
  riskMetricsSection: {
    marginBottom: 24,
  },
  riskMetricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    gap: 10,
  },
  riskMetricItem: {
    alignItems: 'center',
    padding: 16,
    paddingBottom: 24,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    flex: 1,
    position: 'relative',
  },
  riskMetricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
  riskMetricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
    marginTop: 4,
    marginBottom: 8,
  },
  riskMetricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginBottom: 4,
  },
  infoButton: {
    padding: 2,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  infoButtonBottomRight: {
    position: 'absolute',
    bottom: 6,
    right: 6,
    padding: 3,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    zIndex: 1,
  },
  sectorSection: {
    marginBottom: 24,
  },
  sectorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    gap: 10,
  },
  sectorItem: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    flex: 1,
  },
  sectorLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  sectorValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  methodologySection: {
    marginTop: 24,
  },
  methodologyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    gap: 10,
  },
  methodologyItem: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    flex: 1,
  },
  methodologyLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
});
