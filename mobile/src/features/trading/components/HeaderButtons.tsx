import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import logger from '../../../utils/logger';

interface HeaderButtonsProps {
  onRiskPress: () => void;
  onMLPress: () => void;
}

const HeaderButtonsInner: React.FC<HeaderButtonsProps> = ({ onRiskPress, onMLPress }) => {
  return (
    <View style={styles.headerRight}>
      <TouchableOpacity 
        style={[styles.pillBtn, { backgroundColor: '#EE6C4D' }]} 
        onPress={onRiskPress}
      >
        <Icon name="shield" size={14} color="#fff" style={{ marginRight: 4 }} />
        <Text style={styles.pillBtnText}>Risk</Text>
      </TouchableOpacity>
      <TouchableOpacity 
        style={[styles.pillBtn, { backgroundColor: '#9C27B0' }]} 
        onPress={onMLPress}
      >
        <Icon name="cpu" size={14} color="#fff" style={{ marginRight: 4 }} />
        <Text style={styles.pillBtnText}>ML</Text>
      </TouchableOpacity>
    </View>
  );
};

// Memoize with strict comparison - only re-render if callbacks change
export const HeaderButtons = React.memo(
  HeaderButtonsInner,
  (prev, next) =>
    prev.onRiskPress === next.onRiskPress &&
    prev.onMLPress === next.onMLPress
);

HeaderButtons.displayName = 'HeaderButtons';

const styles = StyleSheet.create({
  headerRight: {
    flexDirection: 'row',
    gap: 8,
  },
  pillBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  pillBtnText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
});

