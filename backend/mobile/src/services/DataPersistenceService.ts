import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
export interface CachedData {
data: any;
timestamp: number;
expiresAt: number;
}
export interface OfflineData {
discussions: any[];
watchlists: any[];
portfolios: any[];
user: any;
lastSync: number;
}
class DataPersistenceService {
private readonly CACHE_KEYS = {
DISCUSSIONS: 'cached_discussions',
WATCHLISTS: 'cached_watchlists',
PORTFOLIOS: 'cached_portfolios',
USER_DATA: 'cached_user_data',
OFFLINE_DATA: 'offline_data',
LAST_SYNC: 'last_sync_timestamp',
};
private readonly CACHE_DURATION = {
DISCUSSIONS: 5 * 60 * 1000, // 5 minutes
WATCHLISTS: 10 * 60 * 1000, // 10 minutes
PORTFOLIOS: 15 * 60 * 1000, // 15 minutes
USER_DATA: 30 * 60 * 1000, // 30 minutes
};
/**
* Cache data with expiration
*/
public async cacheData(key: string, data: any, duration?: number): Promise<void> {
try {
const now = Date.now();
const expiresAt = now + (duration || this.CACHE_DURATION.DISCUSSIONS);
const cachedData: CachedData = {
data,
timestamp: now,
expiresAt,
};
await AsyncStorage.setItem(key, JSON.stringify(cachedData));
} catch (error) {
console.error(`Error caching data for key ${key}:`, error);
}
}
/**
* Retrieve cached data if not expired
*/
public async getCachedData(key: string): Promise<any | null> {
try {
const cachedString = await AsyncStorage.getItem(key);
if (!cachedString) {
return null;
}
const cachedData: CachedData = JSON.parse(cachedString);
const now = Date.now();
if (now > cachedData.expiresAt) {
// Data expired, remove it
await AsyncStorage.removeItem(key);
return null;
}
return cachedData.data;
} catch (error) {
console.error(`Error retrieving cached data for key ${key}:`, error);
return null;
}
}
/**
* Cache discussions data
*/
public async cacheDiscussions(discussions: any[]): Promise<void> {
await this.cacheData(
this.CACHE_KEYS.DISCUSSIONS,
discussions,
this.CACHE_DURATION.DISCUSSIONS
);
}
/**
* Get cached discussions
*/
public async getCachedDiscussions(): Promise<any[] | null> {
return await this.getCachedData(this.CACHE_KEYS.DISCUSSIONS);
}
/**
* Cache watchlists data
*/
public async cacheWatchlists(watchlists: any[]): Promise<void> {
await this.cacheData(
this.CACHE_KEYS.WATCHLISTS,
watchlists,
this.CACHE_DURATION.WATCHLISTS
);
}
/**
* Get cached watchlists
*/
public async getCachedWatchlists(): Promise<any[] | null> {
return await this.getCachedData(this.CACHE_KEYS.WATCHLISTS);
}
/**
* Cache portfolios data
*/
public async cachePortfolios(portfolios: any[]): Promise<void> {
await this.cacheData(
this.CACHE_KEYS.PORTFOLIOS,
portfolios,
this.CACHE_DURATION.PORTFOLIOS
);
}
/**
* Get cached portfolios
*/
public async getCachedPortfolios(): Promise<any[] | null> {
return await this.getCachedData(this.CACHE_KEYS.PORTFOLIOS);
}
/**
* Cache user data
*/
public async cacheUserData(user: any): Promise<void> {
await this.cacheData(
this.CACHE_KEYS.USER_DATA,
user,
this.CACHE_DURATION.USER_DATA
);
}
/**
* Get cached user data
*/
public async getCachedUserData(): Promise<any | null> {
return await this.getCachedData(this.CACHE_KEYS.USER_DATA);
}
/**
* Save data for offline use
*/
public async saveOfflineData(data: Partial<OfflineData>): Promise<void> {
try {
const existingData = await this.getOfflineData();
const offlineData: OfflineData = {
...existingData,
...data,
lastSync: Date.now(),
};
await AsyncStorage.setItem(
this.CACHE_KEYS.OFFLINE_DATA,
JSON.stringify(offlineData)
);
} catch (error) {
console.error('Error saving offline data:', error);
}
}
/**
* Get offline data
*/
public async getOfflineData(): Promise<OfflineData> {
try {
const offlineString = await AsyncStorage.getItem(this.CACHE_KEYS.OFFLINE_DATA);
if (!offlineString) {
return {
discussions: [],
watchlists: [],
portfolios: [],
user: null,
lastSync: 0,
};
}
return JSON.parse(offlineString);
} catch (error) {
console.error('Error retrieving offline data:', error);
return {
discussions: [],
watchlists: [],
portfolios: [],
user: null,
lastSync: 0,
};
}
}
/**
* Check if data is stale and needs refresh
*/
public async isDataStale(key: string, maxAge?: number): Promise<boolean> {
try {
const cachedString = await AsyncStorage.getItem(key);
if (!cachedString) {
return true; // No data means it's stale
}
const cachedData: CachedData = JSON.parse(cachedString);
const now = Date.now();
const age = now - cachedData.timestamp;
const threshold = maxAge || this.CACHE_DURATION.DISCUSSIONS;
return age > threshold;
} catch (error) {
console.error(`Error checking if data is stale for key ${key}:`, error);
return true; // Assume stale on error
}
}
/**
* Clear all cached data
*/
public async clearAllCache(): Promise<void> {
try {
const keys = Object.values(this.CACHE_KEYS);
await AsyncStorage.multiRemove(keys);
} catch (error) {
console.error('Error clearing cache:', error);
}
}
/**
* Clear specific cached data
*/
public async clearCache(key: string): Promise<void> {
try {
await AsyncStorage.removeItem(key);
} catch (error) {
console.error(`Error clearing cache for key ${key}:`, error);
}
}
/**
* Get cache statistics
*/
public async getCacheStats(): Promise<{
totalKeys: number;
totalSize: number;
keys: string[];
}> {
try {
const keys = await AsyncStorage.getAllKeys();
const cacheKeys = keys.filter(key => 
Object.values(this.CACHE_KEYS).includes(key)
);
let totalSize = 0;
for (const key of cacheKeys) {
const value = await AsyncStorage.getItem(key);
if (value) {
totalSize += value.length;
}
}
return {
totalKeys: cacheKeys.length,
totalSize,
keys: cacheKeys,
};
} catch (error) {
console.error('Error getting cache stats:', error);
return {
totalKeys: 0,
totalSize: 0,
keys: [],
};
}
}
/**
* Backup user data to local storage
*/
public async backupUserData(): Promise<void> {
try {
const userData = await this.getCachedUserData();
const discussions = await this.getCachedDiscussions();
const watchlists = await this.getCachedWatchlists();
const portfolios = await this.getCachedPortfolios();
const backupData = {
user: userData,
discussions,
watchlists,
portfolios,
timestamp: Date.now(),
};
await AsyncStorage.setItem('user_backup', JSON.stringify(backupData));
} catch (error) {
console.error('Error backing up user data:', error);
}
}
/**
* Restore user data from backup
*/
public async restoreUserData(): Promise<boolean> {
try {
const backupString = await AsyncStorage.getItem('user_backup');
if (!backupString) {
return false;
}
const backupData = JSON.parse(backupString);
// Restore cached data
if (backupData.user) {
await this.cacheUserData(backupData.user);
}
if (backupData.discussions) {
await this.cacheDiscussions(backupData.discussions);
}
if (backupData.watchlists) {
await this.cacheWatchlists(backupData.watchlists);
}
if (backupData.portfolios) {
await this.cachePortfolios(backupData.portfolios);
}
return true;
} catch (error) {
console.error('Error restoring user data:', error);
return false;
}
}
/**
* Check if user is offline and show appropriate message
*/
public async checkOfflineStatus(): Promise<boolean> {
try {
const offlineData = await this.getOfflineData();
const isOffline = offlineData.lastSync > 0 && 
(Date.now() - offlineData.lastSync) > 5 * 60 * 1000; // 5 minutes
if (isOffline) {
Alert.alert(
'Offline Mode',
'You are currently offline. Some features may not be available.',
[{ text: 'OK' }]
);
}
return isOffline;
} catch (error) {
console.error('Error checking offline status:', error);
return false;
}
}
}
// Export singleton instance
export const dataPersistenceService = new DataPersistenceService();
export default dataPersistenceService;
