import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
interface SocialNavProps {
feedType: 'trending' | 'following' | 'social-feed' | 'discover' | 'news';
onFeedTypeChange: (type: 'trending' | 'following' | 'social-feed' | 'discover' | 'news') => void;
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
size={20} 
color={feedType === 'trending' ? '#34C759' : '#8E8E93'} 
/>
<Text style={[
styles.tabLabel,
feedType === 'trending' && styles.activeTabLabel
]}>
Trending
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'following' && styles.activeTab]}
onPress={() => onFeedTypeChange('following')}
>
<Icon 
name="users"
size={20} 
color={feedType === 'following' ? '#34C759' : '#8E8E93'} 
/>
<Text style={[
styles.tabLabel,
feedType === 'following' && styles.activeTabLabel
]}>
Following
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'social-feed' && styles.activeTab]}
onPress={() => onFeedTypeChange('social-feed')}
>
<Icon 
name="activity"
size={20} 
color={feedType === 'social-feed' ? '#34C759' : '#8E8E93'} 
/>
<Text style={[
styles.tabLabel,
feedType === 'social-feed' && styles.activeTabLabel
]}>
Activity
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'discover' && styles.activeTab]}
onPress={() => onFeedTypeChange('discover')}
>
<Icon 
name="search"
size={20} 
color={feedType === 'discover' ? '#34C759' : '#8E8E93'} 
/>
<Text style={[
styles.tabLabel,
feedType === 'discover' && styles.activeTabLabel
]}>
Discover
</Text>
</TouchableOpacity>
<TouchableOpacity
style={[styles.tab, feedType === 'news' && styles.activeTab]}
onPress={() => onFeedTypeChange('news')}
>
<Icon 
name="file-text"
size={20} 
color={feedType === 'news' ? '#34C759' : '#8E8E93'} 
/>
<Text style={[
styles.tabLabel,
feedType === 'news' && styles.activeTabLabel
]}>
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
paddingVertical: 12,
borderRadius: 8,
},
activeTab: {
backgroundColor: '#F2F8FF',
},
tabLabel: {
fontSize: 12,
color: '#8E8E93',
marginTop: 4,
fontWeight: '500',
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
