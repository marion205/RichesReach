import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Modal,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { NEWS_CATEGORIES, NewsCategory } from '../services/newsService';
import newsService from '../services/newsService';

interface NewsPreferencesProps {
  visible: boolean;
  onClose: () => void;
  onPreferencesUpdated: () => void;
}

const NewsPreferences: React.FC<NewsPreferencesProps> = ({
  visible,
  onClose,
  onPreferencesUpdated,
}) => {
  const [selectedCategories, setSelectedCategories] = useState<NewsCategory[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [newSource, setNewSource] = useState('');

  useEffect(() => {
    if (visible) {
      loadPreferences();
    }
  }, [visible]);

  const loadPreferences = async () => {
    const prefs = newsService.getPreferences();
    setSelectedCategories(prefs.categories);
    setKeywords(prefs.keywords);
    setSources(prefs.sources);
  };

  const toggleCategory = (category: NewsCategory) => {
    if (category === NEWS_CATEGORIES.ALL) {
      setSelectedCategories([NEWS_CATEGORIES.ALL]);
    } else {
      setSelectedCategories(prev => {
        const withoutAll = prev.filter(c => c !== NEWS_CATEGORIES.ALL);
        if (prev.includes(category)) {
          const newCategories = withoutAll.filter(c => c !== category);
          return newCategories.length === 0 ? [NEWS_CATEGORIES.ALL] : newCategories;
        } else {
          return [...withoutAll, category];
        }
      });
    }
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !keywords.includes(newKeyword.trim())) {
      setKeywords(prev => [...prev, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setKeywords(prev => prev.filter(k => k !== keyword));
  };

  const addSource = () => {
    if (newSource.trim() && !sources.includes(newSource.trim())) {
      setSources(prev => [...prev, newSource.trim()]);
      setNewSource('');
    }
  };

  const removeSource = (source: string) => {
    setSources(prev => prev.filter(s => s !== source));
  };

  const savePreferences = async () => {
    try {
      await newsService.updatePreferences({
        categories: selectedCategories,
        keywords,
        sources,
      });
      
      Alert.alert('Success', 'News preferences updated successfully!');
      onPreferencesUpdated();
      onClose();
    } catch (error) {
      Alert.alert('Error', 'Failed to update preferences. Please try again.');
    }
  };

  const resetPreferences = () => {
    Alert.alert(
      'Reset Preferences',
      'Are you sure you want to reset all news preferences?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            setSelectedCategories([NEWS_CATEGORIES.ALL]);
            setKeywords([]);
            setSources([]);
          },
        },
      ]
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>News Preferences</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Categories Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Categories</Text>
            <Text style={styles.sectionDescription}>
              Choose which types of news you want to see
            </Text>
            <View style={styles.categoriesGrid}>
              {Object.entries(NEWS_CATEGORIES).map(([key, category]) => (
                <TouchableOpacity
                  key={category}
                  style={[
                    styles.categoryChip,
                    selectedCategories.includes(category) && styles.categoryChipActive,
                  ]}
                  onPress={() => toggleCategory(category)}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      selectedCategories.includes(category) && styles.categoryChipTextActive,
                    ]}
                  >
                    {key.replace(/_/g, ' ')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Keywords Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Keywords</Text>
            <Text style={styles.sectionDescription}>
              Add keywords to filter news by specific topics
            </Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.textInput}
                value={newKeyword}
                onChangeText={setNewKeyword}
                placeholder="Enter keyword (e.g., Tesla, AI, Bitcoin)"
                onSubmitEditing={addKeyword}
              />
              <TouchableOpacity style={styles.addButton} onPress={addKeyword}>
                <Icon name="plus" size={20} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            <View style={styles.tagsContainer}>
              {keywords.map((keyword, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>{keyword}</Text>
                  <TouchableOpacity
                    onPress={() => removeKeyword(keyword)}
                    style={styles.removeTagButton}
                  >
                    <Icon name="x" size={14} color="#FF3B30" />
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          </View>

          {/* Sources Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>News Sources</Text>
            <Text style={styles.sectionDescription}>
              Add preferred news sources
            </Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.textInput}
                value={newSource}
                onChangeText={setNewSource}
                placeholder="Enter source name (e.g., Reuters, Bloomberg)"
                onSubmitEditing={addSource}
              />
              <TouchableOpacity style={styles.addButton} onPress={addSource}>
                <Icon name="plus" size={20} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            <View style={styles.tagsContainer}>
              {sources.map((source, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>{source}</Text>
                  <TouchableOpacity
                    onPress={() => removeSource(source)}
                    style={styles.removeTagButton}
                  >
                    <Icon name="x" size={14} color="#FF3B30" />
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={styles.resetButton} onPress={resetPreferences}>
              <Icon name="refresh-cw" size={16} color="#FF3B30" />
              <Text style={styles.resetButtonText}>Reset All</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.saveButton} onPress={savePreferences}>
              <Icon name="check" size={16} color="#FFFFFF" />
              <Text style={styles.saveButtonText}>Save Preferences</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    </Modal>
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
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 16,
    lineHeight: 20,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  categoryChip: {
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  categoryChipActive: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  categoryChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  categoryChipTextActive: {
    color: '#FFFFFF',
  },
  inputContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  textInput: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
  },
  addButton: {
    backgroundColor: '#34C759',
    width: 44,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    gap: 8,
  },
  tagText: {
    fontSize: 14,
    color: '#1C1C1E',
  },
  removeTagButton: {
    padding: 2,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 20,
    marginBottom: 40,
  },
  resetButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#FF3B30',
    borderRadius: 12,
    paddingVertical: 16,
    gap: 8,
  },
  resetButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
  },
  saveButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#34C759',
    borderRadius: 12,
    paddingVertical: 16,
    gap: 8,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default NewsPreferences;
