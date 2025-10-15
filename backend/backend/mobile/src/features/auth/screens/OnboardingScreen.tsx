import React, { useState } from 'react';
import {
View,
Text,
StyleSheet,
TouchableOpacity,
ScrollView,
Dimensions,
SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
const { width, height } = Dimensions.get('window');
export interface UserProfile {
experienceLevel: 'beginner' | 'intermediate' | 'advanced';
investmentGoals: string[];
riskTolerance: 'conservative' | 'moderate' | 'aggressive';
timeHorizon: 'short' | 'medium' | 'long';
monthlyInvestment: number;
interests: string[];
}
interface OnboardingScreenProps {
onComplete: (profile: UserProfile) => void;
}
const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
const [currentStep, setCurrentStep] = useState(0);
const [profile, setProfile] = useState<Partial<UserProfile>>({});
const steps = [
{
id: 'welcome',
title: 'Welcome to RichesReach',
subtitle: 'Your personal investment journey starts here',
component: WelcomeStep,
},
{
id: 'experience',
title: 'What\'s your investment experience?',
subtitle: 'This helps us personalize your learning path',
component: ExperienceStep,
},
{
id: 'goals',
title: 'What are your investment goals?',
subtitle: 'Select all that apply',
component: GoalsStep,
},
{
id: 'risk',
title: 'How comfortable are you with risk?',
subtitle: 'This helps us recommend suitable investments',
component: RiskStep,
},
{
id: 'timeframe',
title: 'What\'s your investment timeframe?',
subtitle: 'How long do you plan to invest?',
component: TimeframeStep,
},
{
id: 'budget',
title: 'How much can you invest monthly?',
subtitle: 'This helps us suggest realistic strategies',
component: BudgetStep,
},
{
id: 'interests',
title: 'What interests you most?',
subtitle: 'Select topics you\'d like to learn about',
component: InterestsStep,
},
{
id: 'complete',
title: 'You\'re all set!',
subtitle: 'Let\'s start your investment journey',
component: CompleteStep,
},
];
const handleNext = () => {
if (currentStep < steps.length - 1) {
setCurrentStep(currentStep + 1);
} else {
onComplete(profile as UserProfile);
}
};
const handleBack = () => {
if (currentStep > 0) {
setCurrentStep(currentStep - 1);
}
};
const updateProfile = (updates: Partial<UserProfile>) => {
setProfile(prev => ({ ...prev, ...updates }));
};
const CurrentStepComponent = steps[currentStep].component;
return (
<SafeAreaView style={styles.container}>
<View style={styles.header}>
<View style={styles.progressBar}>
<View 
style={[
styles.progressFill, 
{ width: `${((currentStep + 1) / steps.length) * 100}%` }
]} 
/>
</View>
<Text style={styles.stepCounter}>
{currentStep + 1} of {steps.length}
</Text>
</View>
<ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
<View style={styles.stepContainer}>
<Text style={styles.title}>{steps[currentStep].title}</Text>
<Text style={styles.subtitle}>{steps[currentStep].subtitle}</Text>
<CurrentStepComponent
profile={profile}
updateProfile={updateProfile}
onNext={handleNext}
onBack={handleBack}
/>
</View>
</ScrollView>
<View style={styles.footer}>
{currentStep > 0 && (
<TouchableOpacity style={styles.backButton} onPress={handleBack}>
<Icon name="arrow-left" size={20} color="#007AFF" />
<Text style={styles.backButtonText}>Back</Text>
</TouchableOpacity>
)}
<TouchableOpacity 
style={[
styles.nextButton, 
!isStepComplete(currentStep, profile) && styles.nextButtonDisabled
]} 
onPress={handleNext}
disabled={!isStepComplete(currentStep, profile)}
>
<Text style={styles.nextButtonText}>
{currentStep === steps.length - 1 ? 'Get Started' : 'Next'}
</Text>
<Icon name="arrow-right" size={20} color="#FFFFFF" />
</TouchableOpacity>
</View>
</SafeAreaView>
);
};
// Welcome Step
const WelcomeStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ onNext }) => (
<View style={styles.welcomeContainer}>
<View style={styles.welcomeIcon}>
<Icon name="trending-up" size={60} color="#007AFF" />
</View>
<Text style={styles.welcomeText}>
We'll help you build wealth through smart investing, no matter your experience level.
</Text>
<Text style={styles.welcomeSubtext}>
Let's create your personalized investment plan in just a few minutes.
</Text>
</View>
);
// Experience Step
const ExperienceStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const options = [
{
id: 'beginner',
title: 'Beginner',
description: 'New to investing, want to learn the basics',
icon: 'book-open',
color: '#34C759',
},
{
id: 'intermediate',
title: 'Intermediate',
description: 'Some experience, ready to expand knowledge',
icon: 'trending-up',
color: '#007AFF',
},
{
id: 'advanced',
title: 'Advanced',
description: 'Experienced investor, want advanced tools',
icon: 'bar-chart-2',
color: '#FF9500',
},
];
return (
<View style={styles.optionsContainer}>
{options.map((option) => (
<TouchableOpacity
key={option.id}
style={[
styles.optionCard,
profile.experienceLevel === option.id && styles.optionCardSelected,
]}
onPress={() => updateProfile({ experienceLevel: option.id as any })}
>
<View style={[styles.optionIcon, { backgroundColor: option.color }]}>
<Icon name={option.icon} size={24} color="#FFFFFF" />
</View>
<View style={styles.optionContent}>
<Text style={styles.optionTitle}>{option.title}</Text>
<Text style={styles.optionDescription}>{option.description}</Text>
</View>
{profile.experienceLevel === option.id && (
<Icon name="check-circle" size={24} color="#34C759" />
)}
</TouchableOpacity>
))}
</View>
);
};
// Goals Step
const GoalsStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const goals = [
{ id: 'retirement', title: 'Retirement Planning', icon: 'clock' },
{ id: 'house', title: 'Buy a Home', icon: 'home' },
{ id: 'education', title: 'Education Fund', icon: 'book' },
{ id: 'emergency', title: 'Emergency Fund', icon: 'shield' },
{ id: 'wealth', title: 'Build Wealth', icon: 'trending-up' },
{ id: 'passive', title: 'Passive Income', icon: 'dollar-sign' },
];
const toggleGoal = (goalId: string) => {
const currentGoals = profile.investmentGoals || [];
const updatedGoals = currentGoals.includes(goalId)
? currentGoals.filter(id => id !== goalId)
: [...currentGoals, goalId];
updateProfile({ investmentGoals: updatedGoals });
};
return (
<View style={styles.goalsContainer}>
{goals.map((goal) => (
<TouchableOpacity
key={goal.id}
style={[
styles.goalCard,
profile.investmentGoals?.includes(goal.id) && styles.goalCardSelected,
]}
onPress={() => toggleGoal(goal.id)}
>
<Icon 
name={goal.icon} 
size={20} 
color={profile.investmentGoals?.includes(goal.id) ? '#007AFF' : '#8E8E93'} 
/>
<Text style={[
styles.goalText,
profile.investmentGoals?.includes(goal.id) && styles.goalTextSelected,
]}>
{goal.title}
</Text>
{profile.investmentGoals?.includes(goal.id) && (
<Icon name="check" size={16} color="#007AFF" />
)}
</TouchableOpacity>
))}
</View>
);
};
// Risk Step
const RiskStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const riskLevels = [
{
id: 'conservative',
title: 'Conservative',
description: 'I prefer stable, low-risk investments',
color: '#34C759',
allocation: '80% Bonds, 20% Stocks',
},
{
id: 'moderate',
title: 'Moderate',
description: 'I want a balanced approach to risk',
color: '#FF9500',
allocation: '60% Stocks, 40% Bonds',
},
{
id: 'aggressive',
title: 'Aggressive',
description: 'I\'m comfortable with higher risk for higher returns',
color: '#FF3B30',
allocation: '80% Stocks, 20% Bonds',
},
];
return (
<View style={styles.optionsContainer}>
{riskLevels.map((level) => (
<TouchableOpacity
key={level.id}
style={[
styles.riskCard,
profile.riskTolerance === level.id && styles.riskCardSelected,
]}
onPress={() => updateProfile({ riskTolerance: level.id as any })}
>
<View style={styles.riskHeader}>
<View style={[styles.riskIndicator, { backgroundColor: level.color }]} />
<Text style={styles.riskTitle}>{level.title}</Text>
</View>
<Text style={styles.riskDescription}>{level.description}</Text>
<Text style={styles.riskAllocation}>{level.allocation}</Text>
{profile.riskTolerance === level.id && (
<Icon name="check-circle" size={24} color="#34C759" style={styles.riskCheck} />
)}
</TouchableOpacity>
))}
</View>
);
};
// Timeframe Step
const TimeframeStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const timeframes = [
{
id: 'short',
title: 'Short Term',
description: '1-3 years',
icon: 'clock',
color: '#FF3B30',
},
{
id: 'medium',
title: 'Medium Term',
description: '3-10 years',
icon: 'calendar',
color: '#FF9500',
},
{
id: 'long',
title: 'Long Term',
description: '10+ years',
icon: 'target',
color: '#34C759',
},
];
return (
<View style={styles.optionsContainer}>
{timeframes.map((timeframe) => (
<TouchableOpacity
key={timeframe.id}
style={[
styles.optionCard,
profile.timeHorizon === timeframe.id && styles.optionCardSelected,
]}
onPress={() => updateProfile({ timeHorizon: timeframe.id as any })}
>
<View style={[styles.optionIcon, { backgroundColor: timeframe.color }]}>
<Icon name={timeframe.icon} size={24} color="#FFFFFF" />
</View>
<View style={styles.optionContent}>
<Text style={styles.optionTitle}>{timeframe.title}</Text>
<Text style={styles.optionDescription}>{timeframe.description}</Text>
</View>
{profile.timeHorizon === timeframe.id && (
<Icon name="check-circle" size={24} color="#34C759" />
)}
</TouchableOpacity>
))}
</View>
);
};
// Budget Step
const BudgetStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const budgetRanges = [
{ id: 100, label: '$100', description: 'Start small and build' },
{ id: 500, label: '$500', description: 'Good monthly investment' },
{ id: 1000, label: '$1,000', description: 'Strong investment plan' },
{ id: 2500, label: '$2,500+', description: 'Aggressive wealth building' },
];
return (
<View style={styles.budgetContainer}>
<Text style={styles.budgetSubtitle}>
How much can you comfortably invest each month?
</Text>
{budgetRanges.map((budget) => (
<TouchableOpacity
key={budget.id}
style={[
styles.budgetCard,
profile.monthlyInvestment === budget.id && styles.budgetCardSelected,
]}
onPress={() => updateProfile({ monthlyInvestment: budget.id })}
>
<Text style={styles.budgetLabel}>{budget.label}</Text>
<Text style={styles.budgetDescription}>{budget.description}</Text>
{profile.monthlyInvestment === budget.id && (
<Icon name="check-circle" size={24} color="#34C759" />
)}
</TouchableOpacity>
))}
</View>
);
};
// Interests Step
const InterestsStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile, updateProfile }) => {
const interests = [
{ id: 'stocks', title: 'Individual Stocks', icon: 'trending-up' },
{ id: 'etfs', title: 'ETFs & Index Funds', icon: 'layers' },
{ id: 'crypto', title: 'Cryptocurrency', icon: 'bitcoin' },
{ id: 'real-estate', title: 'Real Estate', icon: 'home' },
{ id: 'bonds', title: 'Bonds', icon: 'shield' },
{ id: 'options', title: 'Options Trading', icon: 'activity' },
{ id: 'dividends', title: 'Dividend Investing', icon: 'dollar-sign' },
{ id: 'growth', title: 'Growth Investing', icon: 'target' },
];
const toggleInterest = (interestId: string) => {
const currentInterests = profile.interests || [];
const updatedInterests = currentInterests.includes(interestId)
? currentInterests.filter(id => id !== interestId)
: [...currentInterests, interestId];
updateProfile({ interests: updatedInterests });
};
return (
<View style={styles.interestsContainer}>
{interests.map((interest) => (
<TouchableOpacity
key={interest.id}
style={[
styles.interestCard,
profile.interests?.includes(interest.id) && styles.interestCardSelected,
]}
onPress={() => toggleInterest(interest.id)}
>
<Icon 
name={interest.icon} 
size={20} 
color={profile.interests?.includes(interest.id) ? '#007AFF' : '#8E8E93'} 
/>
<Text style={[
styles.interestText,
profile.interests?.includes(interest.id) && styles.interestTextSelected,
]}>
{interest.title}
</Text>
{profile.interests?.includes(interest.id) && (
<Icon name="check" size={16} color="#007AFF" />
)}
</TouchableOpacity>
))}
</View>
);
};
// Complete Step
const CompleteStep: React.FC<{
profile: Partial<UserProfile>;
updateProfile: (updates: Partial<UserProfile>) => void;
onNext: () => void;
onBack: () => void;
}> = ({ profile }) => (
<View style={styles.completeContainer}>
<View style={styles.completeIcon}>
<Icon name="check-circle" size={80} color="#34C759" />
</View>
<Text style={styles.completeTitle}>Perfect!</Text>
<Text style={styles.completeText}>
We've created your personalized investment profile. You're ready to start your journey to financial success!
</Text>
<View style={styles.profileSummary}>
<Text style={styles.summaryTitle}>Your Profile:</Text>
<Text style={styles.summaryItem}>
Experience: {profile.experienceLevel?.charAt(0).toUpperCase()}{profile.experienceLevel?.slice(1)}
</Text>
<Text style={styles.summaryItem}>
Risk Level: {profile.riskTolerance?.charAt(0).toUpperCase()}{profile.riskTolerance?.slice(1)}
</Text>
<Text style={styles.summaryItem}>
Monthly Budget: ${profile.monthlyInvestment?.toLocaleString()}
</Text>
</View>
</View>
);
// Helper function to check if step is complete
const isStepComplete = (step: number, profile: Partial<UserProfile>): boolean => {
switch (step) {
case 0: return true; // Welcome step
case 1: return !!profile.experienceLevel;
case 2: return (profile.investmentGoals?.length || 0) > 0;
case 3: return !!profile.riskTolerance;
case 4: return !!profile.timeHorizon;
case 5: return !!profile.monthlyInvestment;
case 6: return (profile.interests?.length || 0) > 0;
case 7: return true; // Complete step
default: return false;
}
};
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#FFFFFF',
},
header: {
paddingHorizontal: 20,
paddingTop: 20,
paddingBottom: 10,
},
progressBar: {
height: 4,
backgroundColor: '#E5E5EA',
borderRadius: 2,
marginBottom: 10,
},
progressFill: {
height: '100%',
backgroundColor: '#007AFF',
borderRadius: 2,
},
stepCounter: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
},
content: {
flex: 1,
},
stepContainer: {
paddingHorizontal: 20,
paddingVertical: 20,
},
title: {
fontSize: 28,
fontWeight: 'bold',
color: '#1C1C1E',
textAlign: 'center',
marginBottom: 10,
},
subtitle: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
marginBottom: 30,
lineHeight: 22,
},
footer: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 20,
paddingVertical: 20,
borderTopWidth: 1,
borderTopColor: '#E5E5EA',
},
backButton: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 12,
paddingHorizontal: 16,
},
backButtonText: {
fontSize: 16,
color: '#007AFF',
marginLeft: 8,
},
nextButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 25,
minWidth: 120,
justifyContent: 'center',
},
nextButtonDisabled: {
backgroundColor: '#C7C7CC',
},
nextButtonText: {
fontSize: 16,
color: '#FFFFFF',
fontWeight: '600',
marginRight: 8,
},
// Welcome styles
welcomeContainer: {
alignItems: 'center',
paddingVertical: 40,
},
welcomeIcon: {
width: 120,
height: 120,
borderRadius: 60,
backgroundColor: '#F2F2F7',
justifyContent: 'center',
alignItems: 'center',
marginBottom: 30,
},
welcomeText: {
fontSize: 18,
color: '#1C1C1E',
textAlign: 'center',
lineHeight: 26,
marginBottom: 15,
},
welcomeSubtext: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 22,
},
// Options styles
optionsContainer: {
gap: 16,
},
optionCard: {
flexDirection: 'row',
alignItems: 'center',
padding: 20,
backgroundColor: '#F2F2F7',
borderRadius: 16,
borderWidth: 2,
borderColor: 'transparent',
},
optionCardSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
optionIcon: {
width: 48,
height: 48,
borderRadius: 24,
justifyContent: 'center',
alignItems: 'center',
marginRight: 16,
},
optionContent: {
flex: 1,
},
optionTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
optionDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
},
// Goals styles
goalsContainer: {
gap: 12,
},
goalCard: {
flexDirection: 'row',
alignItems: 'center',
padding: 16,
backgroundColor: '#F2F2F7',
borderRadius: 12,
borderWidth: 1,
borderColor: 'transparent',
},
goalCardSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
goalText: {
fontSize: 16,
color: '#1C1C1E',
marginLeft: 12,
flex: 1,
},
goalTextSelected: {
color: '#007AFF',
fontWeight: '600',
},
// Risk styles
riskCard: {
padding: 20,
backgroundColor: '#F2F2F7',
borderRadius: 16,
borderWidth: 2,
borderColor: 'transparent',
position: 'relative',
},
riskCardSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
riskHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 8,
},
riskIndicator: {
width: 12,
height: 12,
borderRadius: 6,
marginRight: 12,
},
riskTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
},
riskDescription: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
},
riskAllocation: {
fontSize: 12,
color: '#007AFF',
fontWeight: '500',
},
riskCheck: {
position: 'absolute',
top: 16,
right: 16,
},
// Budget styles
budgetContainer: {
gap: 16,
},
budgetSubtitle: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
marginBottom: 20,
},
budgetCard: {
flexDirection: 'row',
alignItems: 'center',
padding: 20,
backgroundColor: '#F2F2F7',
borderRadius: 16,
borderWidth: 2,
borderColor: 'transparent',
},
budgetCardSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
budgetLabel: {
fontSize: 24,
fontWeight: 'bold',
color: '#1C1C1E',
marginRight: 16,
minWidth: 80,
},
budgetDescription: {
fontSize: 14,
color: '#8E8E93',
flex: 1,
},
// Interests styles
interestsContainer: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 12,
},
interestCard: {
flexDirection: 'row',
alignItems: 'center',
paddingVertical: 12,
paddingHorizontal: 16,
backgroundColor: '#F2F2F7',
borderRadius: 20,
borderWidth: 1,
borderColor: 'transparent',
minWidth: '45%',
},
interestCardSelected: {
backgroundColor: '#E3F2FD',
borderColor: '#007AFF',
},
interestText: {
fontSize: 14,
color: '#1C1C1E',
marginLeft: 8,
flex: 1,
},
interestTextSelected: {
color: '#007AFF',
fontWeight: '600',
},
// Complete styles
completeContainer: {
alignItems: 'center',
paddingVertical: 40,
},
completeIcon: {
marginBottom: 30,
},
completeTitle: {
fontSize: 32,
fontWeight: 'bold',
color: '#1C1C1E',
marginBottom: 15,
},
completeText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 24,
marginBottom: 30,
},
profileSummary: {
backgroundColor: '#F2F2F7',
padding: 20,
borderRadius: 16,
width: '100%',
},
summaryTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 12,
},
summaryItem: {
fontSize: 16,
color: '#1C1C1E',
marginBottom: 8,
},
});
export default OnboardingScreen;
