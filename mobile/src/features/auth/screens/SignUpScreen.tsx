import React, { useState, useRef } from 'react';
import { 
View, 
TextInput, 
Text, 
TouchableOpacity, 
StyleSheet, 
ScrollView, 
Alert,
KeyboardAvoidingView,
Platform,
Dimensions,
Image,
SafeAreaView
} from 'react-native';
import { gql, useMutation, useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';
import { StableNumberInput } from '../../../components/StableNumberInput';
const { width } = Dimensions.get('window');
// Income Profile Constants
const incomeBrackets = [
'Under $30,000',
'$30,000 - $50,000',
'$50,000 - $75,000',
'$75,000 - $100,000',
'$100,000 - $150,000',
'Over $150,000'
];
const investmentGoals = [
'Retirement Savings',
'Buy a Home',
'Emergency Fund',
'Wealth Building',
'Passive Income',
'Tax Benefits',
'College Fund',
'Travel Fund'
];
const riskToleranceOptions = [
'Conservative',
'Moderate',
'Aggressive'
];
const investmentHorizonOptions = [
'1-3 years',
'3-5 years',
'5-10 years',
'10+ years'
];
const SIGNUP = gql`
mutation Signup($email: String!, $name: String!, $password: String!, $profilePic: String) {
createUser(email: $email, name: $name, password: $password, profilePic: $profilePic) {
user {
id
email
name
profilePic
}
}
}
`;
interface SignUpScreenProps {
navigateTo: (screen: string) => void;
onSignUp: () => void;
onNavigateToLogin: () => void;
}
export default function SignUpScreen({ navigateTo, onSignUp, onNavigateToLogin }: SignUpScreenProps) {
const [email, setEmail] = useState('');
const [name, setName] = useState('');
const [password, setPassword] = useState('');
const [showPassword, setShowPassword] = useState(false);
const [profilePic, setProfilePic] = useState<string | null>(null);
// Income Profile Fields
const [incomeBracket, setIncomeBracket] = useState('');
const [age, setAge] = useState('');
const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
const [riskTolerance, setRiskTolerance] = useState('');
const [investmentHorizon, setInvestmentHorizon] = useState('');
const [showIncomeProfile, setShowIncomeProfile] = useState(false);
const [signup, { loading, error }] = useMutation(SIGNUP);
const client = useApolloClient();
const pickImage = async (source: 'camera' | 'gallery') => {
try {
let result;
if (source === 'camera') {
const { granted } = await ImagePicker.requestCameraPermissionsAsync();
if (!granted) {
Alert.alert('Permission needed', 'Please allow camera access to take a photo.');
return;
}
result = await ImagePicker.launchCameraAsync({
mediaTypes: ImagePicker.MediaTypeOptions.Images,
allowsEditing: true,
aspect: [1, 1],
quality: 0.8,
});
} else {
const { granted } = await ImagePicker.requestMediaLibraryPermissionsAsync();
if (!granted) {
Alert.alert('Permission needed', 'Please allow photo library access to select an image.');
return;
}
result = await ImagePicker.launchImageLibraryAsync({
mediaTypes: ImagePicker.MediaTypeOptions.Images,
allowsEditing: true,
aspect: [1, 1],
quality: 0.8,
});
}
if (!result.canceled && result.assets.length > 0) {
setProfilePic(result.assets[0].uri);
}
} catch (error) {
console.error('Error picking image:', error);
Alert.alert('Error', 'Failed to pick image. Please try again.');
}
};
const showImagePickerOptions = () => {
Alert.alert(
'Profile Picture',
'Choose how you want to add your profile picture',
[
{ text: 'Cancel', style: 'cancel' },
{ text: 'Take Photo', onPress: () => pickImage('camera') },
{ text: 'Choose from Gallery', onPress: () => pickImage('gallery') },
]
);
};
const removeProfilePic = () => {
setProfilePic(null);
};
// Income Profile Helpers
const handleGoalToggle = (goal: string) => {
if (selectedGoals.includes(goal)) {
setSelectedGoals(selectedGoals.filter(g => g !== goal));
} else {
setSelectedGoals([...selectedGoals, goal]);
}
};
const toggleIncomeProfile = () => {
setShowIncomeProfile(!showIncomeProfile);
};
const validateForm = () => {
if (!name.trim()) {
Alert.alert('Validation Error', 'Please enter your name');
return false;
}
if (!email.trim()) {
Alert.alert('Validation Error', 'Please enter your email');
return false;
}
if (!email.includes('@')) {
Alert.alert('Validation Error', 'Please enter a valid email address');
return false;
}
if (password.length < 6) {
Alert.alert('Validation Error', 'Password must be at least 6 characters long');
return false;
}
return true;
};
const handleSignup = async () => {
if (!validateForm()) return;
try {
const res = await signup({ 
variables: { 
email: email.trim().toLowerCase(), 
name: name.trim(), 
password,
profilePic: profilePic || null
} 
});
// User created successfully - go directly to onboarding
await client.resetStore();
onSignUp();
} catch (err) {
console.error('Signup error:', err);
Alert.alert('Signup Failed', 'There was an error creating your account. Please try again.');
}
};
return (
<SafeAreaView style={styles.container}>
<KeyboardAvoidingView 
style={styles.keyboardContainer} 
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
>
<ScrollView 
contentContainerStyle={styles.scrollContainer}
showsVerticalScrollIndicator={false}
keyboardShouldPersistTaps="handled"
>
{/* Header */}
<View style={styles.header}>
<Icon name="user" size={60} color="#00cc99" />
<Text style={styles.title}>Join RichesReach</Text>
<Text style={styles.subtitle}>Start your financial journey today</Text>
</View>
{/* Form */}
<View style={styles.form}>
{/* Profile Picture Section */}
<View style={styles.profilePicSection}>
<Text style={styles.sectionTitle}>Profile Picture</Text>
<View style={styles.profilePicContainer}>
{profilePic ? (
<View style={styles.profilePicWrapper}>
<Image source={{ uri: profilePic }} style={styles.profilePic} />
<TouchableOpacity 
style={styles.removePicButton} 
onPress={removeProfilePic}
>
<Icon name="x" size={16} color="#fff" />
</TouchableOpacity>
</View>
) : (
<TouchableOpacity 
style={styles.addPicButton} 
onPress={showImagePickerOptions}
>
<Icon name="camera" size={32} color="#00cc99" />
<Text style={styles.addPicText}>Add Photo</Text>
</TouchableOpacity>
)}
</View>
{!profilePic && (
<Text style={styles.optionalText}>Optional - You can add this later</Text>
)}
</View>
{/* Name Input */}
<View style={styles.inputContainer}>
<Icon name="user" size={20} color="#666" style={styles.inputIcon} />
<TextInput
placeholder="Full Name"
style={styles.input}
value={name}
onChangeText={setName}
autoCapitalize="words"
autoCorrect={false}
returnKeyType="next"
/>
</View>
{/* Email Input */}
<View style={styles.inputContainer}>
<Icon name="mail" size={20} color="#666" style={styles.inputIcon} />
<TextInput
placeholder="Email Address"
style={styles.input}
value={email}
onChangeText={setEmail}
keyboardType="email-address"
autoCapitalize="none"
autoCorrect={false}
returnKeyType="next"
/>
</View>
{/* Password Input */}
<View style={styles.inputContainer}>
<Icon name="lock" size={20} color="#666" style={styles.inputIcon} />
<TextInput
placeholder="Password"
style={styles.input}
value={password}
onChangeText={setPassword}
secureTextEntry={!showPassword}
autoCapitalize="none"
autoCorrect={false}
returnKeyType="done"
/>
<TouchableOpacity 
style={styles.eyeIcon} 
onPress={() => setShowPassword(!showPassword)}
>
<Icon name={showPassword ? "eye-off" : "eye"} size={20} color="#666" />
</TouchableOpacity>
</View>
{/* Income Profile Section */}
<View style={styles.incomeProfileSection}>
<TouchableOpacity 
style={styles.incomeProfileToggle} 
onPress={toggleIncomeProfile}
activeOpacity={0.7}
>
<Icon name="trending-up" size={20} color="#00cc99" />
<Text style={styles.incomeProfileToggleText}>
{showIncomeProfile ? 'Hide' : 'Add'} Financial Profile (Optional)
</Text>
<Icon 
name={showIncomeProfile ? "chevron-up" : "chevron-down"} 
size={20} 
color="#666" 
/>
</TouchableOpacity>
<View style={[
  styles.incomeProfileForm,
  { 
    opacity: showIncomeProfile ? 1 : 0,
    height: showIncomeProfile ? 'auto' : 0,
    overflow: 'hidden'
  }
]}>
<Text style={styles.incomeProfileSubtitle}>
Help us provide personalized AI investment recommendations
</Text>
{/* Income Bracket */}
<View style={styles.formGroup}>
<Text style={styles.label}>Annual Income</Text>
<View style={styles.optionsGrid}>
{incomeBrackets.map((bracket) => (
<TouchableOpacity
key={bracket}
style={[
styles.optionButton,
incomeBracket === bracket && styles.selectedOption
]}
onPress={() => setIncomeBracket(bracket)}
>
<Text style={[
styles.optionText,
incomeBracket === bracket && styles.selectedOptionText
]}>
{bracket}
</Text>
</TouchableOpacity>
))}
</View>
</View>
      {/* Age - MINIMAL TEST INPUT */}
      <View style={styles.formGroup}>
        <Text style={styles.label}>Age</Text>
        <TextInput
          style={[styles.input, { borderWidth: 1, borderColor: '#ccc' }]}
          value={age}
          onChangeText={setAge}
          placeholder="Enter your age (minimum 18)"
          keyboardType="number-pad"
          blurOnSubmit={false}
          autoCorrect={false}
          autoCapitalize="none"
          maxLength={3}
        />
      </View>
{/* Investment Goals */}
<View style={styles.formGroup}>
<Text style={styles.label}>Investment Goals (Select all that apply)</Text>
<View style={styles.optionsGrid}>
{investmentGoals.map((goal) => (
<TouchableOpacity
key={goal}
style={[
styles.optionButton,
selectedGoals.includes(goal) && styles.selectedOption
]}
onPress={() => handleGoalToggle(goal)}
>
<Text style={[
styles.optionText,
selectedGoals.includes(goal) && styles.selectedOptionText
]}>
{goal}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* Risk Tolerance */}
<View style={styles.formGroup}>
<Text style={styles.label}>Risk Tolerance</Text>
<View style={styles.optionsGrid}>
{riskToleranceOptions.map((option) => (
<TouchableOpacity
key={option}
style={[
styles.optionButton,
riskTolerance === option && styles.selectedOption
]}
onPress={() => setRiskTolerance(option)}
>
<Text style={[
styles.optionText,
riskTolerance === option && styles.selectedOptionText
]}>
{option}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* Investment Horizon */}
<View style={styles.formGroup}>
<Text style={styles.label}>Investment Time Horizon</Text>
<View style={styles.optionsGrid}>
{investmentHorizonOptions.map((option) => (
<TouchableOpacity
key={option}
style={[
styles.optionButton,
investmentHorizon === option && styles.selectedOption
]}
onPress={() => setInvestmentHorizon(option)}
>
<Text style={[
styles.optionText,
investmentHorizon === option && styles.selectedOptionText
]}>
{option}
</Text>
</TouchableOpacity>
))}
</View>
</View>
</View>
</View>
{/* Sign Up Button */}
<TouchableOpacity 
style={[styles.button, loading && styles.buttonDisabled]} 
onPress={handleSignup}
disabled={loading}
activeOpacity={0.8}
>
{loading ? (
<View style={styles.loadingContainer}>
<Icon name="refresh-cw" size={20} color="#fff" style={styles.spinner} />
<Text style={styles.buttonText}>Creating Account...</Text>
</View>
) : (
<Text style={styles.buttonText}>Create Account</Text>
)}
</TouchableOpacity>
{/* Error Display */}
{error && (
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={16} color="#ef4444" />
<Text style={styles.errorText}>{error.message}</Text>
</View>
)}
{/* Login Link */}
<View style={styles.loginLink}>
<Text style={styles.loginText}>Already have an account? </Text>
<TouchableOpacity onPress={onNavigateToLogin} activeOpacity={0.7}>
<Text style={styles.loginLinkText}>Log in here</Text>
</TouchableOpacity>
</View>
</View>
{/* Footer */}
<View style={styles.footer}>
<Text style={styles.footerText}>By signing up, you agree to our Terms of Service and Privacy Policy</Text>
</View>
</ScrollView>
</KeyboardAvoidingView>
</SafeAreaView>
);
}
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#f8fafc',
},
keyboardContainer: {
flex: 1,
},
scrollContainer: {
flexGrow: 1,
paddingHorizontal: 24,
paddingTop: 80,
paddingBottom: 40,
},
header: {
alignItems: 'center',
marginBottom: 40,
},
title: {
fontSize: 28,
fontWeight: 'bold',
color: '#1e293b',
marginTop: 16,
marginBottom: 8,
},
subtitle: {
fontSize: 16,
color: '#64748b',
textAlign: 'center',
lineHeight: 22,
},
form: {
backgroundColor: '#ffffff',
borderRadius: 16,
padding: 24,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 8,
elevation: 4,
marginBottom: 24,
},
profilePicSection: {
marginBottom: 24,
},
sectionTitle: {
fontSize: 18,
fontWeight: 'bold',
color: '#1e293b',
marginBottom: 12,
},
profilePicContainer: {
width: 100,
height: 100,
borderRadius: 50,
backgroundColor: '#f8fafc',
justifyContent: 'center',
alignItems: 'center',
borderWidth: 1,
borderColor: '#e2e8f0',
alignSelf: 'center',
},
profilePicWrapper: {
position: 'relative',
width: '100%',
height: '100%',
},
profilePic: {
width: '100%',
height: '100%',
borderRadius: 50,
},
addPicButton: {
width: '100%',
height: '100%',
justifyContent: 'center',
alignItems: 'center',
},
addPicText: {
marginTop: 8,
color: '#00cc99',
fontSize: 14,
fontWeight: '600',
},
removePicButton: {
position: 'absolute',
top: -8,
right: -8,
backgroundColor: '#ef4444',
borderRadius: 12,
width: 24,
height: 24,
justifyContent: 'center',
alignItems: 'center',
borderWidth: 2,
borderColor: '#ffffff',
},
optionalText: {
color: '#94a3b8',
fontSize: 14,
textAlign: 'center',
marginTop: 8,
},
inputContainer: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#f8fafc',
borderRadius: 12,
marginBottom: 16,
borderWidth: 1,
borderColor: '#e2e8f0',
},
inputIcon: {
marginLeft: 16,
marginRight: 12,
},
input: {
flex: 1,
paddingVertical: 16,
paddingHorizontal: 8,
fontSize: 16,
color: '#1e293b',
},
eyeIcon: {
padding: 16,
},
button: {
backgroundColor: '#00cc99',
borderRadius: 12,
paddingVertical: 16,
alignItems: 'center',
marginTop: 8,
marginBottom: 16,
shadowColor: '#00cc99',
shadowOffset: { width: 0, height: 4 },
shadowOpacity: 0.3,
shadowRadius: 8,
elevation: 6,
},
buttonDisabled: {
backgroundColor: '#94a3b8',
shadowOpacity: 0.1,
},
loadingContainer: {
flexDirection: 'row',
alignItems: 'center',
},
spinner: {
marginRight: 8,
},
buttonText: {
color: '#ffffff',
fontSize: 18,
fontWeight: '600',
},
errorContainer: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#fef2f2',
borderWidth: 1,
borderColor: '#fecaca',
borderRadius: 8,
padding: 12,
marginBottom: 16,
},
errorText: {
color: '#dc2626',
marginLeft: 8,
fontSize: 14,
},
loginLink: {
flexDirection: 'row',
justifyContent: 'center',
alignItems: 'center',
marginTop: 8,
},
loginText: {
color: '#64748b',
fontSize: 16,
},
loginLinkText: {
color: '#00cc99',
fontSize: 16,
fontWeight: '600',
textDecorationLine: 'underline',
},
footer: {
alignItems: 'center',
},
footerText: {
color: '#94a3b8',
fontSize: 12,
textAlign: 'center',
lineHeight: 16,
},
// Income Profile Styles
incomeProfileSection: {
marginBottom: 24,
},
incomeProfileToggle: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
backgroundColor: '#f8fafc',
borderRadius: 12,
padding: 16,
borderWidth: 1,
borderColor: '#e2e8f0',
},
incomeProfileToggleText: {
flex: 1,
fontSize: 16,
fontWeight: '600',
color: '#1e293b',
marginLeft: 12,
},
incomeProfileForm: {
marginTop: 16,
padding: 20,
backgroundColor: '#f8fafc',
borderRadius: 12,
borderWidth: 1,
borderColor: '#e2e8f0',
},
incomeProfileSubtitle: {
fontSize: 14,
color: '#64748b',
textAlign: 'center',
marginBottom: 20,
lineHeight: 20,
},
formGroup: {
marginBottom: 20,
},
label: {
fontSize: 16,
fontWeight: '600',
color: '#374151',
marginBottom: 10,
},
optionsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 10,
},
optionButton: {
paddingHorizontal: 16,
paddingVertical: 8,
borderRadius: 20,
borderWidth: 1,
borderColor: '#D1D5DB',
backgroundColor: '#fff',
},
selectedOption: {
backgroundColor: '#00cc99',
borderColor: '#00cc99',
},
optionText: {
fontSize: 14,
color: '#374151',
},
selectedOptionText: {
color: '#fff',
fontWeight: '600',
},
});