/**
 * Load More Button Component
 * 
 * Reusable button component for pagination "Load More" functionality.
 */

import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface LoadMoreButtonProps {
  onPress: () => void;
  loading?: boolean;
  hasMore?: boolean;
  label?: string;
  disabled?: boolean;
}

export const LoadMoreButton: React.FC<LoadMoreButtonProps> = ({
  onPress,
  loading = false,
  hasMore = false,
  label = 'Load More',
  disabled = false,
}) => {
  if (!hasMore && !loading) {
    return null;
  }

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.button, (loading || disabled) && styles.buttonDisabled]}
        onPress={onPress}
        disabled={loading || disabled}
        activeOpacity={0.7}
      >
        {loading ? (
          <>
            <ActivityIndicator size="small" color="#3B82F6" style={styles.loader} />
            <Text style={styles.buttonText}>Loading...</Text>
          </>
        ) : (
          <>
            <Text style={styles.buttonText}>{label}</Text>
            <Icon name="chevron-down" size={16} color="#3B82F6" style={styles.icon} />
          </>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    minWidth: 120,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
  loader: {
    marginRight: 8,
  },
  icon: {
    marginLeft: 8,
  },
});

