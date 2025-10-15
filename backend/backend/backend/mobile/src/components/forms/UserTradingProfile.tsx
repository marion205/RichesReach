import React, { useState } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import intelligentPriceAlertService, { UserProfile } from '../../features/stocks/services/IntelligentPriceAlertService';
interface UserTradingProfileProps {
onProfileSet: (profile: UserProfile) => void;
}
const UserTradingProfile: React.FC<UserTradingProfileProps> = ({ onProfileSet }) => {
const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
const [investmentHorizon, setInvestmentHorizon] = useState<'short' | 'medium' | 'long'>('medium');
const [portfolioSize, setPortfolioSize] = useState<number>(10000);
const [preferredSectors, setPreferredSectors] = useState<string[]>([]);
const [tradingFrequency, setTradingFrequency] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
const sectors = [
'Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer Goods',
'Industrial', 'Utilities', 'Real Estate', 'Materials', 'Communication'
];
const toggleSector = (sector: string) => {
setPreferredSectors(prev => 
prev.includes(sector) 
? prev.filter(s => s !== sector)
: [...prev, sector]
);
};
const handleSaveProfile = async () => {
const profile: UserProfile = {
riskTolerance,
investmentHorizon,
portfolioSize,
preferredSectors,
tradingFrequency,
};
try {
await intelligentPriceAlertService.setUserProfile(profile);
onProfileSet(profile);
Alert.alert('Success', 'Your trading profile has been saved! The AI will now provide personalized stock recommendations.');
} catch (error) {
Alert.alert('Error', 'Failed to save your trading profile. Please try again.');
}
};
const getRiskDescription = (risk: string) => {
switch (risk) {
case 'conservative':
return 'Prefers stable, low-volatility stocks with steady dividends';
case 'moderate':
return 'Balanced approach with mix of growth and value stocks';
case 'aggressive':
return 'Seeks high-growth, high-volatility opportunities';
default:
return '';
}
};
const getHorizonDescription = (horizon: string) => {
switch (horizon) {
case 'short':
return '1-6 months - Quick trades and momentum plays';
case 'medium':
return '6 months - 2 years - Balanced growth strategy';
case 'long':
return '2+ years - Long-term value and growth investing';
default:
return '';
}
};
return (
<ScrollView style={styles.container}>
<View style={styles.header}>
<Icon name="user" size={32} color="#007AFF" />
<Text style={styles.title}>Trading Profile Setup</Text>
<Text style={styles.subtitle}>
Help our AI understand your investment style for better recommendations
</Text>
</View>
{/* Risk Tolerance */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Risk Tolerance</Text>
{(['conservative', 'moderate', 'aggressive'] as const).map((risk) => (
<TouchableOpacity
key={risk}
style={[
styles.option,
riskTolerance === risk && styles.optionSelected
]}
onPress={() => setRiskTolerance(risk)}
>
<View style={styles.optionContent}>
<Text style={[
styles.optionTitle,
riskTolerance === risk && styles.optionTitleSelected
]}>
{risk.charAt(0).toUpperCase() + risk.slice(1)}
</Text>
<Text style={[
styles.optionDescription,
riskTolerance === risk && styles.optionDescriptionSelected
]}>
{getRiskDescription(risk)}
</Text>
</View>
{riskTolerance === risk && (
<Icon name="check" size={20} color="#007AFF" />
)}
</TouchableOpacity>
))}
</View>
{/* Investment Horizon */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Investment Horizon</Text>
{(['short', 'medium', 'long'] as const).map((horizon) => (
<TouchableOpacity
key={horizon}
style={[
styles.option,
investmentHorizon === horizon && styles.optionSelected
]}
onPress={() => setInvestmentHorizon(horizon)}
>
<View style={styles.optionContent}>
<Text style={[
styles.optionTitle,
investmentHorizon === horizon && styles.optionTitleSelected
]}>
{horizon.charAt(0).toUpperCase() + horizon.slice(1)} Term
</Text>
<Text style={[
styles.optionDescription,
investmentHorizon === horizon && styles.optionDescriptionSelected
]}>
{getHorizonDescription(horizon)}
</Text>
</View>
{investmentHorizon === horizon && (
<Icon name="check" size={20} color="#007AFF" />
)}
</TouchableOpacity>
))}
</View>
{/* Portfolio Size */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Portfolio Size</Text>
<View style={styles.portfolioSizeContainer}>
{[5000, 10000, 25000, 50000, 100000].map((size) => (
<TouchableOpacity
key={size}
style={[
styles.portfolioSizeOption,
portfolioSize === size && styles.portfolioSizeOptionSelected
]}
onPress={() => setPortfolioSize(size)}
>
<Text style={[
styles.portfolioSizeText,
portfolioSize === size && styles.portfolioSizeTextSelected
]}>
${size.toLocaleString()}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* Preferred Sectors */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Preferred Sectors</Text>
<Text style={styles.sectionSubtitle}>Select sectors you're interested in (optional)</Text>
<View style={styles.sectorsGrid}>
{sectors.map((sector) => (
<TouchableOpacity
key={sector}
style={[
styles.sectorOption,
preferredSectors.includes(sector) && styles.sectorOptionSelected
]}
onPress={() => toggleSector(sector)}
>
<Text style={[
styles.sectorText,
preferredSectors.includes(sector) && styles.sectorTextSelected
]}>
{sector}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* Trading Frequency */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Trading Frequency</Text>
{(['daily', 'weekly', 'monthly'] as const).map((frequency) => (
<TouchableOpacity
key={frequency}
style={[
styles.option,
tradingFrequency === frequency && styles.optionSelected
]}
onPress={() => setTradingFrequency(frequency)}
>
<View style={styles.optionContent}>
<Text style={[
styles.optionTitle,
tradingFrequency === frequency && styles.optionTitleSelected
]}>
{frequency.charAt(0).toUpperCase() + frequency.slice(1)}
</Text>
<Text style={[
styles.optionDescription,
tradingFrequency === frequency && styles.optionDescriptionSelected
]}>
{frequency === 'daily' && 'Active day trading and quick decisions'}
{frequency === 'weekly' && 'Regular monitoring with weekly adjustments'}
{frequency === 'monthly' && 'Long-term positions with monthly reviews'}
</Text>
</View>
{tradingFrequency === frequency && (
<Icon name="check" size={20} color="#007AFF" />
)}
</TouchableOpacity>
))}
</View>
{/* Save Button */}
<TouchableOpacity style={styles.saveButton} onPress={handleSaveProfile}>
<Icon name="save" size={20} color="#FFFFFF" />
<Text style={styles.saveButtonText}>Save Profile & Enable AI Recommendations</Text>
</TouchableOpacity>
{/* AI Explanation */}
<View style={styles.aiExplanation}>
<Icon name="cpu" size={24} color="#007AFF" />
<Text style={styles.aiExplanationTitle}>How AI Recommendations Work</Text>
<Text style={styles.aiExplanationText}>
Our AI analyzes technical indicators (RSI, MACD, Bollinger Bands), market conditions, 
and your personal profile to identify optimal buying opportunities. It considers:
</Text>
<View style={styles.aiFeatures}>
<Text style={styles.aiFeature}>• Technical analysis scores</Text>
<Text style={styles.aiFeature}>• Market trend alignment</Text>
<Text style={styles.aiFeature}>• Risk tolerance matching</Text>
<Text style={styles.aiFeature}>• Sector preferences</Text>
<Text style={styles.aiFeature}>• Investment horizon compatibility</Text>
</View>
</View>
</ScrollView>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
header: {
alignItems: 'center',
padding: 24,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
title: {
fontSize: 24,
fontWeight: '700',
color: '#1C1C1E',
marginTop: 12,
marginBottom: 8,
},
subtitle: {
fontSize: 16,
color: '#6C757D',
textAlign: 'center',
lineHeight: 24,
},
section: {
backgroundColor: '#FFFFFF',
marginTop: 16,
padding: 20,
},
sectionTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 8,
},
sectionSubtitle: {
fontSize: 14,
color: '#6C757D',
marginBottom: 16,
},
option: {
flexDirection: 'row',
alignItems: 'center',
padding: 16,
borderRadius: 12,
borderWidth: 2,
borderColor: '#E5E5EA',
marginBottom: 12,
},
optionSelected: {
borderColor: '#007AFF',
backgroundColor: '#F0F8FF',
},
optionContent: {
flex: 1,
},
optionTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
optionTitleSelected: {
color: '#007AFF',
},
optionDescription: {
fontSize: 14,
color: '#6C757D',
lineHeight: 20,
},
optionDescriptionSelected: {
color: '#007AFF',
},
portfolioSizeContainer: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 12,
},
portfolioSizeOption: {
paddingHorizontal: 16,
paddingVertical: 12,
borderRadius: 8,
borderWidth: 1,
borderColor: '#E5E5EA',
backgroundColor: '#FFFFFF',
},
portfolioSizeOptionSelected: {
borderColor: '#007AFF',
backgroundColor: '#F0F8FF',
},
portfolioSizeText: {
fontSize: 14,
fontWeight: '500',
color: '#1C1C1E',
},
portfolioSizeTextSelected: {
color: '#007AFF',
},
sectorsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 8,
},
sectorOption: {
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 6,
borderWidth: 1,
borderColor: '#E5E5EA',
backgroundColor: '#FFFFFF',
},
sectorOptionSelected: {
borderColor: '#007AFF',
backgroundColor: '#F0F8FF',
},
sectorText: {
fontSize: 12,
fontWeight: '500',
color: '#1C1C1E',
},
sectorTextSelected: {
color: '#007AFF',
},
saveButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#007AFF',
padding: 16,
margin: 20,
borderRadius: 12,
},
saveButtonText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
aiExplanation: {
backgroundColor: '#FFFFFF',
margin: 20,
padding: 20,
borderRadius: 12,
borderWidth: 1,
borderColor: '#E5E5EA',
},
aiExplanationTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 12,
marginBottom: 12,
},
aiExplanationText: {
fontSize: 14,
color: '#6C757D',
lineHeight: 20,
marginBottom: 16,
},
aiFeatures: {
gap: 8,
},
aiFeature: {
fontSize: 14,
color: '#6C757D',
lineHeight: 20,
},
});
export default UserTradingProfile;
