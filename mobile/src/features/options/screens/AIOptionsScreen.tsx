/**
* AI Options Screen
* Hedge Fund-Level Options Strategy Recommendations
*/
import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
TouchableOpacity,
TextInput,
Alert,
ActivityIndicator,
RefreshControl,
StatusBar,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import AIOptionsService, { OptionsRecommendation, MarketAnalysis } from '../services/AIOptionsService';
import logger from '../../../utils/logger';
interface AIOptionsScreenProps {
  navigation?: any;
}
const AIOptionsScreen: React.FC<AIOptionsScreenProps> = ({ navigation: navigationProp }) => {
  // Use React Navigation hook as primary, fallback to prop
  const nav = useNavigation<any>();
  const navigation = navigationProp || nav;
const [symbol, setSymbol] = useState('AAPL');
const [riskTolerance, setRiskTolerance] = useState<'low' | 'medium' | 'high'>('medium');
const [portfolioValue, setPortfolioValue] = useState('10000');
const [timeHorizon, setTimeHorizon] = useState('30');
const [recommendations, setRecommendations] = useState<OptionsRecommendation[]>([]);
const [marketAnalysis, setMarketAnalysis] = useState<MarketAnalysis | null>(null);
const [loading, setLoading] = useState(false);
const [refreshing, setRefreshing] = useState(false);
const [selectedRecommendation, setSelectedRecommendation] = useState<OptionsRecommendation | null>(null);
const aiOptionsService = AIOptionsService.getInstance();
useEffect(() => {
// Load initial recommendations
loadRecommendations();
}, []);
// Auto-reload when risk tolerance changes immediately
useEffect(() => {
if (riskTolerance) {
loadRecommendations();
}
}, [riskTolerance]);
// Note: Symbol changes only trigger reload when search button is pressed
const loadRecommendations = async () => {
setLoading(true);

// Defensive parsing for numeric inputs
const pv = Number.parseFloat(portfolioValue || '0');
const th = Number.parseInt(timeHorizon || '0', 10);
if (Number.isNaN(pv) || Number.isNaN(th)) {
Alert.alert('Invalid input', 'Please enter numeric values.');
setLoading(false);
return;
}

try {
const response = await aiOptionsService.getRecommendations(
symbol,
riskTolerance,
pv,
th
);
// Recommendations loaded successfully
setRecommendations(response.recommendations);
setMarketAnalysis(response.market_analysis);
    } catch (error: any) {
      // Suppress network errors - they're handled with mock data fallback
      if (!error?.message?.includes('Network request failed') && !error?.message?.includes('Failed to fetch')) {
        logger.error('AI Options Screen: Error loading recommendations:', error);
        // Only show alert for non-network errors
        Alert.alert('Error', `Failed to load AI options recommendations: ${error?.message || 'Unknown error'}`);
      } else {
        logger.warn('⚠️ Network error, using mock data for demo');
      }
    } finally {
      setLoading(false);
    }
};
const onRefresh = async () => {
setRefreshing(true);
await loadRecommendations();
setRefreshing(false);
};
const handleRecommendationPress = (recommendation: OptionsRecommendation) => {
setSelectedRecommendation(recommendation);
};
const handleOptimizeStrategy = async (strategyType: string) => {
try {
setLoading(true);
const response = await aiOptionsService.optimizeStrategy({
symbol: symbol,
strategy_type: strategyType,
current_price: marketAnalysis?.current_price || 0,
});
Alert.alert(
'Strategy Optimized',
`Optimization Score: ${response.optimization_score.toFixed(1)}%\n\nOptimal Parameters:\n${JSON.stringify(response.optimal_parameters, null, 2)}`
);
} catch (error) {
  logger.error('Error optimizing strategy:', error);
  Alert.alert('Error', 'Failed to optimize strategy');
} finally {
setLoading(false);
}
};
const renderRecommendationCard = (rec: OptionsRecommendation, index: number) => (
<TouchableOpacity
key={index}
style={[
styles.recommendationCard,
selectedRecommendation === rec && styles.selectedCard
]}
onPress={() => handleRecommendationPress(rec)}
>
<View style={styles.cardHeader}>
<View style={styles.strategyInfo}>
<Text style={styles.strategyName}>{rec.strategy_name}</Text>
<View style={[
styles.strategyTypeBadge,
{ backgroundColor: aiOptionsService.getStrategyTypeColor(rec.strategy_type) }
]}>
<Text style={styles.strategyTypeText}>{(rec.strategy_type || 'unknown').toUpperCase()}</Text>
</View>
</View>
<View style={styles.confidenceContainer}>
<Text style={styles.confidenceScore}>{(rec.confidence_score || 0).toFixed(0)}%</Text>
<Text style={styles.confidenceLabel}>Confidence</Text>
</View>
</View>
<View style={styles.cardBody}>
<Text style={styles.strategyRationale}>{rec.reasoning.strategy_rationale}</Text>
<View style={styles.metricsRow}>
<View style={styles.metric}>
<Text style={styles.metricValue}>${(rec.analytics?.max_profit || 0).toFixed(0)}</Text>
<Text style={styles.metricLabel}>Max Profit</Text>
</View>
<View style={styles.metric}>
<Text style={[styles.metricValue, { color: (rec.analytics?.max_loss || 0) > 0 ? '#FF3B30' : '#34C759' }]}>
${Math.abs(rec.analytics?.max_loss || 0).toFixed(0)}
</Text>
<Text style={styles.metricLabel}>Max Loss</Text>
</View>
<View style={styles.metric}>
<Text style={styles.metricValue}>{((rec.analytics?.probability_of_profit || 0) * 100).toFixed(0)}%</Text>
<Text style={styles.metricLabel}>Prob. Profit</Text>
</View>
</View>
<View style={styles.riskReturnRow}>
<View style={styles.riskContainer}>
<Text style={styles.riskLabel}>Risk: </Text>
<Text style={[
styles.riskValue,
{ color: (rec.risk_score || 0) <= 30 ? '#34C759' : (rec.risk_score || 0) <= 60 ? '#FF9500' : '#FF3B30' }
]}>
{aiOptionsService.getRiskLevelDescription(rec.risk_score || 0)}
</Text>
</View>
<Text style={styles.expectedReturn}>
Expected Return: {((rec.analytics?.expected_return || 0) * 100).toFixed(1)}%
</Text>
</View>
</View>
<View style={styles.cardFooter}>
<Text style={styles.expirationText}>
Expires in {rec.days_to_expiration || 0} days
</Text>
<TouchableOpacity
style={styles.optimizeButton}
onPress={() => handleOptimizeStrategy((rec.strategy_name || 'unknown').toLowerCase().replace(' ', '_'))}
>
<Icon name="tune" size={16} color="#007AFF" />
<Text style={styles.optimizeButtonText}>Optimize</Text>
</TouchableOpacity>
</View>
</TouchableOpacity>
);
const renderMarketAnalysis = () => {
if (!marketAnalysis) return null;
return (
<View style={styles.marketAnalysisCard}>
<Text style={styles.sectionTitle}>Market Analysis</Text>
<View style={styles.analysisRow}>
<Text style={styles.analysisLabel}>Current Price:</Text>
<Text style={styles.analysisValue}>${Number(marketAnalysis?.current_price || 0).toFixed(2)}</Text>
</View>
<View style={styles.analysisRow}>
<Text style={styles.analysisLabel}>Volatility:</Text>
<Text style={styles.analysisValue}>{((marketAnalysis?.volatility || 0) * 100).toFixed(1)}%</Text>
</View>
<View style={styles.analysisRow}>
<Text style={styles.analysisLabel}>Trend:</Text>
<Text style={[
styles.analysisValue,
{ 
color: (marketAnalysis?.trend_direction || 'neutral') === 'bullish' ? '#34C759' : 
(marketAnalysis?.trend_direction || 'neutral') === 'bearish' ? '#FF3B30' : '#8E8E93'
}
]}>
{(marketAnalysis.trend_direction || 'neutral').toUpperCase()}
</Text>
</View>
<View style={styles.analysisRow}>
<Text style={styles.analysisLabel}>Sentiment:</Text>
<Text style={[
styles.analysisValue,
{ 
color: (marketAnalysis?.sentiment_score || 0) > 0 ? '#34C759' : 
(marketAnalysis?.sentiment_score || 0) < 0 ? '#FF3B30' : '#8E8E93'
}
]}>
{(marketAnalysis?.sentiment_score || 0) > 0 ? '+' : ''}{(marketAnalysis?.sentiment_score || 0).toFixed(1)}
</Text>
</View>
</View>
);
};
const renderDetailedRecommendation = () => {
if (!selectedRecommendation) return null;
const rec = selectedRecommendation;
return (
<View style={styles.detailedView}>
<View style={styles.detailedHeader}>
<Text style={styles.detailedTitle}>{rec.strategy_name || 'Unknown Strategy'}</Text>
<TouchableOpacity
style={styles.closeButton}
onPress={() => setSelectedRecommendation(null)}
>
<Icon name="close" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
<ScrollView style={styles.detailedContent}>
<View style={styles.detailedSection}>
<Text style={styles.detailedSectionTitle}>Strategy Details</Text>
<Text style={styles.detailedText}>{rec.reasoning?.strategy_rationale || 'No rationale available'}</Text>
</View>
<View style={styles.detailedSection}>
<Text style={styles.detailedSectionTitle}>Market Outlook</Text>
<Text style={styles.detailedText}>{rec.reasoning?.market_outlook || 'No outlook available'}</Text>
</View>
<View style={styles.detailedSection}>
<Text style={styles.detailedSectionTitle}>Key Benefits</Text>
{(rec.reasoning?.key_benefits || []).map((benefit, index) => (
<Text key={index} style={styles.benefitItem}>• {benefit}</Text>
))}
</View>
<View style={styles.detailedSection}>
<Text style={styles.detailedSectionTitle}>Risk Factors</Text>
{(rec.reasoning?.risk_factors || []).map((risk, index) => (
<Text key={index} style={styles.riskItem}>• {risk}</Text>
))}
</View>
<View style={styles.detailedSection}>
<Text style={styles.detailedSectionTitle}>Options Details</Text>
{(rec.options || []).map((option, index) => (
<View key={index} style={styles.optionDetail}>
<Text style={styles.optionText}>
{(option.action || 'unknown').toUpperCase()} {option.quantity} {(option.type || 'unknown').toUpperCase()}(s)
</Text>
<Text style={styles.optionText}>
Strike: ${option.strike || 0} | Premium: ${Number(option?.premium || 0).toFixed(2)}
</Text>
<Text style={styles.optionText}>
Expiration: {option.expiration || 'Unknown'}
</Text>
</View>
))}
</View>
</ScrollView>
</View>
);
};
return (
<View style={styles.container}>
<StatusBar barStyle="dark-content" backgroundColor="#fff" />
<View style={styles.header}>
<TouchableOpacity
style={styles.backButton}
onPress={() => navigation.goBack()}
>
<Icon name="arrow-back" size={24} color="#000" />
</TouchableOpacity>
<Text style={styles.headerTitle}>AI Options</Text>
<View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.copilotButton}
            onPress={() => {
              try {
                // Try direct navigation first (if in same stack)
                if (navigation && typeof navigation.navigate === 'function') {
                  // Try 'options-copilot' first (works in HomeStack)
                  try {
                    navigation.navigate('options-copilot');
                  } catch {
                    // Fallback to nested navigation for InvestStack
                    try {
                      navigation.navigate('Invest', { 
                        screen: 'OptionsCopilot',
                        params: {}
                      });
                    } catch {
                      // Last resort: try OptionsCopilot directly
                      navigation.navigate('OptionsCopilot');
                    }
                  }
                }
              } catch (error: any) {
                // Suppress navigation errors for demo
                logger.warn('⚠️ Navigation to Copilot not available:', error?.message);
              }
            }}
          >
                <Icon name="flash-on" size={20} color="#00cc99" />
                <Text style={styles.copilotButtonText}>Copilot</Text>
          </TouchableOpacity>
<TouchableOpacity
style={styles.refreshButton}
onPress={loadRecommendations}
disabled={loading}
>
<Icon name="refresh" size={24} color="#007AFF" />
</TouchableOpacity>
</View>
</View>
{selectedRecommendation ? (
renderDetailedRecommendation()
) : (
<ScrollView
style={styles.content}
refreshControl={
<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
}
>
{/* Input Section */}
<View style={styles.inputSection}>
<View style={styles.inputRow}>
<TextInput
style={styles.symbolInput}
value={symbol}
onChangeText={setSymbol}
placeholder="Symbol (e.g., AAPL)"
placeholderTextColor="#8E8E93"
autoCapitalize="characters"
/>
<TouchableOpacity
style={[styles.searchButton, loading && styles.searchButtonDisabled]}
onPress={loadRecommendations}
disabled={loading}
>
{loading ? (
<ActivityIndicator size="small" color="#fff" />
) : (
<Icon name="search" size={20} color="#fff" />
)}
</TouchableOpacity>
</View>
<View style={styles.parameterRow}>
<View style={styles.parameterGroup}>
<Text style={styles.parameterLabel}>Risk Tolerance</Text>
<View style={styles.riskButtons}>
{(['low', 'medium', 'high'] as const).map((risk) => (
<TouchableOpacity
key={risk}
style={[
styles.riskButton,
riskTolerance === risk && styles.riskButtonActive
]}
onPress={() => {
setRiskTolerance(risk);
}}
>
<Text style={[
styles.riskButtonText,
riskTolerance === risk && styles.riskButtonTextActive
]}>
{(risk || 'unknown').toUpperCase()}
</Text>
</TouchableOpacity>
))}
</View>
</View>
</View>
<View style={styles.parameterRow}>
<View style={styles.parameterGroup}>
<Text style={styles.parameterLabel}>Portfolio Value ($)</Text>
<TextInput
style={styles.parameterInput}
value={portfolioValue}
onChangeText={setPortfolioValue}
keyboardType="numeric"
placeholder="10000"
/>
</View>
<View style={styles.parameterGroup}>
<Text style={styles.parameterLabel}>Time Horizon (days)</Text>
<TextInput
style={styles.parameterInput}
value={timeHorizon}
onChangeText={setTimeHorizon}
keyboardType="numeric"
placeholder="30"
/>
</View>
</View>
</View>
{/* Status Message */}
{loading && (
<View style={styles.statusMessage}>
<ActivityIndicator size="small" color="#007AFF" />
<Text style={styles.statusText}>
Loading AI recommendations for {symbol}...
</Text>
</View>
)}
{/* Market Analysis */}
{renderMarketAnalysis()}
{/* Recommendations */}
<View style={styles.recommendationsSection}>
<Text style={styles.sectionTitle}>
AI Recommendations ({recommendations.length})
</Text>
{/* Educational Disclaimer */}
<View style={styles.disclaimerBox}>
  <Icon name="alert-triangle" size={16} color="#F59E0B" />
  <View style={styles.disclaimerContent}>
    <Text style={styles.disclaimerTitle}>Educational Purpose Only</Text>
    <Text style={styles.disclaimerText}>
      AI and ML recommendations are for educational and informational purposes only. 
      This is not investment advice. Options trading involves significant risk. Consult 
      a qualified financial advisor before making investment decisions. Past performance 
      does not guarantee future results.
    </Text>
  </View>
</View>
{loading ? (
<View style={styles.loadingContainer}>
<ActivityIndicator size="large" color="#007AFF" />
<Text style={styles.loadingText}>Generating AI recommendations...</Text>
</View>
) : (
recommendations.map((rec, index) => renderRecommendationCard(rec, index))
)}
</View>
</ScrollView>
)}
</View>
);
};
const styles = StyleSheet.create({
disclaimerBox: {
flexDirection: 'row',
backgroundColor: '#FFF3E0',
padding: 12,
borderRadius: 8,
marginBottom: 16,
borderLeftWidth: 3,
borderLeftColor: '#F59E0B',
alignItems: 'flex-start',
},
disclaimerContent: {
flex: 1,
marginLeft: 8,
},
disclaimerTitle: {
fontSize: 12,
fontWeight: '600',
color: '#92400E',
marginBottom: 4,
},
disclaimerText: {
fontSize: 11,
color: '#92400E',
lineHeight: 16,
},
container: {
flex: 1,
backgroundColor: '#f5f5f5',
paddingTop: 44, // Account for status bar
},
header: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
paddingHorizontal: 16,
paddingVertical: 12,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#e0e0e0',
},
backButton: {
padding: 8,
},
headerTitle: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
headerActions: {
flexDirection: 'row',
alignItems: 'center',
},
copilotButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#E8F5E8',
paddingHorizontal: 12,
paddingVertical: 6,
borderRadius: 16,
marginRight: 8,
},
copilotButtonText: {
fontSize: 12,
fontWeight: '600',
color: '#00cc99',
marginLeft: 4,
},
refreshButton: {
padding: 8,
},
content: {
flex: 1,
},
inputSection: {
backgroundColor: '#fff',
padding: 16,
marginBottom: 8,
},
inputRow: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 16,
},
symbolInput: {
flex: 1,
height: 40,
borderWidth: 1,
borderColor: '#e0e0e0',
borderRadius: 8,
paddingHorizontal: 12,
fontSize: 16,
marginRight: 12,
},
inputLoadingIndicator: {
position: 'absolute',
right: 50,
top: 8,
},
statusMessage: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#F0F8FF',
paddingVertical: 12,
paddingHorizontal: 16,
borderRadius: 8,
marginBottom: 16,
borderLeftWidth: 4,
borderLeftColor: '#007AFF',
},
statusText: {
marginLeft: 8,
fontSize: 14,
color: '#007AFF',
fontWeight: '500',
},
searchButton: {
backgroundColor: '#007AFF',
paddingHorizontal: 16,
paddingVertical: 10,
borderRadius: 8,
},
searchButtonDisabled: {
backgroundColor: '#8E8E93',
opacity: 0.6,
},
parameterRow: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 12,
},
parameterGroup: {
flex: 1,
marginRight: 8,
},
parameterLabel: {
fontSize: 12,
color: '#666',
marginBottom: 4,
},
parameterInput: {
height: 36,
borderWidth: 1,
borderColor: '#e0e0e0',
borderRadius: 6,
paddingHorizontal: 8,
fontSize: 14,
},
riskButtons: {
flexDirection: 'row',
},
riskButton: {
flex: 1,
paddingVertical: 8,
paddingHorizontal: 12,
borderWidth: 1,
borderColor: '#e0e0e0',
borderRadius: 6,
marginRight: 4,
alignItems: 'center',
},
riskButtonActive: {
backgroundColor: '#007AFF',
borderColor: '#007AFF',
},
riskButtonText: {
fontSize: 12,
color: '#666',
},
riskButtonTextActive: {
color: '#fff',
},
marketAnalysisCard: {
backgroundColor: '#fff',
padding: 16,
marginBottom: 8,
},
sectionTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 12,
},
analysisRow: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 8,
},
analysisLabel: {
fontSize: 14,
color: '#666',
},
analysisValue: {
fontSize: 14,
fontWeight: '500',
color: '#000',
},
recommendationsSection: {
padding: 16,
},
loadingContainer: {
alignItems: 'center',
paddingVertical: 40,
},
loadingText: {
marginTop: 12,
fontSize: 14,
color: '#666',
},
recommendationCard: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
selectedCard: {
borderWidth: 2,
borderColor: '#007AFF',
},
cardHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 12,
},
strategyInfo: {
flex: 1,
},
strategyName: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 4,
},
strategyTypeBadge: {
paddingHorizontal: 8,
paddingVertical: 2,
borderRadius: 4,
alignSelf: 'flex-start',
},
strategyTypeText: {
fontSize: 10,
fontWeight: '600',
color: '#fff',
},
confidenceContainer: {
alignItems: 'center',
},
confidenceScore: {
fontSize: 18,
fontWeight: '700',
color: '#007AFF',
},
confidenceLabel: {
fontSize: 10,
color: '#666',
},
cardBody: {
marginBottom: 12,
},
strategyRationale: {
fontSize: 14,
color: '#666',
lineHeight: 20,
marginBottom: 12,
},
metricsRow: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 12,
},
metric: {
alignItems: 'center',
flex: 1,
},
metricValue: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
metricLabel: {
fontSize: 10,
color: '#666',
marginTop: 2,
},
riskReturnRow: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
},
riskContainer: {
flexDirection: 'row',
alignItems: 'center',
},
riskLabel: {
fontSize: 12,
color: '#666',
},
riskValue: {
fontSize: 12,
fontWeight: '500',
},
expectedReturn: {
fontSize: 12,
color: '#666',
},
cardFooter: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingTop: 12,
borderTopWidth: 1,
borderTopColor: '#f0f0f0',
},
expirationText: {
fontSize: 12,
color: '#666',
},
optimizeButton: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 12,
paddingVertical: 6,
backgroundColor: '#f0f8ff',
borderRadius: 6,
},
optimizeButtonText: {
fontSize: 12,
color: '#007AFF',
marginLeft: 4,
},
detailedView: {
flex: 1,
backgroundColor: '#fff',
},
detailedHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
padding: 16,
borderBottomWidth: 1,
borderBottomColor: '#e0e0e0',
},
detailedTitle: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
closeButton: {
padding: 8,
},
detailedContent: {
flex: 1,
padding: 16,
},
detailedSection: {
marginBottom: 20,
},
detailedSectionTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 8,
},
detailedText: {
fontSize: 14,
color: '#666',
lineHeight: 20,
},
benefitItem: {
fontSize: 14,
color: '#34C759',
marginBottom: 4,
},
riskItem: {
fontSize: 14,
color: '#FF3B30',
marginBottom: 4,
},
optionDetail: {
backgroundColor: '#f8f9fa',
padding: 12,
borderRadius: 8,
marginBottom: 8,
},
optionText: {
fontSize: 12,
color: '#666',
marginBottom: 2,
},
});
export default AIOptionsScreen;
