import React from 'react';
import {
View,
Text,
StyleSheet,
Modal,
TouchableOpacity,
ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface PortfolioEducationModalProps {
visible: boolean;
onClose: () => void;
isPositive: boolean;
totalValue: number;
totalReturn: number;
totalReturnPercent: number;
clickedElement: string;
}
export default function PortfolioEducationModal({
visible,
onClose,
isPositive,
totalValue,
totalReturn,
totalReturnPercent,
clickedElement,
}: PortfolioEducationModalProps) {
// Ensure we have the correct positive/negative logic
const isActuallyPositive = totalReturn >= 0 && totalReturnPercent >= 0;
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
const getContextualContent = () => {
switch (clickedElement) {
case 'totalValue':
return {
title: " Portfolio Value",
icon: 'dollar-sign',
color: '#1E90FF',
explanation: `Your total portfolio value is ${formatCurrency(totalValue)}.`,
concepts: [
{
title: "What is portfolio value?",
description: "This is the current total worth of all your investments combined. It includes stocks, bonds, and other assets you own."
},
{
title: "How is it calculated?",
description: "Portfolio value = (Number of shares × Current stock price) for each stock, then add them all together."
},
{
title: "Why does it change?",
description: "Stock prices fluctuate throughout the day based on company performance, market conditions, and investor sentiment."
},
{
title: "What should you know?",
description: "Focus on long-term trends rather than daily changes. A diversified portfolio helps reduce risk."
}
]
};
case 'return':
return {
title: " Return & Percentage",
icon: 'percent',
color: isActuallyPositive ? '#34C759' : '#FF3B30',
explanation: `Your portfolio has ${isActuallyPositive ? 'gained' : 'lost'} ${formatCurrency(Math.abs(totalReturn))} (${formatPercent(totalReturnPercent)}).`,
concepts: [
{
title: "What does this percentage mean?",
description: `${formatPercent(totalReturnPercent)} means for every $100 you invested, you now have $${(100 + totalReturnPercent).toFixed(2)}. ${isActuallyPositive ? 'This is a gain!' : 'This is a loss.'}`
},
{
title: "How is this calculated?",
description: "Return % = (Current Value - Original Cost) ÷ Original Cost × 100. Your return amount is the dollar difference."
},
{
title: "Why did this happen?",
description: `${isActuallyPositive ? 'Your stocks performed well due to strong company fundamentals and market growth.' : 'Stock prices fell due to market conditions, company performance, or economic factors.'}`
},
{
title: "What should you do?",
description: `${isActuallyPositive ? 'Consider your goals - you might rebalance or take some profits.' : 'Stay calm and think long-term. Market downturns can be buying opportunities.'}`
}
]
};
case 'chart':
return {
title: " Performance Chart",
icon: 'trending-up',
color: '#FF6B35',
explanation: "This chart shows how your portfolio value has changed over time.",
concepts: [
{
title: "What does this chart show?",
description: "The line represents your portfolio's value over time. Upward trends show gains, downward trends show losses."
},
{
title: "How to read it?",
description: "The Y-axis shows dollar amounts, the X-axis shows time. The line color indicates whether you're up (green) or down (red)."
},
{
title: "Why is it important?",
description: "Charts help you see trends and patterns. They show if your investments are growing over time, not just daily changes."
},
{
title: "What to look for?",
description: "Look for overall upward trends over months/years, not daily fluctuations. Some volatility is completely normal in investing."
},
{
title: "Remember:",
description: "This is a snapshot of recent performance. Long-term investing success is measured in years, not days or weeks."
}
]
};
default:
return {
title: " Portfolio Overview",
icon: 'pie-chart',
color: '#1E90FF',
explanation: "Here's an overview of your portfolio performance.",
concepts: [
{
title: "What is a portfolio?",
description: "Your portfolio is your collection of investments - stocks, bonds, and other assets you own."
},
{
title: "Why track performance?",
description: "Monitoring helps you understand how your investments are doing and make informed decisions."
},
{
title: "Key metrics to watch:",
description: "Total value, returns, and performance over time. Focus on long-term trends."
},
{
title: "Remember:",
description: "Investing is long-term. Daily changes are normal - focus on your overall strategy."
}
]
};
}
};
const content = getContextualContent();
return (
<Modal
visible={visible}
animationType="slide"
transparent={true}
onRequestClose={onClose}
>
<View style={styles.overlay}>
<View style={styles.modal}>
{/* Header */}
<View style={styles.header}>
<View style={styles.titleContainer}>
<Icon name={content.icon} size={24} color={content.color} />
<Text style={styles.title}>{content.title}</Text>
</View>
<TouchableOpacity onPress={onClose} style={styles.closeButton}>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
{/* Performance Summary */}
<View style={styles.summaryContainer}>
<Text style={styles.summaryText}>{content.explanation}</Text>
{clickedElement !== 'chart' && (
<View style={styles.performanceContainer}>
<Text style={[styles.performanceText, { color: content.color }]}>
{formatCurrency(Math.abs(totalReturn))} ({formatPercent(totalReturnPercent)})
</Text>
</View>
)}
</View>
{/* Educational Content */}
<ScrollView style={styles.contentContainer} showsVerticalScrollIndicator={false}>
{content.concepts.map((concept, index) => (
<View key={index} style={styles.conceptCard}>
<Text style={styles.conceptTitle}>{concept.title}</Text>
<Text style={styles.conceptDescription}>{concept.description}</Text>
</View>
))}
{/* Percentage Explanation - Only show for return-related clicks */}
{clickedElement !== 'chart' && (
<View style={styles.percentageCard}>
<Text style={styles.percentageTitle}> Understanding Your Return</Text>
<View style={styles.percentageExample}>
<Text style={styles.percentageText}>
<Text style={styles.bold}>Example:</Text> If you invested $1,000 and now have $1,176.50:
</Text>
<Text style={styles.percentageFormula}>
Return = ($1,176.50 - $1,000) ÷ $1,000 × 100 = +17.65%
</Text>
<Text style={styles.percentageMeaning}>
This means you gained $176.50 on your $1,000 investment!
</Text>
</View>
</View>
)}
{/* Investment Concepts */}
<View style={styles.conceptsCard}>
<Text style={styles.conceptsTitle}> Key Investment Concepts</Text>
<View style={styles.conceptsList}>
<View style={styles.conceptItem}>
<Text style={styles.conceptTerm}>Portfolio:</Text>
<Text style={styles.conceptDefinition}>Your collection of investments (stocks, bonds, etc.)</Text>
</View>
<View style={styles.conceptItem}>
<Text style={styles.conceptTerm}>Return:</Text>
<Text style={styles.conceptDefinition}>The profit or loss on your investment</Text>
</View>
<View style={styles.conceptItem}>
<Text style={styles.conceptTerm}>Diversification:</Text>
<Text style={styles.conceptDefinition}>Spreading investments across different companies and sectors</Text>
</View>
<View style={styles.conceptItem}>
<Text style={styles.conceptTerm}>Risk:</Text>
<Text style={styles.conceptDefinition}>The chance that your investment could lose value</Text>
</View>
</View>
</View>
{/* General Investment Tips */}
<View style={styles.tipsCard}>
<Text style={styles.tipsTitle}> Investment Tips</Text>
<View style={styles.tipsList}>
<Text style={styles.tipItem}>• Diversify your portfolio across different sectors</Text>
<Text style={styles.tipItem}>• Invest for the long term, not short-term gains</Text>
<Text style={styles.tipItem}>• Don't invest money you can't afford to lose</Text>
<Text style={styles.tipItem}>• Regularly review and rebalance your portfolio</Text>
<Text style={styles.tipItem}>• Consider dollar-cost averaging to reduce risk</Text>
</View>
</View>
</ScrollView>
{/* Footer */}
<View style={styles.footer}>
<TouchableOpacity style={styles.learnMoreButton} onPress={onClose}>
<Text style={styles.learnMoreText}>Got it! Close</Text>
</TouchableOpacity>
</View>
</View>
</View>
</Modal>
);
}
const styles = StyleSheet.create({
overlay: {
flex: 1,
backgroundColor: 'rgba(0, 0, 0, 0.5)',
justifyContent: 'center',
alignItems: 'center',
},
modal: {
backgroundColor: '#FFFFFF',
borderRadius: 20,
width: '90%',
height: '85%',
shadowColor: '#000',
shadowOffset: { width: 0, height: 4 },
shadowOpacity: 0.25,
shadowRadius: 10,
elevation: 10,
},
header: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
padding: 20,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
titleContainer: {
flexDirection: 'row',
alignItems: 'center',
gap: 8,
},
title: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
},
closeButton: {
padding: 4,
},
summaryContainer: {
padding: 20,
alignItems: 'center',
},
summaryText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
marginBottom: 12,
},
performanceContainer: {
backgroundColor: '#F2F2F7',
paddingHorizontal: 16,
paddingVertical: 8,
borderRadius: 12,
},
performanceText: {
fontSize: 18,
fontWeight: '700',
},
contentContainer: {
flex: 1,
paddingHorizontal: 20,
},
conceptCard: {
backgroundColor: '#F8F9FA',
borderRadius: 12,
padding: 16,
marginBottom: 12,
},
conceptTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 8,
},
conceptDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
tipsCard: {
backgroundColor: '#E3F2FD',
borderRadius: 12,
padding: 16,
marginBottom: 20,
},
tipsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1976D2',
marginBottom: 12,
},
tipsList: {
gap: 8,
},
tipItem: {
fontSize: 14,
color: '#1976D2',
lineHeight: 20,
},
percentageCard: {
backgroundColor: '#FFF3E0',
borderRadius: 12,
padding: 16,
marginBottom: 12,
},
percentageTitle: {
fontSize: 16,
fontWeight: '600',
color: '#F57C00',
marginBottom: 12,
},
percentageExample: {
gap: 8,
},
percentageText: {
fontSize: 14,
color: '#F57C00',
lineHeight: 20,
},
percentageFormula: {
fontSize: 14,
color: '#F57C00',
fontFamily: 'monospace',
backgroundColor: '#FFE0B2',
padding: 8,
borderRadius: 6,
marginVertical: 4,
},
percentageMeaning: {
fontSize: 14,
color: '#F57C00',
fontWeight: '600',
lineHeight: 20,
},
bold: {
fontWeight: '700',
},
conceptsCard: {
backgroundColor: '#F0F8FF',
borderRadius: 12,
padding: 16,
marginBottom: 12,
},
conceptsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1E90FF',
marginBottom: 12,
},
conceptsList: {
gap: 12,
},
conceptItem: {
flexDirection: 'row',
alignItems: 'flex-start',
gap: 8,
},
conceptTerm: {
fontSize: 14,
fontWeight: '600',
color: '#1E90FF',
minWidth: 80,
},
conceptDefinition: {
fontSize: 14,
color: '#1E90FF',
flex: 1,
lineHeight: 20,
},
footer: {
padding: 20,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
learnMoreButton: {
backgroundColor: '#34C759',
borderRadius: 12,
paddingVertical: 16,
alignItems: 'center',
},
learnMoreText: {
color: '#FFFFFF',
fontSize: 16,
fontWeight: '600',
},
});
