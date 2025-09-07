import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import MockUserService from '../services/MockUserService';

const SearchTest: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const mockUserService = MockUserService.getInstance();

  const handleSearch = () => {
    console.log('🔍 SearchTest: Searching for:', searchTerm);
    const results = mockUserService.getDiscoverUsers(20, 0, searchTerm);
    console.log('🔍 SearchTest: Found', results.length, 'results');
    setSearchResults(results);
  };

  const clearSearch = () => {
    setSearchTerm('');
    setSearchResults([]);
  };

  const allUsers = mockUserService.getDiscoverUsers(20, 0);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🔍 Search Test</Text>
        <Text style={styles.subtitle}>
          Test the search functionality in the Discover tab
        </Text>
      </View>

      <View style={styles.searchSection}>
        <View style={styles.searchContainer}>
          <Icon name="search" size={20} color="#8E8E93" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search investors..."
            value={searchTerm}
            onChangeText={setSearchTerm}
            placeholderTextColor="#8E8E93"
          />
          {searchTerm.length > 0 && (
            <TouchableOpacity onPress={clearSearch}>
              <Icon name="x" size={20} color="#8E8E93" />
            </TouchableOpacity>
          )}
        </View>
        
        <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
          <Text style={styles.searchButtonText}>Search</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.resultsSection}>
        <Text style={styles.resultsTitle}>
          {searchTerm ? `Search Results for "${searchTerm}"` : 'All Users'}
        </Text>
        <Text style={styles.resultsCount}>
          {searchResults.length > 0 ? searchResults.length : allUsers.length} users found
        </Text>

        {(searchResults.length > 0 ? searchResults : allUsers).map((user) => (
          <View key={user.id} style={styles.userCard}>
            <View style={styles.userInfo}>
              <Text style={styles.userName}>{user.name}</Text>
              <Text style={styles.userEmail}>{user.email}</Text>
              <Text style={styles.userLevel}>
                {user.experienceLevel.charAt(0).toUpperCase()}{user.experienceLevel.slice(1)} • {user.followersCount} followers
              </Text>
            </View>
            <View style={[
              styles.followStatus,
              { backgroundColor: user.isFollowingUser ? '#E8F5E8' : '#F2F2F7' }
            ]}>
              <Text style={[
                styles.followStatusText,
                { color: user.isFollowingUser ? '#34C759' : '#8E8E93' }
              ]}>
                {user.isFollowingUser ? 'Following' : 'Not Following'}
              </Text>
            </View>
          </View>
        ))}
      </View>

      <View style={styles.testInstructions}>
        <Text style={styles.instructionsTitle}>🧪 Test Instructions:</Text>
        <View style={styles.instructionItem}>
          <Text style={styles.instructionNumber}>1</Text>
          <Text style={styles.instructionText}>Try searching for "Test" - should find "Test Investor"</Text>
        </View>
        <View style={styles.instructionItem}>
          <Text style={styles.instructionNumber}>2</Text>
          <Text style={styles.instructionText}>Try searching for "Sarah" - should find "Sarah Johnson"</Text>
        </View>
        <View style={styles.instructionItem}>
          <Text style={styles.instructionNumber}>3</Text>
          <Text style={styles.instructionText}>Try searching for "example.com" - should find multiple users</Text>
        </View>
        <View style={styles.instructionItem}>
          <Text style={styles.instructionNumber}>4</Text>
          <Text style={styles.instructionText}>Try searching for "xyz" - should find no results</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
    lineHeight: 22,
  },
  searchSection: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1C1C1E',
    marginLeft: 8,
  },
  searchButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
    alignItems: 'center',
  },
  searchButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  resultsSection: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  resultsCount: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 16,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  userEmail: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 2,
  },
  userLevel: {
    fontSize: 12,
    color: '#007AFF',
  },
  followStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  followStatusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  testInstructions: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  instructionNumber: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#007AFF',
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 20,
    marginRight: 8,
  },
  instructionText: {
    flex: 1,
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
  },
});

export default SearchTest;
