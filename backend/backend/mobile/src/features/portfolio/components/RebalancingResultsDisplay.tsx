import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
ScrollView,
TouchableOpacity,
Alert,
Share,
Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import RebalancingStorageService, { RebalancingResult } from '../services/RebalancingStorageService';
interface RebalancingResultsDisplayProps {
onClose?: () => void;
showCloseButton?: boolean;
}
const RebalancingResultsDisplay: React.FC<RebalancingResultsDisplayProps> = ({
onClose,
showCloseButton = true,
}) => {
const [results, setResults] = useState<RebalancingResult[]>([]);
const [loading, setLoading] = useState(true);
const [stats, setStats] = useState({
totalRebalancings: 0,
successfulRebalancings: 0,
totalCost: 0,
averageCost: 0,
lastRebalancingDate: null as string | null,
});
const [selectedResult, setSelectedResult] = useState<RebalancingResult | null>(null);
const [showDetailModal, setShowDetailModal] = useState(false);
const storageService = RebalancingStorageService.getInstance();
useEffect(() => {
loadResults();
}, []);
const loadResults = async () => {
try {
setLoading(true);
const [resultsData, statsData] = await Promise.all([
storageService.getRebalancingResults(),
storageService.getRebalancingStats(),
]);
setResults(resultsData);
setStats(statsData);
} catch (error) {
console.error('Error loading rebalancing results:', error);
Alert.alert('Error', 'Failed to load rebalancing results');
} finally {
setLoading(false);
}
};
const handleClearAll = () => {
Alert.alert(
'Clear All Results',
'Are you sure you want to clear all rebalancing results? This action cannot be undone.',
[
{ text: 'Cancel', style: 'cancel' },
{
text: 'Clear All',
style: 'destructive',
onPress: async () => {
try {
await storageService.clearAllResults();
await loadResults();
Alert.alert('Success', 'All rebalancing results have been cleared');
} catch (error) {
Alert.alert('Error', 'Failed to clear results');
}
},
},
]
);
};
const handleExport = async () => {
try {
const exportText = await storageService.exportResults();
await Share.share({
message: exportText,
title: 'Rebalancing Results Export',
});
} catch (error) {
Alert.alert('Error', 'Failed to export results');
}
};
const formatDate = (timestamp: string) => {
return new Date(timestamp).toLocaleString();
};
const formatCurrency = (amount: number) => {
return `$${amount.toFixed(2)}`;
};
const getStatusColor = (success: boolean) => {
return success ? '#34C759' : '#FF3B30';
};
const getStatusIcon = (success: boolean) => {
return success ? 'check-circle' : 'x-circle';
};
if (loading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading rebalancing results...</Text>
</View>
);
}
if (results.length === 0) {
return (
<View style={styles.emptyContainer}>
<Icon name="trending-up" size={48} color="#8E8E93" />
<Text style={styles.emptyTitle}>No Rebalancing Results</Text>
<Text style={styles.emptyText}>
Run a portfolio rebalancing to see your results here
</Text>
{showCloseButton && onClose && (
<TouchableOpacity style={styles.closeButton} onPress={onClose}>
<Text style={styles.closeButtonText}>Close</Text>
</TouchableOpacity>
)}
</View>
);
}
return (
<View style={styles.container}>
{/* Header */}
<View style={styles.header}>
<View>
<Text style={styles.title}>Rebalancing Results</Text>
<Text style={styles.subtitle}>
{stats.totalRebalancings} rebalancing{stats.totalRebalancings !== 1 ? 's' : ''} performed
</Text>
</View>
{showCloseButton && onClose && (
<TouchableOpacity style={styles.closeButton} onPress={onClose}>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
)}
</View>
{/* Stats Summary */}
<View style={styles.statsContainer}>
<View style={styles.statItem}>
<Text style={styles.statValue}>{stats.successfulRebalancings}</Text>
<Text style={styles.statLabel}>Successful</Text>
</View>
<View style={styles.statItem}>
<Text style={styles.statValue}>{formatCurrency(stats.totalCost)}</Text>
<Text style={styles.statLabel}>Total Cost</Text>
</View>
<View style={styles.statItem}>
<Text style={styles.statValue}>{formatCurrency(stats.averageCost)}</Text>
<Text style={styles.statLabel}>Avg Cost</Text>
</View>
</View>
{/* Action Buttons */}
<View style={styles.actionButtons}>
<TouchableOpacity style={styles.actionButton} onPress={handleExport}>
<Icon name="share" size={16} color="#007AFF" />
<Text style={styles.actionButtonText}>Export</Text>
</TouchableOpacity>
<TouchableOpacity style={[styles.actionButton, styles.clearButton]} onPress={handleClearAll}>
<Icon name="trash-2" size={16} color="#FF3B30" />
<Text style={[styles.actionButtonText, styles.clearButtonText]}>Clear All</Text>
</TouchableOpacity>
</View>
{/* Results List */}
<ScrollView style={styles.resultsList} showsVerticalScrollIndicator={false}>
{results.map((result, index) => (
<TouchableOpacity
key={result.id}
style={styles.resultCard}
onPress={() => {
setSelectedResult(result);
setShowDetailModal(true);
}}
>
<View style={styles.resultHeader}>
<View style={styles.resultTitle}>
<Icon
name={getStatusIcon(result.success)}
size={20}
color={getStatusColor(result.success)}
/>
<Text style={styles.resultTitleText}>
Rebalancing #{results.length - index}
</Text>
</View>
<Text style={styles.resultDate}>{formatDate(result.timestamp)}</Text>
</View>
<Text style={styles.resultMessage}>{result.message}</Text>
<View style={styles.resultDetails}>
<View style={styles.resultDetailItem}>
<Text style={styles.resultDetailLabel}>Portfolio Value:</Text>
<Text style={styles.resultDetailValue}>
{formatCurrency(result.newPortfolioValue)}
</Text>
</View>
<View style={styles.resultDetailItem}>
<Text style={styles.resultDetailLabel}>Cost:</Text>
<Text style={styles.resultDetailValue}>
{formatCurrency(result.rebalanceCost)}
</Text>
</View>
<View style={styles.resultDetailItem}>
<Text style={styles.resultDetailLabel}>Trades:</Text>
<Text style={styles.resultDetailValue}>
{result.stockTrades.length}
</Text>
</View>
</View>
<View style={styles.resultFooter}>
<Text style={styles.resultFooterText}>
{result.riskTolerance} • {result.maxRebalancePercentage}% max
</Text>
<Icon name="chevron-right" size={16} color="#8E8E93" />
</View>
</TouchableOpacity>
))}
</ScrollView>
{/* Detail Modal */}
<Modal
visible={showDetailModal}
animationType="slide"
presentationStyle="pageSheet"
>
<View style={styles.modalContainer}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>Rebalancing Details</Text>
<TouchableOpacity
style={styles.modalCloseButton}
onPress={() => setShowDetailModal(false)}
>
<Icon name="x" size={24} color="#8E8E93" />
</TouchableOpacity>
</View>
{selectedResult && (
<ScrollView style={styles.modalContent}>
<View style={styles.detailSection}>
<Text style={styles.detailSectionTitle}>Overview</Text>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Date:</Text>
<Text style={styles.detailValue}>{formatDate(selectedResult.timestamp)}</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Status:</Text>
<Text style={[styles.detailValue, { color: getStatusColor(selectedResult.success) }]}>
{selectedResult.success ? 'Success' : 'Failed'}
</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Message:</Text>
<Text style={styles.detailValue}>{selectedResult.message}</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Portfolio Value:</Text>
<Text style={styles.detailValue}>{formatCurrency(selectedResult.newPortfolioValue)}</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Rebalance Cost:</Text>
<Text style={styles.detailValue}>{formatCurrency(selectedResult.rebalanceCost)}</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Risk Tolerance:</Text>
<Text style={styles.detailValue}>{selectedResult.riskTolerance}</Text>
</View>
<View style={styles.detailItem}>
<Text style={styles.detailLabel}>Max Rebalance:</Text>
<Text style={styles.detailValue}>{selectedResult.maxRebalancePercentage}%</Text>
</View>
</View>
{selectedResult.estimatedImprovement && (
<View style={styles.detailSection}>
<Text style={styles.detailSectionTitle}>Improvement</Text>
<Text style={styles.detailValue}>{selectedResult.estimatedImprovement}</Text>
</View>
)}
{selectedResult.changesMade.length > 0 && (
<View style={styles.detailSection}>
<Text style={styles.detailSectionTitle}>Sector Changes</Text>
{selectedResult.changesMade.map((change, index) => (
<Text key={index} style={styles.detailValue}>• {change}</Text>
))}
</View>
)}
{selectedResult.stockTrades.length > 0 && (
<View style={styles.detailSection}>
<Text style={styles.detailSectionTitle}>Stock Trades</Text>
{selectedResult.stockTrades.map((trade, index) => (
<View key={index} style={styles.tradeItem}>
<View style={styles.tradeHeader}>
<Text style={styles.tradeAction}>{trade.action}</Text>
<Text style={styles.tradeSymbol}>{trade.symbol}</Text>
</View>
<Text style={styles.tradeCompany}>{trade.companyName}</Text>
<View style={styles.tradeDetails}>
<Text style={styles.tradeDetail}>
{trade.shares} shares @ {formatCurrency(trade.price)}
</Text>
<Text style={styles.tradeTotal}>
Total: {formatCurrency(trade.totalValue)}
</Text>
</View>
{trade.reason && (
<Text style={styles.tradeReason}>Reason: {trade.reason}</Text>
)}
</View>
))}
</View>
)}
</ScrollView>
)}
</View>
</Modal>
</View>
);
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#F2F2F7',
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#F2F2F7',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#F2F2F7',
padding: 20,
},
emptyTitle: {
fontSize: 20,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
marginBottom: 8,
},
emptyText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
},
header: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
padding: 20,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
title: {
fontSize: 24,
fontWeight: '700',
color: '#1C1C1E',
},
subtitle: {
fontSize: 16,
color: '#8E8E93',
marginTop: 4,
},
closeButton: {
padding: 8,
},
closeButtonText: {
fontSize: 16,
color: '#007AFF',
fontWeight: '600',
},
statsContainer: {
flexDirection: 'row',
backgroundColor: '#FFFFFF',
padding: 20,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
statItem: {
flex: 1,
alignItems: 'center',
},
statValue: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
},
statLabel: {
fontSize: 14,
color: '#8E8E93',
marginTop: 4,
},
actionButtons: {
flexDirection: 'row',
padding: 20,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
actionButton: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 16,
paddingVertical: 8,
borderRadius: 8,
borderWidth: 1,
borderColor: '#007AFF',
marginRight: 12,
},
actionButtonText: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
marginLeft: 6,
},
clearButton: {
borderColor: '#FF3B30',
},
clearButtonText: {
color: '#FF3B30',
},
resultsList: {
flex: 1,
padding: 20,
},
resultCard: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 2,
},
resultHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
resultTitle: {
flexDirection: 'row',
alignItems: 'center',
},
resultTitleText: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginLeft: 8,
},
resultDate: {
fontSize: 14,
color: '#8E8E93',
},
resultMessage: {
fontSize: 14,
color: '#1C1C1E',
marginBottom: 12,
lineHeight: 20,
},
resultDetails: {
marginBottom: 12,
},
resultDetailItem: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 4,
},
resultDetailLabel: {
fontSize: 14,
color: '#8E8E93',
},
resultDetailValue: {
fontSize: 14,
color: '#1C1C1E',
fontWeight: '500',
},
resultFooter: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
},
resultFooterText: {
fontSize: 12,
color: '#8E8E93',
},
modalContainer: {
flex: 1,
backgroundColor: '#F2F2F7',
},
modalHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
padding: 20,
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
modalTitle: {
fontSize: 20,
fontWeight: '700',
color: '#1C1C1E',
},
modalCloseButton: {
padding: 8,
},
modalContent: {
flex: 1,
padding: 20,
},
detailSection: {
backgroundColor: '#FFFFFF',
borderRadius: 12,
padding: 16,
marginBottom: 16,
},
detailSectionTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 12,
},
detailItem: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 8,
},
detailLabel: {
fontSize: 14,
color: '#8E8E93',
flex: 1,
},
detailValue: {
fontSize: 14,
color: '#1C1C1E',
fontWeight: '500',
flex: 2,
textAlign: 'right',
},
tradeItem: {
backgroundColor: '#F2F2F7',
borderRadius: 8,
padding: 12,
marginBottom: 8,
},
tradeHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 4,
},
tradeAction: {
fontSize: 14,
fontWeight: '600',
color: '#1C1C1E',
},
tradeSymbol: {
fontSize: 14,
fontWeight: '600',
color: '#007AFF',
},
tradeCompany: {
fontSize: 12,
color: '#8E8E93',
marginBottom: 8,
},
tradeDetails: {
flexDirection: 'row',
justifyContent: 'space-between',
},
tradeDetail: {
fontSize: 12,
color: '#1C1C1E',
},
tradeTotal: {
fontSize: 12,
fontWeight: '600',
color: '#1C1C1E',
},
tradeReason: {
fontSize: 12,
color: '#8E8E93',
marginTop: 4,
fontStyle: 'italic',
},
});
export default RebalancingResultsDisplay;
