import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme, CULTURAL_THEMES, ACCESSIBILITY_THEMES, PROFESSIONAL_THEMES } from '../theme/PersonalizedThemes';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

interface ThemeSettingsScreenProps {
  onClose: () => void;
}

export default function ThemeSettingsScreen({ onClose }: ThemeSettingsScreenProps) {
  const { 
    currentTheme, 
    setTheme, 
    availableThemes, 
    isDarkMode, 
    toggleDarkMode, 
    accessibilitySettings, 
    updateAccessibilitySettings 
  } = useTheme();

  const [selectedCategory, setSelectedCategory] = useState<'cultural' | 'accessibility' | 'professional'>('cultural');

  const getThemesByCategory = () => {
    switch (selectedCategory) {
      case 'cultural':
        return CULTURAL_THEMES;
      case 'accessibility':
        return ACCESSIBILITY_THEMES;
      case 'professional':
        return PROFESSIONAL_THEMES;
      default:
        return CULTURAL_THEMES;
    }
  };

  const handleThemeSelect = async (theme: any) => {
    try {
      await setTheme(theme);
      Alert.alert('Theme Updated', `Switched to ${theme.displayName} theme`);
    } catch (error) {
      Alert.alert('Error', 'Failed to update theme');
    }
  };

  const handleAccessibilityToggle = async (setting: keyof typeof accessibilitySettings, value: boolean) => {
    try {
      await updateAccessibilitySettings({ [setting]: value });
    } catch (error) {
      Alert.alert('Error', 'Failed to update accessibility settings');
    }
  };

  const handleDarkModeToggle = async () => {
    try {
      toggleDarkMode();
      Alert.alert('Theme Updated', `Switched to ${!isDarkMode ? 'dark' : 'light'} mode`);
    } catch (error) {
      Alert.alert('Error', 'Failed to toggle dark mode');
    }
  };

  const renderThemeCard = (theme: any) => {
    const isSelected = currentTheme.name === theme.name;
    
    return (
      <TouchableOpacity
        key={theme.name}
        style={[styles.themeCard, isSelected && styles.themeCardSelected]}
        onPress={() => handleThemeSelect(theme)}
      >
        <LinearGradient
          colors={[theme.colors.primary, theme.colors.secondary]}
          style={styles.themePreview}
        >
          <View style={styles.themePreviewContent}>
            <View style={[styles.themePreviewBox, { backgroundColor: theme.colors.surface }]}>
              <View style={[styles.themePreviewText, { backgroundColor: theme.colors.text }]} />
              <View style={[styles.themePreviewText, { backgroundColor: theme.colors.textSecondary, width: '60%' }]} />
            </View>
          </View>
        </LinearGradient>
        
        <View style={styles.themeInfo}>
          <Text style={styles.themeName}>{theme.displayName}</Text>
          <Text style={styles.themeDescription}>{theme.description}</Text>
          {isSelected && (
            <View style={styles.selectedIndicator}>
              <Ionicons name="checkmark-circle" size={16} color="#007AFF" />
              <Text style={styles.selectedText}>Selected</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderAccessibilitySettings = () => (
    <View style={styles.accessibilitySection}>
      <Text style={styles.sectionTitle}>Accessibility Settings</Text>
      
      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>High Contrast</Text>
          <Text style={styles.settingDescription}>Increase contrast for better visibility</Text>
        </View>
        <Switch
          value={accessibilitySettings.highContrast}
          onValueChange={(value) => handleAccessibilityToggle('highContrast', value)}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>Large Text</Text>
          <Text style={styles.settingDescription}>Increase font sizes for better readability</Text>
        </View>
        <Switch
          value={accessibilitySettings.largeText}
          onValueChange={(value) => handleAccessibilityToggle('largeText', value)}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>Reduced Motion</Text>
          <Text style={styles.settingDescription}>Minimize animations and transitions</Text>
        </View>
        <Switch
          value={accessibilitySettings.reducedMotion}
          onValueChange={(value) => handleAccessibilityToggle('reducedMotion', value)}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.settingItem}>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>Voice Navigation</Text>
          <Text style={styles.settingDescription}>Enable voice commands for navigation</Text>
        </View>
        <Switch
          value={accessibilitySettings.voiceNavigation}
          onValueChange={(value) => handleAccessibilityToggle('voiceNavigation', value)}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Ionicons name="close" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Theme Settings</Text>
        <View style={styles.headerRight}>
          <TouchableOpacity onPress={handleDarkModeToggle} style={styles.darkModeButton}>
            <Ionicons name={isDarkMode ? "sunny" : "moon"} size={20} color="#333" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Dark Mode Toggle */}
        <View style={styles.darkModeSection}>
          <View style={styles.darkModeInfo}>
            <Text style={styles.darkModeTitle}>Dark Mode</Text>
            <Text style={styles.darkModeDescription}>
              {isDarkMode ? 'Currently using dark theme' : 'Currently using light theme'}
            </Text>
          </View>
          <Switch
            value={isDarkMode}
            onValueChange={handleDarkModeToggle}
            trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
            thumbColor="#fff"
          />
        </View>

        {/* Category Tabs */}
        <View style={styles.categoryTabs}>
          {[
            { id: 'cultural', name: 'Cultural', icon: '🌍' },
            { id: 'accessibility', name: 'Accessibility', icon: '♿' },
            { id: 'professional', name: 'Professional', icon: '💼' },
          ].map((category) => (
            <TouchableOpacity
              key={category.id}
              style={[
                styles.categoryTab,
                selectedCategory === category.id && styles.categoryTabActive
              ]}
              onPress={() => setSelectedCategory(category.id as any)}
            >
              <Text style={styles.categoryIcon}>{category.icon}</Text>
              <Text style={[
                styles.categoryText,
                selectedCategory === category.id && styles.categoryTextActive
              ]}>
                {category.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Themes Grid */}
        <View style={styles.themesSection}>
          <Text style={styles.sectionTitle}>
            {selectedCategory === 'cultural' && 'Cultural Themes'}
            {selectedCategory === 'accessibility' && 'Accessibility Themes'}
            {selectedCategory === 'professional' && 'Professional Themes'}
          </Text>
          
          <View style={styles.themesGrid}>
            {getThemesByCategory().map(renderThemeCard)}
          </View>
        </View>

        {/* Accessibility Settings */}
        {selectedCategory === 'accessibility' && renderAccessibilitySettings()}

        {/* Current Theme Info */}
        <View style={styles.currentThemeSection}>
          <Text style={styles.sectionTitle}>Current Theme</Text>
          <View style={styles.currentThemeCard}>
            <LinearGradient
              colors={[currentTheme.colors.primary, currentTheme.colors.secondary]}
              style={styles.currentThemePreview}
            >
              <View style={styles.currentThemePreviewContent}>
                <View style={[styles.currentThemePreviewBox, { backgroundColor: currentTheme.colors.surface }]}>
                  <View style={[styles.currentThemePreviewText, { backgroundColor: currentTheme.colors.text }]} />
                  <View style={[styles.currentThemePreviewText, { backgroundColor: currentTheme.colors.textSecondary, width: '60%' }]} />
                </View>
              </View>
            </LinearGradient>
            
            <View style={styles.currentThemeInfo}>
              <Text style={styles.currentThemeName}>{currentTheme.displayName}</Text>
              <Text style={styles.currentThemeDescription}>{currentTheme.description}</Text>
              <Text style={styles.currentThemeCategory}>
                Category: {currentTheme.category.charAt(0).toUpperCase() + currentTheme.category.slice(1)}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  closeButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  headerRight: {
    width: 40,
  },
  darkModeButton: {
    padding: 8,
    alignSelf: 'flex-end',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  darkModeSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  darkModeInfo: {
    flex: 1,
  },
  darkModeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  darkModeDescription: {
    fontSize: 14,
    color: '#666',
  },
  categoryTabs: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  categoryTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  categoryTabActive: {
    backgroundColor: '#007AFF',
  },
  categoryIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
  },
  categoryTextActive: {
    color: 'white',
    fontWeight: '600',
  },
  themesSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  themesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  themeCard: {
    width: (width - 60) / 2,
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  themeCardSelected: {
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  themePreview: {
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
  },
  themePreviewContent: {
    width: '80%',
    height: '60%',
  },
  themePreviewBox: {
    flex: 1,
    borderRadius: 4,
    padding: 8,
    justifyContent: 'space-between',
  },
  themePreviewText: {
    height: 4,
    borderRadius: 2,
  },
  themeInfo: {
    padding: 12,
  },
  themeName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  themeDescription: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  selectedIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  selectedText: {
    fontSize: 12,
    color: '#007AFF',
    marginLeft: 4,
    fontWeight: '500',
  },
  accessibilitySection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 18,
  },
  currentThemeSection: {
    marginBottom: 20,
  },
  currentThemeCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currentThemePreview: {
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
  },
  currentThemePreviewContent: {
    width: '80%',
    height: '60%',
  },
  currentThemePreviewBox: {
    flex: 1,
    borderRadius: 6,
    padding: 12,
    justifyContent: 'space-between',
  },
  currentThemePreviewText: {
    height: 6,
    borderRadius: 3,
  },
  currentThemeInfo: {
    padding: 20,
  },
  currentThemeName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  currentThemeDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  currentThemeCategory: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
});
