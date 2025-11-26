import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from './EducationalTooltip';

interface ChartAnnotation {
  price: number;
  label: string;
  color: string;
  type: 'entry' | 'stop' | 'target' | 'support' | 'resistance';
  description?: string;
}

interface ChartAnnotationsProps {
  annotations: ChartAnnotation[];
  chartHeight: number;
  minPrice: number;
  maxPrice: number;
  onAnnotationPress?: (annotation: ChartAnnotation) => void;
}

export const ChartAnnotations: React.FC<ChartAnnotationsProps> = ({
  annotations,
  chartHeight,
  minPrice,
  maxPrice,
  onAnnotationPress,
}) => {
  const priceRange = maxPrice - minPrice || 1;
  const paddedMin = minPrice - priceRange * 0.1;
  const paddedMax = maxPrice + priceRange * 0.1;
  const paddedRange = paddedMax - paddedMin;
  
  const getY = (price: number) => {
    return chartHeight - ((price - paddedMin) / paddedRange) * chartHeight;
  };
  
  const getIcon = (type: string) => {
    switch (type) {
      case 'entry':
        return 'arrow-right';
      case 'stop':
        return 'alert-circle'; // Stop loss - alert icon
      case 'target':
        return 'check-circle'; // Take profit - check icon
      case 'support':
        return 'trending-down';
      case 'resistance':
        return 'trending-up';
      default:
        return 'circle';
    }
  };
  
  return (
    <View style={styles.container} pointerEvents="box-none">
      {annotations.map((annotation, index) => {
        const y = getY(annotation.price);
        const content = (
          <View
            style={[
              styles.annotation,
              {
                top: y - 12,
                borderColor: annotation.color,
                backgroundColor: `${annotation.color}15`,
              },
            ]}
          >
            <Icon 
              name={getIcon(annotation.type)} 
              size={14} 
              color={annotation.color} 
            />
            <Text 
              style={[styles.annotationLabel, { color: annotation.color }]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              {annotation.label}
            </Text>
            <Text style={styles.annotationPrice}>
              ${annotation.price.toFixed(2)}
            </Text>
          </View>
        );
        
        if (annotation.description) {
          return (
            <EducationalTooltip
              key={index}
              term={annotation.label}
              explanation={annotation.description}
              position="right"
            >
              <TouchableOpacity
                onPress={() => onAnnotationPress?.(annotation)}
                activeOpacity={0.7}
              >
                {content}
              </TouchableOpacity>
            </EducationalTooltip>
          );
        }
        
        return (
          <TouchableOpacity
            key={index}
            onPress={() => onAnnotationPress?.(annotation)}
            activeOpacity={0.7}
          >
            {content}
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  annotation: {
    position: 'absolute',
    right: 8,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1.5,
    gap: 6,
    minWidth: 120,
    maxWidth: 200,
  },
  annotationLabel: {
    fontSize: 11,
    fontWeight: '700',
    flexShrink: 0,
  },
  annotationPrice: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6B7280',
  },
});

