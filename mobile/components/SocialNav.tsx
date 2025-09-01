import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface SocialNavProps {
  // No props needed for single tab
}

const SocialNav: React.FC<SocialNavProps> = () => {

  return (
    <View style={styles.container}>
        <View style={styles.singleTab}>
          <Icon 
            name="message-circle"
            size={24} 
            color="#34C759" 
          />
          <Text style={styles.singleTabLabel}>
            Discussions
          </Text>
        </View>
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
