import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface NewsPreferences {
  breakingNews: boolean;
  marketNews: boolean;
  companyNews: boolean;
  earningsNews: boolean;
  cryptoNews: boolean;
  personalStocks: boolean;
  quietHours: boolean;
  quietStart: string;
  quietEnd: string;
  frequency: 'immediate' | 'hourly' | 'daily';
}

const NewsPreferencesScreen = ({ navigation }: { navigation?: any }) => {
  const [preferences, setPreferences] = useState<NewsPreferences>({
    breakingNews: true,
    marketNews: true,
    companyNews: true,
    earningsNews: false,
    cryptoNews: false,
    personalStocks: true,
    quietHours: false,
    quietStart: '22:00',
    quietEnd: '08:00',
    frequency: 'immediate',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const saved = await AsyncStorage.getItem('newsPreferences');
      if (saved) {
        setPreferences(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading news preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async (newPreferences: NewsPreferences) => {
    try {
      await AsyncStorage.setItem('newsPreferences', JSON.stringify(newPreferences));
      setPreferences(newPreferences);
    } catch (error) {
      console.error('Error saving news preferences:', error);
      Alert.alert('Error', 'Failed to save preferences');
    }
  };

  const handleToggle = (key: keyof NewsPreferences) => {
    const newPreferences = { ...preferences, [key]: !preferences[key] };
    savePreferences(newPreferences);
  };

  const handleFrequencyChange = (frequency: 'immediate' | 'hourly' | 'daily') => {
    const newPreferences = { ...preferences, frequency };
    savePreferences(newPreferences);
  };

  const handleReset = () => {
    Alert.alert(
      'Reset Preferences',
      'Are you sure you want to reset all news preferences to default?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            const defaultPreferences: NewsPreferences = {
              breakingNews: true,
              marketNews: true,
              companyNews: true,
              earningsNews: false,
              cryptoNews: false,
              personalStocks: true,
              quietHours: false,
              quietStart: '22:00',
              quietEnd: '08:00',
              frequency: 'immediate',
            };
            savePreferences(defaultPreferences);
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading preferences...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation?.goBack?.()}>
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>News Preferences</Text>
        <TouchableOpacity onPress={handleReset}>
          <Icon name="refresh-cw" size={20} color="#007AFF" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* News Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>News Types</Text>
          <Text style={styles.sectionDescription}>
            Choose which types of news you want to receive
          </Text>

          {[
            {
              key: 'breakingNews' as keyof NewsPreferences,
              title: 'Breaking News',
              description: 'Urgent market-moving news and alerts',
              icon: 'zap',
              color: '#FF3B30',
            },
            {
              key: 'marketNews' as keyof NewsPreferences,
              title: 'Market News',
              description: 'General market updates and analysis',
              icon: 'trending-up',
              color: '#34C759',
            },
            {
              key: 'companyNews' as keyof NewsPreferences,
              title: 'Company News',
              description: 'Corporate announcements and updates',
              icon: 'building',
              color: '#007AFF',
            },
            {
              key: 'earningsNews' as keyof NewsPreferences,
              title: 'Earnings News',
              description: 'Quarterly earnings reports and guidance',
              icon: 'dollar-sign',
              color: '#FF9500',
            },
            {
              key: 'cryptoNews' as keyof NewsPreferences,
              title: 'Crypto News',
              description: 'Cryptocurrency market updates',
              icon: 'bitcoin',
              color: '#AF52DE',
            },
            {
              key: 'personalStocks' as keyof NewsPreferences,
              title: 'Personal Stocks',
              description: 'News about stocks in your portfolio',
              icon: 'star',
              color: '#FFD700',
            },
          ].map((item) => (
            <View key={item.key} style={styles.preferenceItem}>
              <View style={styles.preferenceInfo}>
                <View style={[styles.preferenceIcon, { backgroundColor: item.color + '20' }]}>
                  <Icon name={item.icon} size={20} color={item.color} />
                </View>
                <View style={styles.preferenceText}>
                  <Text style={styles.preferenceTitle}>{item.title}</Text>
                  <Text style={styles.preferenceDescription}>{item.description}</Text>
                </View>
              </View>
              <Switch
                value={preferences[item.key] as boolean}
                onValueChange={() => handleToggle(item.key)}
                trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
                thumbColor="#fff"
              />
            </View>
          ))}
        </View>

        {/* Notification Frequency */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notification Frequency</Text>
          <Text style={styles.sectionDescription}>
            How often you want to receive news notifications
          </Text>

          {[
            { key: 'immediate', title: 'Immediate', description: 'Get notified as soon as news breaks' },
            { key: 'hourly', title: 'Hourly Digest', description: 'Receive a summary every hour' },
            { key: 'daily', title: 'Daily Digest', description: 'Get a daily summary of important news' },
          ].map((option) => (
            <TouchableOpacity
              key={option.key}
              style={[
                styles.frequencyOption,
                preferences.frequency === option.key && styles.frequencyOptionActive,
              ]}
              onPress={() => handleFrequencyChange(option.key as any)}
            >
              <View style={styles.frequencyInfo}>
                <Text style={[
                  styles.frequencyTitle,
                  preferences.frequency === option.key && styles.frequencyTitleActive,
                ]}>
                  {option.title}
                </Text>
                <Text style={[
                  styles.frequencyDescription,
                  preferences.frequency === option.key && styles.frequencyDescriptionActive,
                ]}>
                  {option.description}
                </Text>
              </View>
              <View style={[
                styles.radioButton,
                preferences.frequency === option.key && styles.radioButtonActive,
              ]}>
                {preferences.frequency === option.key && (
                  <View style={styles.radioButtonInner} />
                )}
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Quiet Hours */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quiet Hours</Text>
          <Text style={styles.sectionDescription}>
            Pause notifications during specific hours
          </Text>

          <View style={styles.preferenceItem}>
            <View style={styles.preferenceInfo}>
              <View style={[styles.preferenceIcon, { backgroundColor: '#8E8E93' + '20' }]}>
                <Icon name="moon" size={20} color="#8E8E93" />
              </View>
              <View style={styles.preferenceText}>
                <Text style={styles.preferenceTitle}>Enable Quiet Hours</Text>
                <Text style={styles.preferenceDescription}>
                  {preferences.quietHours 
                    ? `${preferences.quietStart} - ${preferences.quietEnd}`
                    : 'Pause notifications during sleep hours'
                  }
                </Text>
              </View>
            </View>
            <Switch
              value={preferences.quietHours}
              onValueChange={() => handleToggle('quietHours')}
              trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
              thumbColor="#fff"
            />
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity style={styles.saveButton} onPress={() => navigation?.goBack?.()}>
          <Text style={styles.saveButtonText}>Save Preferences</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748B',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E293B',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 20,
  },
  preferenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  preferenceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  preferenceIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  preferenceText: {
    flex: 1,
  },
  preferenceTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1E293B',
    marginBottom: 4,
  },
  preferenceDescription: {
    fontSize: 14,
    color: '#64748B',
  },
  frequencyOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  frequencyOptionActive: {
    borderColor: '#007AFF',
    backgroundColor: '#F0F9FF',
  },
  frequencyInfo: {
    flex: 1,
  },
  frequencyTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1E293B',
    marginBottom: 4,
  },
  frequencyTitleActive: {
    color: '#007AFF',
  },
  frequencyDescription: {
    fontSize: 14,
    color: '#64748B',
  },
  frequencyDescriptionActive: {
    color: '#007AFF',
  },
  radioButton: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioButtonActive: {
    borderColor: '#007AFF',
  },
  radioButtonInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#007AFF',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default NewsPreferencesScreen;
