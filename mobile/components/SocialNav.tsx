import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface SocialNavProps {
feedType: 'trending' | 'following' | 'discover' | 'news';
onFeedTypeChange: (type: 'trending' | 'following' | 'discover' | 'news') => void;
}
const SocialNav: React.FC<SocialNavProps> = ({ feedType, onFeedTypeChange }) => {
return (
<View style={styles.container}>
<TouchableOpacity
style={[styles.tab, feedType === 'trending' && styles.activeTab]}
onPress={() => onFeedTypeChange('trending')}
>
<Icon 
name="trending-up"
size={18} 
color={feedType === 'trending' ? '#34C759' : '#8E8E93'} 
/>
<Text 
style={[
styles.tabLabel,
feedType === 'trending' && styles.activeTabLabel
]}
numberOfLines={1}
>
Trending
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'following' && styles.activeTab]}
onPress={() => onFeedTypeChange('following')}
>
<Icon 
name="users"
size={18} 
color={feedType === 'following' ? '#34C759' : '#8E8E93'} 
/>
<Text 
style={[
styles.tabLabel,
feedType === 'following' && styles.activeTabLabel
]}
numberOfLines={1}
>
Following
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'discover' && styles.activeTab]}
onPress={() => onFeedTypeChange('discover')}
>
<Icon 
name="search"
size={18} 
color={feedType === 'discover' ? '#34C759' : '#8E8E93'} 
/>
<Text 
style={[
styles.tabLabel,
feedType === 'discover' && styles.activeTabLabel
]}
numberOfLines={1}
>
Discover
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'news' && styles.activeTab]}
onPress={() => onFeedTypeChange('news')}
>
<Icon 
name="file-text"
size={18} 
color={feedType === 'news' ? '#34C759' : '#8E8E93'} 
/>
<Text 
style={[
styles.tabLabel,
feedType === 'news' && styles.activeTabLabel
]}
numberOfLines={1}
>
News
</Text>
</TouchableOpacity>
</View>
);
};
const styles = StyleSheet.create({
container: {
flexDirection: 'row',
backgroundColor: '#FFFFFF',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
paddingHorizontal: 16,
paddingVertical: 8,
},
tab: {
flex: 1,
alignItems: 'center',
paddingVertical: 8,
paddingHorizontal: 4,
borderRadius: 8,
minWidth: 0, // Allow flex shrinking
},
activeTab: {
backgroundColor: '#F2F8FF',
},
tabLabel: {
fontSize: 11,
color: '#8E8E93',
marginTop: 2,
fontWeight: '500',
textAlign: 'center',
numberOfLines: 1,
},
activeTabLabel: {
color: '#34C759',
fontWeight: '600',
},
singleTab: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
paddingVertical: 16,
paddingHorizontal: 20,
backgroundColor: '#F8F9FA',
borderRadius: 12,
gap: 8,
},
singleTabLabel: {
fontSize: 18,
fontWeight: '600',
color: '#34C759',
},
});
export default SocialNav;
