import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
SafeAreaView,
ScrollView,
TouchableOpacity,
TextInput,
Alert,
Modal,
FlatList,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, useMutation, gql } from '@apollo/client';
import { 
GET_MY_PORTFOLIOS, 
CREATE_PORTFOLIO,
CREATE_PORTFOLIO_HOLDING, 
UPDATE_PORTFOLIO_HOLDING, 
UPDATE_HOLDING_SHARES,
REMOVE_PORTFOLIO_HOLDING,
GET_STOCKS_FOR_PORTFOLIO 
} from '../graphql/portfolioQueries';
import MarketDataService from '../services/MarketDataService';

// ProfileScreen's query to refetch after portfolio creation
const GET_ME = gql`
query GetMe {
me {
id
name
email
profilePic
followersCount
followingCount
isFollowingUser
isFollowedByUser
hasPremiumAccess
subscriptionTier
}
}
`;
interface PortfolioManagementScreenProps {
navigateTo?: (screen: string) => void;
}
const PortfolioManagementScreen: React.FC<PortfolioManagementScreenProps> = ({ navigateTo }) => {
const [selectedPortfolio, setSelectedPortfolio] = useState<string | null>(null);
const [showAddStockModal, setShowAddStockModal] = useState(false);
const [showCreatePortfolioModal, setShowCreatePortfolioModal] = useState(false);
const [showEditHoldingModal, setShowEditHoldingModal] = useState(false);
const [showPortfolioDropdown, setShowPortfolioDropdown] = useState(false);
const [editingHolding, setEditingHolding] = useState<any>(null);
const [newPortfolioName, setNewPortfolioName] = useState('');
const [stockSearch, setStockSearch] = useState('');
const [selectedStock, setSelectedStock] = useState<any>(null);
const [shares, setShares] = useState('');
const [averagePrice, setAveragePrice] = useState('');
const [editShares, setEditShares] = useState('');
const [realTimePrices, setRealTimePrices] = useState<{ [key: string]: number }>({});
const [loadingPrices, setLoadingPrices] = useState(false);
// Queries
const { data: portfoliosData, loading: portfoliosLoading, refetch } = useQuery(GET_MY_PORTFOLIOS);
const { data: stocksData, loading: stocksLoading } = useQuery(GET_STOCKS_FOR_PORTFOLIO, {
variables: { search: stockSearch },
skip: !stockSearch || stockSearch.length < 2,
});
// Mutations
const [createPortfolio] = useMutation(CREATE_PORTFOLIO, {
  refetchQueries: [GET_MY_PORTFOLIOS, GET_ME],
  awaitRefetchQueries: true
});
const [createPortfolioHolding] = useMutation(CREATE_PORTFOLIO_HOLDING, {
  refetchQueries: [GET_MY_PORTFOLIOS, GET_ME],
  awaitRefetchQueries: true
});
const [updatePortfolioHolding] = useMutation(UPDATE_PORTFOLIO_HOLDING, {
  refetchQueries: [GET_MY_PORTFOLIOS, GET_ME],
  awaitRefetchQueries: true
});
const [updateHoldingShares] = useMutation(UPDATE_HOLDING_SHARES, {
  refetchQueries: [GET_MY_PORTFOLIOS, GET_ME],
  awaitRefetchQueries: true
});
const [removePortfolioHolding] = useMutation(REMOVE_PORTFOLIO_HOLDING, {
  refetchQueries: [GET_MY_PORTFOLIOS, GET_ME],
  awaitRefetchQueries: true
});
// Fetch real-time prices for stocks
const fetchRealTimePrices = async (stocks: any[]) => {
if (stocks.length === 0) return;
setLoadingPrices(true);
try {
const symbols = stocks.map(stock => stock.symbol);
const quotes = await MarketDataService.getMultipleQuotes(symbols);
const prices: { [key: string]: number } = {};
quotes.forEach((quote) => {
if (quote.price > 0) {
prices[quote.symbol] = quote.price;
}
});
      setRealTimePrices(prices);
    } catch (error: any) {
console.error('Failed to fetch real-time prices:', error);
} finally {
setLoadingPrices(false);
}
};
// Update real-time prices when stocks data changes
useEffect(() => {
if (stocksData?.stocks) {
fetchRealTimePrices(stocksData.stocks);
}
}, [stocksData]);
const handleCreatePortfolio = async () => {
if (!newPortfolioName.trim()) {
Alert.alert('Error', 'Please enter a portfolio name');
return;
}

try {
const result = await createPortfolio({
variables: {
portfolioName: newPortfolioName.trim()
}
});

if (result.data?.createPortfolio?.success) {
setShowCreatePortfolioModal(false);
setNewPortfolioName('');
Alert.alert('Success', result.data.createPortfolio.message);
} else {
console.error('Portfolio creation failed:', result.data?.createPortfolio);
Alert.alert('Error', result.data?.createPortfolio?.message || 'Failed to create portfolio');
}
} catch (error: any) {
console.error('Error creating portfolio:', error);
console.error('Error details:', JSON.stringify(error, null, 2));
Alert.alert('Error', `Failed to create portfolio: ${error?.message || error?.toString() || 'Unknown error'}`);
}
};
  const handleAddStock = async () => {
    if (!selectedStock || !shares || !selectedPortfolio) {
Alert.alert('Error', 'Please select a stock, enter shares, and choose a portfolio');
return;
}
try {
await createPortfolioHolding({
variables: {
stockId: selectedStock.id,
shares: parseInt(shares),
portfolioName: selectedPortfolio,
averagePrice: averagePrice ? parseFloat(averagePrice) : null,
currentPrice: realTimePrices[selectedStock.symbol] || selectedStock.currentPrice,
},
});
Alert.alert('Success', `Added ${shares} shares of ${selectedStock.symbol} to ${selectedPortfolio}`);
setShowAddStockModal(false);
setSelectedStock(null);
setShares('');
setAveragePrice('');
} catch (error: any) {
Alert.alert('Error', 'Failed to add stock to portfolio');
}
};
const handleRemoveStock = async (holdingId: string, stockSymbol: string) => {
Alert.alert(
'Remove Stock',
`Are you sure you want to remove ${stockSymbol} from this portfolio?`,
[
{ text: 'Cancel', style: 'cancel' },
{
text: 'Remove',
style: 'destructive',
onPress: async () => {
try {
await removePortfolioHolding({
variables: { holdingId },
});
Alert.alert('Success', `${stockSymbol} removed from portfolio`);
} catch (error: any) {
Alert.alert('Error', 'Failed to remove stock from portfolio');
}
},
},
]
);
};
const handleUpdateShares = async (holdingId: string, newShares: number) => {
try {
await updatePortfolioHolding({
variables: {
holdingId,
newShares,
},
});
Alert.alert('Success', 'Shares updated successfully');
} catch (error: any) {
Alert.alert('Error', 'Failed to update shares');
}
};
const handleEditHolding = (holding: any) => {
setEditingHolding(holding);
setEditShares(holding.shares.toString());
setShowEditHoldingModal(true);
};
const handleSaveEdit = async () => {
if (!editingHolding || !editShares) {
Alert.alert('Error', 'Please enter a valid number of shares');
return;
}
try {
await updateHoldingShares({
variables: {
holdingId: editingHolding.id,
newShares: parseInt(editShares),
},
});
Alert.alert('Success', 'Shares updated successfully');
setShowEditHoldingModal(false);
setEditingHolding(null);
setEditShares('');
} catch (error: any) {
Alert.alert('Error', 'Failed to update shares');
}
};
const renderStockItem = ({ item }: { item: any }) => (
<TouchableOpacity
style={styles.stockItem}
onPress={() => setSelectedStock(item)}
>
<View style={styles.stockInfo}>
<Text style={styles.stockSymbol}>{item.symbol}</Text>
<Text style={styles.stockName}>{item.companyName}</Text>
</View>
<View style={styles.priceContainer}>
<Text style={styles.stockPrice}>
${realTimePrices[item.symbol] ? realTimePrices[item.symbol].toFixed(2) : item.currentPrice}
</Text>
{realTimePrices[item.symbol] && (
<Text style={styles.livePriceIndicator}>Live</Text>
)}
</View>
</TouchableOpacity>
);
const renderPortfolio = (portfolio: any) => (
<View key={portfolio.name || `portfolio-${portfolio.id || Math.random()}`} style={styles.portfolioCard}>
<View style={styles.portfolioHeader}>
<Text style={styles.portfolioName}>{portfolio.name}</Text>
<Text style={styles.portfolioValue}>${portfolio.totalValue ? portfolio.totalValue.toLocaleString() : '0.00'}</Text>
</View>
<Text style={styles.portfolioStats}>{portfolio.holdingsCount} holdings</Text>
{portfolio.holdings && portfolio.holdings.length > 0 && (
<View style={styles.holdingsList}>
{portfolio.holdings.map((holding: any, index: number) => (
<View key={holding.id || `holding-${index}`} style={styles.holdingItem}>
<View style={styles.holdingInfo}>
<Text style={styles.stockSymbol}>{holding.stock.symbol}</Text>
<Text style={styles.stockName}>{holding.stock.companyName}</Text>
<Text style={styles.sharesText}>{holding.shares} shares</Text>
</View>
<View style={styles.holdingActions}>
<Text style={styles.holdingValue}>
${holding.totalValue ? holding.totalValue.toLocaleString() : '0.00'}
</Text>
<View style={styles.actionButtons}>
<TouchableOpacity
style={styles.editButton}
onPress={() => handleEditHolding(holding)}
>
<Icon name="edit-2" size={16} color="#007AFF" />
</TouchableOpacity>
<TouchableOpacity
style={styles.removeButton}
onPress={() => handleRemoveStock(holding.id, holding.stock.symbol)}
>
<Icon name="trash-2" size={16} color="#FF3B30" />
</TouchableOpacity>
</View>
</View>
</View>
))}
</View>
)}
<TouchableOpacity
style={styles.addStockButton}
                onPress={() => {
                  setSelectedPortfolio(portfolio.name);
setShowAddStockModal(true);
}}
>
<Icon name="plus" size={16} color="#007AFF" />
<Text style={styles.addStockButtonText}>Add Stock</Text>
</TouchableOpacity>
</View>
);
return (
<SafeAreaView style={styles.container}>
<View style={styles.header}>
<TouchableOpacity onPress={() => navigateTo?.('profile')}>
<Icon name="arrow-left" size={24} color="#1C1C1E" />
</TouchableOpacity>
<Text style={styles.headerTitle}>Portfolio Management</Text>
<TouchableOpacity onPress={() => setShowCreatePortfolioModal(true)}>
<Icon name="plus" size={24} color="#007AFF" />
</TouchableOpacity>
</View>
<ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
{portfoliosLoading ? (
<View style={styles.loadingContainer}>
<Icon name="refresh-cw" size={24} color="#C7C7CC" style={styles.spinningIcon} />
<Text style={styles.loadingText}>Loading portfolios...</Text>
</View>
) : portfoliosData?.myPortfolios?.portfolios && portfoliosData.myPortfolios.portfolios.length > 0 ? (
portfoliosData.myPortfolios.portfolios.map(renderPortfolio)
) : (
<View style={styles.emptyContainer}>
<Icon name="briefcase" size={64} color="#C7C7CC" />
<Text style={styles.emptyTitle}>No Portfolios Yet</Text>
<Text style={styles.emptySubtitle}>
Create your first portfolio to start managing your investments
</Text>
<TouchableOpacity
style={styles.createFirstButton}
onPress={() => setShowCreatePortfolioModal(true)}
>
<Icon name="plus" size={20} color="#fff" />
<Text style={styles.createFirstButtonText}>Create Portfolio</Text>
</TouchableOpacity>
</View>
)}
</ScrollView>
{/* Create Portfolio Modal */}
<Modal
visible={showCreatePortfolioModal}
animationType="slide"
presentationStyle="pageSheet"
>
<SafeAreaView style={styles.modalContainer}>
<View style={styles.modalHeader}>
<TouchableOpacity onPress={() => setShowCreatePortfolioModal(false)}>
<Text style={styles.cancelButton}>Cancel</Text>
</TouchableOpacity>
<Text style={styles.modalTitle}>Create Portfolio</Text>
<TouchableOpacity 
onPress={handleCreatePortfolio}
style={styles.createButtonContainer}
>
<Text style={styles.saveButton}>Create</Text>
</TouchableOpacity>
</View>
<View style={styles.modalContent}>
<Text style={styles.inputLabel}>Portfolio Name</Text>
<TextInput
style={styles.textInput}
value={newPortfolioName}
onChangeText={setNewPortfolioName}
placeholder="e.g., Growth Portfolio"
autoFocus
/>
</View>
</SafeAreaView>
</Modal>
{/* Add Stock Modal */}
<Modal
visible={showAddStockModal}
animationType="slide"
presentationStyle="pageSheet"
>
<SafeAreaView style={styles.modalContainer}>
<View style={styles.modalHeader}>
<TouchableOpacity onPress={() => setShowAddStockModal(false)}>
<Text style={styles.cancelButton}>Cancel</Text>
</TouchableOpacity>
<Text style={styles.modalTitle}>Add Stock to {selectedPortfolio || 'Unknown Portfolio'}</Text>
<TouchableOpacity onPress={handleAddStock}>
<Text style={styles.saveButton}>Add</Text>
</TouchableOpacity>
</View>
<View style={styles.modalContent}>
{/* Portfolio Selection */}
<Text style={styles.inputLabel}>Select Portfolio</Text>
<View style={styles.dropdownContainer}>
<TouchableOpacity 
style={styles.dropdownButton}
onPress={() => setShowPortfolioDropdown(!showPortfolioDropdown)}
>
<Text style={styles.dropdownText}>
{selectedPortfolio || 'Select a portfolio...'}
</Text>
<Icon name={showPortfolioDropdown ? "chevron-up" : "chevron-down"} size={20} color="#666" />
</TouchableOpacity>

{/* Portfolio Dropdown List */}
{showPortfolioDropdown && portfoliosData?.myPortfolios?.portfolios && (
<View style={styles.dropdownList}>
{portfoliosData.myPortfolios.portfolios.map((portfolio: any, index: number) => (
<TouchableOpacity
key={portfolio.name || `portfolio-${index}`}
style={styles.dropdownItem}
onPress={() => {
setSelectedPortfolio(portfolio.name);
setShowPortfolioDropdown(false);
}}
>
<Text style={styles.dropdownItemText}>{portfolio.name}</Text>
</TouchableOpacity>
))}
</View>
)}
</View>

<Text style={styles.inputLabel}>Search Stock</Text>
<TextInput
style={styles.textInput}
value={stockSearch}
onChangeText={setStockSearch}
placeholder="Enter stock symbol or company name"
/>
{selectedStock && (
<View style={styles.selectedStock}>
<Text style={styles.selectedStockText}>
Selected: {selectedStock.symbol} - {selectedStock.companyName}
</Text>
</View>
)}
{stocksData?.stocks && (
<FlatList
data={stocksData.stocks}
renderItem={renderStockItem}
keyExtractor={(item) => item.id}
style={styles.stocksList}
/>
)}
<Text style={styles.inputLabel}>Number of Shares</Text>
<TextInput
style={styles.textInput}
value={shares}
onChangeText={setShares}
placeholder="Enter number of shares"
keyboardType="numeric"
/>
<Text style={styles.inputLabel}>Average Price (Optional)</Text>
<TextInput
style={styles.textInput}
value={averagePrice}
onChangeText={setAveragePrice}
placeholder="Enter average purchase price"
keyboardType="numeric"
/>
</View>
</SafeAreaView>
</Modal>
{/* Edit Holding Modal */}
<Modal
visible={showEditHoldingModal}
animationType="slide"
presentationStyle="pageSheet"
>
<SafeAreaView style={styles.modalContainer}>
<View style={styles.modalHeader}>
<TouchableOpacity onPress={() => setShowEditHoldingModal(false)}>
<Text style={styles.cancelButton}>Cancel</Text>
</TouchableOpacity>
<Text style={styles.modalTitle}>Edit Holding</Text>
<TouchableOpacity onPress={handleSaveEdit}>
<Text style={styles.saveButton}>Save</Text>
</TouchableOpacity>
</View>
<View style={styles.modalContent}>
{editingHolding && (
<>
<View style={styles.selectedStock}>
<Text style={styles.selectedStockText}>
{editingHolding.stock.symbol} - {editingHolding.stock.companyName}
</Text>
</View>
<Text style={styles.inputLabel}>Number of Shares</Text>
<TextInput
style={styles.textInput}
value={editShares}
onChangeText={setEditShares}
placeholder="Enter number of shares"
keyboardType="numeric"
autoFocus
/>
<Text style={styles.inputLabel}>Current Value</Text>
<Text style={styles.currentValueText}>
${editingHolding.totalValue ? editingHolding.totalValue.toLocaleString() : '0.00'}
</Text>
</>
)}
</View>
</SafeAreaView>
</Modal>
</SafeAreaView>
);
};
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
paddingVertical: 12,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
headerTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
},
content: {
flex: 1,
padding: 16,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
paddingVertical: 40,
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
marginTop: 12,
},
spinningIcon: {
transform: [{ rotate: '0deg' }],
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
paddingVertical: 60,
},
emptyTitle: {
fontSize: 24,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 16,
},
emptySubtitle: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
marginTop: 8,
marginBottom: 32,
paddingHorizontal: 32,
},
createFirstButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#007AFF',
paddingHorizontal: 24,
paddingVertical: 12,
borderRadius: 8,
},
createFirstButtonText: {
color: '#fff',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
portfolioCard: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
portfolioHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
portfolioName: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
},
portfolioValue: {
fontSize: 16,
fontWeight: '700',
color: '#34C759',
},
portfolioStats: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 16,
},
holdingsList: {
marginBottom: 16,
},
holdingItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 12,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
holdingInfo: {
flex: 1,
},
stockSymbol: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
},
stockName: {
fontSize: 14,
color: '#8E8E93',
marginTop: 2,
},
sharesText: {
fontSize: 12,
color: '#8E8E93',
marginTop: 2,
},
holdingActions: {
flexDirection: 'row',
alignItems: 'center',
},
holdingValue: {
fontSize: 14,
fontWeight: '600',
color: '#34C759',
marginRight: 12,
},
actionButtons: {
flexDirection: 'row',
alignItems: 'center',
},
editButton: {
padding: 8,
marginRight: -8,
},
removeButton: {
padding: 8,
},
currentValueText: {
fontSize: 16,
fontWeight: '600',
color: '#34C759',
backgroundColor: '#F2F2F7',
padding: 12,
borderRadius: 8,
textAlign: 'center',
},
addStockButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#F2F2F7',
paddingVertical: 12,
borderRadius: 8,
},
addStockButtonText: {
color: '#007AFF',
fontSize: 16,
fontWeight: '500',
marginLeft: 8,
},
modalContainer: {
flex: 1,
backgroundColor: '#F2F2F7',
},
modalHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 16,
paddingVertical: 12,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
modalTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
},
cancelButton: {
fontSize: 16,
color: '#8E8E93',
},
saveButton: {
fontSize: 16,
color: '#007AFF',
fontWeight: '600',
},
createButtonContainer: {
paddingHorizontal: 8,
paddingVertical: 4,
},
modalContent: {
flex: 1,
padding: 16,
},
inputLabel: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 8,
marginTop: 16,
},
textInput: {
backgroundColor: '#fff',
borderRadius: 8,
paddingHorizontal: 16,
paddingVertical: 12,
fontSize: 16,
borderWidth: 1,
borderColor: '#E5E5EA',
},
selectedStock: {
backgroundColor: '#E3F2FD',
padding: 12,
borderRadius: 8,
marginVertical: 12,
},
selectedStockText: {
fontSize: 14,
color: '#1976D2',
fontWeight: '500',
},
stocksList: {
maxHeight: 200,
backgroundColor: '#fff',
borderRadius: 8,
marginVertical: 12,
},
stockItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 16,
paddingVertical: 12,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
stockInfo: {
flex: 1,
},
priceContainer: {
alignItems: 'flex-end',
},
stockPrice: {
fontSize: 14,
fontWeight: '600',
color: '#34C759',
},
livePriceIndicator: {
fontSize: 10,
fontWeight: '600',
color: '#34C759',
backgroundColor: '#E8F5E8',
paddingHorizontal: 4,
paddingVertical: 2,
borderRadius: 4,
textAlign: 'center',
marginTop: 2,
},
// Dropdown styles
dropdownContainer: {
marginBottom: 16,
position: 'relative',
zIndex: 1000,
},
dropdownButton: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
backgroundColor: '#fff',
borderWidth: 1,
borderColor: '#E5E5EA',
borderRadius: 8,
paddingHorizontal: 12,
paddingVertical: 12,
},
dropdownText: {
fontSize: 16,
color: '#1C1C1E',
},
dropdownList: {
position: 'absolute',
top: '100%',
left: 0,
right: 0,
backgroundColor: '#fff',
borderWidth: 1,
borderColor: '#E5E5EA',
borderRadius: 8,
marginTop: 4,
maxHeight: 200,
zIndex: 1001,
},
dropdownItem: {
paddingHorizontal: 12,
paddingVertical: 12,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
dropdownItemText: {
fontSize: 16,
color: '#1C1C1E',
},
});
export default PortfolioManagementScreen;
