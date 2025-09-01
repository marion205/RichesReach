import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface SocialNavProps {
  activeTab: string;
  onTabPress: (tab: string) => void;
}

const SocialNav: React.FC<SocialNavProps> = ({ activeTab, onTabPress }) => {
  const tabs = [
    { id: 'discussions', label: 'Discussions', icon: 'message-circle' },
    { id: 'watchlists', label: 'Watchlists', icon: 'list' },
    { id: 'portfolios', label: 'Portfolios', icon: 'trending-up' },
    { id: 'achievements', label: 'Achievements', icon: 'award' },
  ];

  return (
    <View style={styles.container}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.id}
          style={[
            styles.tab,
            activeTab === tab.id && styles.activeTab
          ]}
          onPress={() => onTabPress(tab.id)}
        >
          <Icon
            name={tab.icon as any}
            size={20}
            color={activeTab === tab.id ? '#007AFF' : '#8E8E93'}
          />
          <Text style={[
            styles.tabLabel,
            activeTab === tab.id && styles.activeTabLabel
          ]}>
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
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
    color: '#007AFF',
    fontWeight: '600',
  },
});

export default SocialNav;
