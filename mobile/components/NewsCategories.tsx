import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { NEWS_CATEGORIES, NewsCategory } from '../services/newsService';

interface NewsCategoriesProps {
  selectedCategory: NewsCategory;
  onCategorySelect: (category: NewsCategory) => void;
  categories: Array<{
    category: NewsCategory;
    count: number;
    label: string;
  }>;
}

const NewsCategories: React.FC<NewsCategoriesProps> = ({
  selectedCategory,
  onCategorySelect,
  categories,
}) => {
  const getCategoryIcon = (category: NewsCategory) => {
    switch (category) {
      case NEWS_CATEGORIES.ALL:
        return 'globe';
      case NEWS_CATEGORIES.MARKETS:
        return 'trending-up';
      case NEWS_CATEGORIES.TECHNOLOGY:
        return 'cpu';
      case NEWS_CATEGORIES.CRYPTO:
        return 'zap';
      case NEWS_CATEGORIES.ECONOMY:
        return 'dollar-sign';
      case NEWS_CATEGORIES.PERSONAL_FINANCE:
        return 'credit-card';
      case NEWS_CATEGORIES.INVESTING:
        return 'trending-up';
      case NEWS_CATEGORIES.REAL_ESTATE:
        return 'home';
      default:
        return 'file-text';
    }
  };

  const getCategoryColor = (category: NewsCategory) => {
    switch (category) {
      case NEWS_CATEGORIES.ALL:
        return '#34C759';
      case NEWS_CATEGORIES.MARKETS:
        return '#007AFF';
      case NEWS_CATEGORIES.TECHNOLOGY:
        return '#FF9500';
      case NEWS_CATEGORIES.CRYPTO:
        return '#FF3B30';
      case NEWS_CATEGORIES.ECONOMY:
        return '#5856D6';
      case NEWS_CATEGORIES.PERSONAL_FINANCE:
        return '#FF2D92';
      case NEWS_CATEGORIES.INVESTING:
        return '#34C759';
      case NEWS_CATEGORIES.REAL_ESTATE:
        return '#AF52DE';
      default:
        return '#8E8E93';
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>News Categories</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.categoriesContainer}
      >
        {categories && Array.isArray(categories) && categories.length > 0 ? categories.map((item) => {
          const { category, count, label } = item || {};
          if (!category || !label) return null;
          
          return (
            <TouchableOpacity
              key={category}
              style={[
                styles.categoryButton,
                selectedCategory === category && styles.categoryButtonActive,
              ]}
              onPress={() => onCategorySelect(category)}
            >
              <Icon
                name={getCategoryIcon(category)}
                size={16}
                color={selectedCategory === category ? '#FFFFFF' : getCategoryColor(category)}
              />
              <Text
                style={[
                  styles.categoryLabel,
                  selectedCategory === category && styles.categoryLabelActive,
                ]}
              >
                {label}
              </Text>
              <View style={styles.countContainer}>
                <Text
                  style={[
                    styles.countText,
                    selectedCategory === category && styles.countTextActive,
                  ]}
                >
                  {count || 0}
                </Text>
              </View>
            </TouchableOpacity>
          );
        }) : (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading categories...</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  categoriesContainer: {
    paddingHorizontal: 16,
    gap: 12,
  },
  categoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    gap: 8,
    minWidth: 100,
    justifyContent: 'center',
  },
  categoryButtonActive: {
    backgroundColor: '#34C759',
  },
  categoryLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  categoryLabelActive: {
    color: '#FFFFFF',
  },
  countContainer: {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 20,
    alignItems: 'center',
  },
  countText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  countTextActive: {
    color: '#FFFFFF',
  },
  loadingContainer: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E93',
    fontStyle: 'italic',
  },
});

export default NewsCategories;
