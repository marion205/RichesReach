import React, { useState, useEffect, useRef } from 'react';
import {
View,
Text,
StyleSheet,
Dimensions,
TouchableOpacity,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/Feather';
import PortfolioEducationModal from './PortfolioEducationModal';
import EducationalTooltip from '../../../components/common/EducationalTooltip';
import { getTermExplanation } from '../../../shared/financialTerms';
import webSocketService, { PortfolioUpdate } from '../../../services/WebSocketService';
import logger from '../../../utils/logger';
const { width } = Dimensions.get('window');
interface PortfolioGraphProps {
totalValue: number;
totalReturn: number;
totalReturnPercent: number;
onPress?: () => void;
}
export default function PortfolioGraph({ 
totalValue, 
totalReturn, 
totalReturnPercent,
onPress 
}: PortfolioGraphProps) {
const [showEducationModal, setShowEducationModal] = useState(false);
const [clickedElement, setClickedElement] = useState<string>('');
const [portfolioHistory, setPortfolioHistory] = useState<number[]>([]);
const [isLoading, setIsLoading] = useState(true);
// WebSocket state
const [liveTotalValue, setLiveTotalValue] = useState(totalValue);
const [liveTotalReturn, setLiveTotalReturn] = useState(totalReturn);
const [liveTotalReturnPercent, setLiveTotalReturnPercent] = useState(totalReturnPercent);
const [isLiveData, setIsLiveData] = useState(false);
const wsService = useRef(webSocketService);
// Use live data if available, otherwise fall back to props
const currentTotalValue = isLiveData ? liveTotalValue : totalValue;
const currentTotalReturn = isLiveData ? liveTotalReturn : totalReturn;
const currentTotalReturnPercent = isLiveData ? liveTotalReturnPercent : totalReturnPercent;
const isPositive = currentTotalReturn >= 0 && currentTotalReturnPercent >= 0;
const returnColor = isPositive ? '#34C759' : '#FF3B30';
const returnIcon = isPositive ? 'trending-up' : 'trending-down';
const formatCurrency = (amount: number) => {
return `$${amount.toLocaleString('en-US', { 
minimumFractionDigits: 2, 
maximumFractionDigits: 2 
})}`;
};
const formatPercent = (percent: number) => {
const isPositive = percent >= 0;
return `${isPositive ? '+' : ''}${percent.toFixed(2)}%`;
};
// Fetch live portfolio data
const fetchLivePortfolioData = async () => {
try {
setIsLoading(true);
// In a real app, this would fetch from your backend API
// For now, we'll simulate live data with some realistic variations
const baseValue = totalValue;
const data = [];
// Generate 30 days of data with realistic market movements
for (let i = 0; i < 30; i++) {
const daysAgo = 29 - i;
const volatility = 0.015; // 1.5% daily volatility
const trend = isPositive ? 0.0005 : -0.0003; // Slight upward or downward trend
// Add some realistic market noise
const randomChange = (Math.random() - 0.5) * volatility;
const trendEffect = trend * daysAgo;
const value = baseValue * (1 + trendEffect + randomChange);
data.push(Math.max(value, baseValue * 0.85)); // Don't go below 85% of current value
}
// Ensure the last value matches current total value
data[data.length - 1] = totalValue;
setPortfolioHistory(data);
} catch (error) {
logger.error('Error fetching portfolio data:', error);
// Fallback to generated data
const fallbackData = generateFallbackData();
setPortfolioHistory(fallbackData);
} finally {
setIsLoading(false);
}
};
// Fallback data generation
const generateFallbackData = () => {
const data = [];
const baseValue = totalValue * 0.9;
const volatility = 0.02;
for (let i = 0; i < 30; i++) {
const randomChange = (Math.random() - 0.5) * volatility;
const value = baseValue * (1 + randomChange * i / 30);
data.push(Math.max(value, baseValue * 0.8));
}
data[data.length - 1] = totalValue;
return data;
};
// Load data on component mount
useEffect(() => {
fetchLivePortfolioData();
}, [totalValue]);
// WebSocket setup for live portfolio updates
useEffect(() => {
const setupWebSocket = async () => {
try {
// Set up portfolio update callback
wsService.current.setCallbacks({
onPortfolioUpdate: (portfolio: PortfolioUpdate) => {
// Update live data
setLiveTotalValue(portfolio.totalValue);
setLiveTotalReturn(portfolio.totalReturn);
setLiveTotalReturnPercent(portfolio.totalReturnPercent);
setIsLiveData(true);
// Add to portfolio history for chart
setPortfolioHistory(prev => {
const newHistory = [...prev, portfolio.totalValue];
// Keep only last 30 data points
return newHistory.length > 30 ? newHistory.slice(-30) : newHistory;
});
}
});
// Connect to WebSocket
wsService.current.connect();
// Subscribe to portfolio updates
setTimeout(() => {
wsService.current?.subscribeToPortfolio();
}, 1000);
} catch (error) {
logger.error('Error setting up portfolio WebSocket:', error);
}
};
setupWebSocket();
// Cleanup on unmount
return () => {
// Don't disconnect the shared WebSocket service
// as other components might be using it
};
}, []);
const portfolioData = portfolioHistory.length > 0 ? portfolioHistory : generateFallbackData();
const minValue = Math.min(...portfolioData);
const maxValue = Math.max(...portfolioData);
const chartData = {
labels: ['', '', '', '', '', ''], // Minimal labels for cleaner look
datasets: [
{
data: portfolioData,
color: (opacity = 1) => returnColor,
strokeWidth: 3,
},
],
};
const chartConfig = {
backgroundColor: '#FFFFFF',
backgroundGradientFrom: '#FFFFFF',
backgroundGradientTo: '#FFFFFF',
decimalPlaces: 0,
color: (opacity = 1) => returnColor,
labelColor: (opacity = 1) => '#8E8E93',
style: {
borderRadius: 16,
},
propsForDots: {
r: '0', // Hide dots for cleaner line
},
propsForBackgroundLines: {
strokeDasharray: '', // Solid lines
stroke: '#E5E5EA',
strokeWidth: 1,
},
};
const handleElementPress = (element: string) => {
setClickedElement(element);
setShowEducationModal(true);
};
return (
<>
<View style={styles.container}>
{/* Header */}
<View style={styles.header}>
<View style={styles.titleContainer}>
<Icon name="pie-chart" size={20} color="#34C759" />
<Text style={styles.title}>Portfolio Performance</Text>
</View>
<View style={styles.timeframeContainer}>
<Text style={styles.timeframe}>1M</Text>
</View>
</View>
{/* Value Display */}
<View style={styles.valueContainer}>
<EducationalTooltip
term="Total Value"
explanation={getTermExplanation('Total Value')}
position="top"
>
<TouchableOpacity 
style={styles.valueTouchable}
onPress={() => handleElementPress('totalValue')}
activeOpacity={0.7}
>
<Text style={styles.valueText}>{formatCurrency(currentTotalValue)}</Text>
</TouchableOpacity>
</EducationalTooltip>
<EducationalTooltip
term="Total Return"
explanation={getTermExplanation('Total Return')}
position="top"
>
<TouchableOpacity 
style={styles.returnTouchable}
onPress={() => handleElementPress('return')}
activeOpacity={0.7}
>
<View style={styles.returnContainer}>
<Icon 
name={returnIcon} 
size={16} 
color={returnColor} 
/>
<Text style={[styles.returnText, { color: returnColor }]}>
{formatCurrency(Math.abs(currentTotalReturn))} ({formatPercent(currentTotalReturnPercent)})
</Text>
</View>
</TouchableOpacity>
</EducationalTooltip>
</View>
{/* Chart */}
<TouchableOpacity 
style={styles.chartContainer}
onPress={() => handleElementPress('chart')}
activeOpacity={0.7}
>
<LineChart
data={chartData}
width={width - 64} // Account for margins
height={200}
chartConfig={chartConfig}
bezier
style={styles.chart}
withInnerLines={true}
withOuterLines={false}
withVerticalLines={false}
withHorizontalLines={true}
withDots={false}
withShadow={false}
/>
</TouchableOpacity>
{/* Footer */}
<View style={styles.footer}>
<Text style={styles.footerText}>
{isLoading ? 'Loading live data...' : 
isLiveData ? ' Live data • Tap any element to learn what it means' : 
'Tap any element to learn what it means'}
</Text>
</View>
</View>
{/* Educational Modal */}
<PortfolioEducationModal
visible={showEducationModal}
onClose={() => setShowEducationModal(false)}
isPositive={isPositive}
totalValue={currentTotalValue}
totalReturn={currentTotalReturn}
totalReturnPercent={currentTotalReturnPercent}
clickedElement={clickedElement}
/>
</>
);
}
const styles = StyleSheet.create({
container: {
backgroundColor: '#FFFFFF',
marginHorizontal: 16,
marginVertical: 8,
borderRadius: 16,
padding: 20,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 5,
borderWidth: 1,
borderColor: '#E5E5EA',
},
header: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 16,
},
titleContainer: {
flexDirection: 'row',
alignItems: 'center',
gap: 8,
},
title: {
fontSize: 18,
fontWeight: '700',
color: '#1C1C1E',
},
timeframeContainer: {
backgroundColor: '#F2F2F7',
paddingHorizontal: 12,
paddingVertical: 6,
borderRadius: 8,
},
timeframe: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
},
valueContainer: {
marginBottom: 20,
},
valueTouchable: {
paddingVertical: 8,
paddingHorizontal: 16,
borderRadius: 8,
},
returnTouchable: {
paddingVertical: 8,
paddingHorizontal: 16,
borderRadius: 8,
},
valueText: {
fontSize: 28,
fontWeight: '800',
color: '#1C1C1E',
marginBottom: 4,
},
returnContainer: {
flexDirection: 'row',
alignItems: 'center',
gap: 6,
},
returnText: {
fontSize: 16,
fontWeight: '600',
},
chartContainer: {
alignItems: 'center',
marginBottom: 16,
},
chart: {
borderRadius: 16,
},
footer: {
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
paddingTop: 12,
},
footerText: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
},
});
