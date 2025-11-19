import React, { useState, useEffect } from 'react';
import {
View,
Text,
StyleSheet,
FlatList,
TouchableOpacity,
RefreshControl,
Linking,
Alert,
Image,
ActivityIndicator
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { SecureMarketDataService } from '../services/SecureMarketDataService';
import logger from '../../../utils/logger';
interface FinancialNewsProps {
symbol?: string; // Optional: show news for specific stock
limit?: number; // Optional: limit number of articles
}
const FinancialNews: React.FC<FinancialNewsProps> = ({ symbol, limit = 20 }) => {
const [news, setNews] = useState<MarketNews[]>([]);
const [loading, setLoading] = useState(true);
const [refreshing, setRefreshing] = useState(false);
const [error, setError] = useState<string | null>(null);
useEffect(() => {
loadNews();
}, [symbol]);
const loadNews = async () => {
try {
setLoading(true);
setError(null);
// For now, use mock news data since we're focusing on market data
// Future enhancement: Integrate with backend news API when available
const mockNews = [
{
id: '1',
title: 'Market Update: Tech Stocks Show Strong Performance',
summary: 'Technology stocks continue to lead market gains with strong earnings reports.',
source: 'Financial Times',
publishedAt: new Date().toISOString(),
url: '#',
imageUrl: null
},
{
id: '2',
title: 'Federal Reserve Maintains Current Interest Rates',
summary: 'The Fed keeps rates steady as inflation shows signs of cooling.',
source: 'Reuters',
publishedAt: new Date(Date.now() - 3600000).toISOString(),
url: '#',
imageUrl: null
},
{
id: '3',
title: 'Energy Sector Sees Volatility Amid Supply Concerns',
summary: 'Oil prices fluctuate as global supply chain issues persist.',
source: 'Bloomberg',
publishedAt: new Date(Date.now() - 7200000).toISOString(),
url: '#',
imageUrl: null
}
];
setNews(mockNews.slice(0, limit));
} catch (err) {
setError('Failed to load news');
logger.error('Error loading news:', err);
} finally {
setLoading(false);
}
};
const onRefresh = async () => {
setRefreshing(true);
await loadNews();
setRefreshing(false);
};
const openArticle = async (url: string) => {
try {
const supported = await Linking.canOpenURL(url);
if (supported) {
await Linking.openURL(url);
} else {
Alert.alert('Error', 'Cannot open this article');
}
} catch (error) {
Alert.alert('Error', 'Failed to open article');
}
};
const getSentimentColor = (sentiment: string) => {
switch (sentiment) {
case 'positive': return '#34C759';
case 'negative': return '#FF3B30';
default: return '#8E8E93';
}
};
const getSentimentIcon = (sentiment: string) => {
switch (sentiment) {
case 'positive': return 'trending-up';
case 'negative': return 'trending-down';
default: return 'minus';
}
};
const formatDate = (dateString: string) => {
const date = new Date(dateString);
const now = new Date();
const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
if (diffInHours < 1) return 'Just now';
if (diffInHours < 24) return `${diffInHours}h ago`;
if (diffInHours < 48) return 'Yesterday';
return date.toLocaleDateString();
};
const renderNewsItem = ({ item }: { item: MarketNews }) => (
<TouchableOpacity 
style={styles.newsItem} 
onPress={() => openArticle(item.url)}
activeOpacity={0.7}
>
<View style={styles.newsHeader}>
<View style={styles.newsSourceContainer}>
<Text style={styles.newsSource}>{item.source}</Text>
<View style={[styles.sentimentBadge, { backgroundColor: getSentimentColor(item.sentiment) }]}>
<Icon 
name={getSentimentIcon(item.sentiment)} 
size={12} 
color="#fff" 
/>
</View>
</View>
<Text style={styles.newsTime}>{formatDate(item.publishedAt)}</Text>
</View>
<Text style={styles.newsTitle} numberOfLines={2}>
{item.title}
</Text>
<Text style={styles.newsSummary} numberOfLines={3}>
{item.summary}
</Text>
{item.relatedSymbols && item.relatedSymbols.length > 0 && (
<View style={styles.symbolsContainer}>
{item.relatedSymbols.slice(0, 3).map((symbol, index) => (
<View key={index} style={styles.symbolBadge}>
<Text style={styles.symbolText}>{symbol}</Text>
</View>
))}
</View>
)}
<View style={styles.newsFooter}>
<Icon name="external-link" size={14} color="#007AFF" />
<Text style={styles.readMoreText}>Read full article</Text>
</View>
</TouchableOpacity>
);
if (loading && (!news || news.length === 0)) {
return (
<View style={styles.loadingContainer}>
<ActivityIndicator size="large" color="#007AFF" />
<Text style={styles.loadingText}>Loading financial news...</Text>
</View>
);
}
if (error && (!news || news.length === 0)) {
return (
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={48} color="#FF3B30" />
<Text style={styles.errorTitle}>Failed to Load News</Text>
<Text style={styles.errorMessage}>{error}</Text>
<TouchableOpacity style={styles.retryButton} onPress={loadNews}>
<Text style={styles.retryButtonText}>Try Again</Text>
</TouchableOpacity>
</View>
);
}
return (
<View style={styles.container}>
<View style={styles.header}>
<Text style={styles.headerTitle}>
{symbol ? `${symbol} News` : 'Financial News'}
</Text>
<TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
<Icon name="refresh-cw" size={20} color="#007AFF" />
</TouchableOpacity>
</View>
<FlatList
data={news}
renderItem={renderNewsItem}
keyExtractor={(item) => item.id}
refreshControl={
<RefreshControl
refreshing={refreshing}
onRefresh={onRefresh}
colors={['#007AFF']}
tintColor="#007AFF"
/>
}
showsVerticalScrollIndicator={false}
contentContainerStyle={styles.listContainer}
ListEmptyComponent={
<View style={styles.emptyContainer}>
<Icon name="newspaper" size={48} color="#8E8E93" />
<Text style={styles.emptyTitle}>No News Available</Text>
<Text style={styles.emptyMessage}>
{symbol ? `No recent news found for ${symbol}` : 'No financial news available at the moment'}
</Text>
</View>
}
/>
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
justifyContent: 'space-between',
alignItems: 'center',
padding: 16,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#e0e0e0',
},
headerTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#333',
},
refreshButton: {
padding: 8,
},
listContainer: {
padding: 16,
},
newsItem: {
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
newsHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
newsSourceContainer: {
flexDirection: 'row',
alignItems: 'center',
},
newsSource: {
fontSize: 12,
color: '#666',
fontWeight: '600',
marginRight: 8,
},
sentimentBadge: {
flexDirection: 'row',
alignItems: 'center',
paddingHorizontal: 6,
paddingVertical: 2,
borderRadius: 8,
},
newsTime: {
fontSize: 12,
color: '#999',
},
newsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#333',
lineHeight: 22,
marginBottom: 8,
},
newsSummary: {
fontSize: 14,
color: '#666',
lineHeight: 20,
marginBottom: 12,
},
symbolsContainer: {
flexDirection: 'row',
flexWrap: 'wrap',
marginBottom: 12,
},
symbolBadge: {
backgroundColor: '#E3F2FD',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 6,
marginRight: 6,
marginBottom: 4,
},
symbolText: {
fontSize: 12,
color: '#1976D2',
fontWeight: '600',
},
newsFooter: {
flexDirection: 'row',
alignItems: 'center',
},
readMoreText: {
fontSize: 14,
color: '#007AFF',
marginLeft: 4,
fontWeight: '500',
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#f8f9fa',
},
loadingText: {
marginTop: 16,
fontSize: 16,
color: '#666',
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
backgroundColor: '#f8f9fa',
padding: 32,
},
errorTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#333',
marginTop: 16,
marginBottom: 8,
},
errorMessage: {
fontSize: 14,
color: '#666',
textAlign: 'center',
marginBottom: 24,
},
retryButton: {
backgroundColor: '#007AFF',
paddingHorizontal: 24,
paddingVertical: 12,
borderRadius: 8,
},
retryButtonText: {
color: '#fff',
fontSize: 16,
fontWeight: '600',
},
emptyContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
padding: 32,
},
emptyTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#333',
marginTop: 16,
marginBottom: 8,
},
emptyMessage: {
fontSize: 14,
color: '#666',
textAlign: 'center',
},
});
export default FinancialNews;
