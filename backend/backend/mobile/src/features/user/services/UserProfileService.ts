import AsyncStorage from '@react-native-async-storage/async-storage';
import { UserProfile } from '../../auth/screens/OnboardingScreen';
const USER_PROFILE_KEY = 'user_profile';
const ONBOARDING_COMPLETED_KEY = 'onboarding_completed';
export interface UserPreferences {
notifications: {
marketUpdates: boolean;
learningReminders: boolean;
priceAlerts: boolean;
weeklyReports: boolean;
};
theme: 'light' | 'dark' | 'auto';
language: string;
currency: string;
}
export interface UserStats {
totalLearningTime: number; // in minutes
modulesCompleted: number;
achievements: string[];
streakDays: number;
lastActiveDate: string;
}
export interface ExtendedUserProfile extends UserProfile {
preferences: UserPreferences;
stats: UserStats;
createdAt: string;
updatedAt: string;
}
class UserProfileService {
private static instance: UserProfileService;
private currentProfile: ExtendedUserProfile | null = null;
static getInstance(): UserProfileService {
if (!UserProfileService.instance) {
UserProfileService.instance = new UserProfileService();
}
return UserProfileService.instance;
}
// Initialize default preferences
private getDefaultPreferences(): UserPreferences {
return {
notifications: {
marketUpdates: true,
learningReminders: true,
priceAlerts: false,
weeklyReports: true,
},
theme: 'light',
language: 'en',
currency: 'USD',
};
}
// Initialize default stats
private getDefaultStats(): UserStats {
return {
totalLearningTime: 0,
modulesCompleted: 0,
achievements: [],
streakDays: 0,
lastActiveDate: new Date().toISOString(),
};
}
// Save user profile
async saveProfile(profile: UserProfile): Promise<void> {
try {
const extendedProfile: ExtendedUserProfile = {
...profile,
preferences: this.getDefaultPreferences(),
stats: this.getDefaultStats(),
createdAt: new Date().toISOString(),
updatedAt: new Date().toISOString(),
};
await AsyncStorage.setItem(USER_PROFILE_KEY, JSON.stringify(extendedProfile));
this.currentProfile = extendedProfile;
} catch (error) {
console.error('Error saving user profile:', error);
throw error;
}
}
// Get user profile
async getProfile(): Promise<ExtendedUserProfile | null> {
try {
if (this.currentProfile) {
return this.currentProfile;
}
const profileData = await AsyncStorage.getItem(USER_PROFILE_KEY);
if (profileData) {
this.currentProfile = JSON.parse(profileData);
return this.currentProfile;
}
return null;
} catch (error) {
console.error('Error getting user profile:', error);
return null;
}
}
// Update profile preferences
async updatePreferences(preferences: Partial<UserPreferences>): Promise<void> {
try {
const profile = await this.getProfile();
if (profile) {
const updatedProfile = {
...profile,
preferences: { ...profile.preferences, ...preferences },
updatedAt: new Date().toISOString(),
};
await AsyncStorage.setItem(USER_PROFILE_KEY, JSON.stringify(updatedProfile));
this.currentProfile = updatedProfile;
}
} catch (error) {
console.error('Error updating preferences:', error);
throw error;
}
}
// Update user stats
async updateStats(stats: Partial<UserStats>): Promise<void> {
try {
const profile = await this.getProfile();
if (profile) {
const updatedProfile = {
...profile,
stats: { ...profile.stats, ...stats },
updatedAt: new Date().toISOString(),
};
await AsyncStorage.setItem(USER_PROFILE_KEY, JSON.stringify(updatedProfile));
this.currentProfile = updatedProfile;
}
} catch (error) {
console.error('Error updating stats:', error);
throw error;
}
}
// Mark onboarding as completed
async markOnboardingCompleted(): Promise<void> {
try {
await AsyncStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
} catch (error) {
console.error('Error marking onboarding completed:', error);
throw error;
}
}
// Check if onboarding is completed
async isOnboardingCompleted(): Promise<boolean> {
try {
const completed = await AsyncStorage.getItem(ONBOARDING_COMPLETED_KEY);
return completed === 'true';
} catch (error) {
console.error('Error checking onboarding status:', error);
return false;
}
}
// Get personalized recommendations based on profile
getPersonalizedRecommendations(profile: ExtendedUserProfile) {
const recommendations = {
learningPaths: [] as string[],
investmentSuggestions: [] as string[],
riskLevel: profile.riskTolerance,
suggestedAllocation: this.getSuggestedAllocation(profile),
nextSteps: [] as string[],
};
// Learning path recommendations based on experience
if (profile.experienceLevel === 'beginner') {
recommendations.learningPaths.push('getting-started');
recommendations.nextSteps.push('Complete the "Getting Started" learning path');
} else if (profile.experienceLevel === 'intermediate') {
recommendations.learningPaths.push('portfolio-management');
recommendations.nextSteps.push('Explore advanced portfolio management techniques');
} else {
recommendations.learningPaths.push('portfolio-management');
recommendations.nextSteps.push('Set up advanced analytics and monitoring');
}
// Investment suggestions based on goals and risk
if (profile.investmentGoals?.includes('retirement')) {
recommendations.investmentSuggestions.push('Consider a target-date fund or diversified ETF');
}
if (profile.investmentGoals?.includes('house')) {
recommendations.investmentSuggestions.push('Look into high-yield savings or short-term bonds');
}
if (profile.riskTolerance === 'aggressive' && profile.timeHorizon === 'long') {
recommendations.investmentSuggestions.push('Consider growth stocks and sector ETFs');
}
return recommendations;
}
// Get suggested asset allocation based on profile
private getSuggestedAllocation(profile: ExtendedUserProfile) {
const age = 30; // Default age, could be added to profile later
const riskMultiplier = profile.riskTolerance === 'conservative' ? 0.6 : 
profile.riskTolerance === 'moderate' ? 0.8 : 1.0;
const stockPercentage = Math.min(100 - age, 90) * riskMultiplier;
const bondPercentage = 100 - stockPercentage;
return {
stocks: Math.round(stockPercentage),
bonds: Math.round(bondPercentage),
cash: 5, // Always keep some cash
};
}
// Get user's learning progress
async getLearningProgress(): Promise<{
completedModules: string[];
currentStreak: number;
totalTimeSpent: number;
achievements: string[];
}> {
const profile = await this.getProfile();
if (!profile) {
return {
completedModules: [],
currentStreak: 0,
totalTimeSpent: 0,
achievements: [],
};
}
return {
completedModules: [], // This would be populated from learning progress
currentStreak: profile.stats.streakDays,
totalTimeSpent: profile.stats.totalLearningTime,
achievements: profile.stats.achievements,
};
}
// Update learning progress
async updateLearningProgress(moduleId: string, timeSpent: number): Promise<void> {
try {
const profile = await this.getProfile();
if (profile) {
const updatedStats = {
...profile.stats,
modulesCompleted: profile.stats.modulesCompleted + 1,
totalLearningTime: profile.stats.totalLearningTime + timeSpent,
lastActiveDate: new Date().toISOString(),
};
await this.updateStats(updatedStats);
}
} catch (error) {
console.error('Error updating learning progress:', error);
throw error;
}
}
// Clear all user data (for testing or account deletion)
async clearUserData(): Promise<void> {
try {
await AsyncStorage.removeItem(USER_PROFILE_KEY);
await AsyncStorage.removeItem(ONBOARDING_COMPLETED_KEY);
this.currentProfile = null;
} catch (error) {
console.error('Error clearing user data:', error);
throw error;
}
}
// Get user's investment style summary
getUserStyleSummary(profile: ExtendedUserProfile): string {
const experience = profile.experienceLevel;
const risk = profile.riskTolerance;
const timeframe = profile.timeHorizon;
if (experience === 'beginner' && risk === 'conservative') {
return 'Conservative Beginner - Focus on learning and low-risk investments';
} else if (experience === 'beginner' && risk === 'moderate') {
return 'Balanced Beginner - Ready to explore moderate risk investments';
} else if (experience === 'intermediate' && risk === 'aggressive') {
return 'Growth-Oriented Investor - Seeking higher returns with calculated risk';
} else if (experience === 'advanced' && risk === 'aggressive') {
return 'Sophisticated Investor - Advanced strategies and high-risk opportunities';
} else {
return 'Balanced Investor - Steady growth with moderate risk';
}
}
}
export default UserProfileService;
