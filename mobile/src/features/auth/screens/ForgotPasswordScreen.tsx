import React, { useState } from 'react';
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
Animated
} from 'react-native';
import { gql, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import logger from '../../../utils/logger';
const FORGOT_PASSWORD = gql`
mutation ForgotPassword($email: String!) {
forgotPassword(email: $email) {
success
message
}
}
`;
interface ForgotPasswordScreenProps {
onNavigateToLogin: () => void;
onNavigateToResetPassword: (email: string) => void;
}
export default function ForgotPasswordScreen({ 
onNavigateToLogin, 
onNavigateToResetPassword 
}: ForgotPasswordScreenProps) {
const [email, setEmail] = useState('');
const [emailSent, setEmailSent] = useState(false);
const [formErrors, setFormErrors] = useState({ email: '' });
const [fadeAnim] = useState(new Animated.Value(0));
const [forgotPassword, { loading }] = useMutation(FORGOT_PASSWORD);
React.useEffect(() => {
Animated.timing(fadeAnim, {
toValue: 1,
duration: 800,
useNativeDriver: true,
}).start();
}, []);
const validateEmail = (email: string) => {
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
return emailRegex.test(email);
};
const validateForm = () => {
const errors = { email: '' };
let isValid = true;
if (!email.trim()) {
errors.email = 'Email is required';
isValid = false;
} else if (!validateEmail(email)) {
errors.email = 'Please enter a valid email address';
isValid = false;
}
setFormErrors(errors);
return isValid;
};
const handleForgotPassword = async () => {
if (!validateForm()) return;
try {
const response = await forgotPassword({ 
variables: { email: email.trim().toLowerCase() } 
});
if (response.data?.forgotPassword?.success) {
setEmailSent(true);
Alert.alert(
'Email Sent',
'Please check your email for password reset instructions.',
[{ text: 'OK' }]
);
} else {
throw new Error(response.data?.forgotPassword?.message || 'Failed to send reset email');
}
} catch (err: any) {
  logger.error('Forgot password error:', err);
  Alert.alert(
'Error',
err.message || 'Failed to send reset email. Please try again.',
[{ text: 'OK' }]
);
}
};
const handleResendEmail = () => {
setEmailSent(false);
handleForgotPassword();
};
if (emailSent) {
return (
<KeyboardAvoidingView 
style={styles.container} 
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
>
<ScrollView contentContainerStyle={styles.scrollContainer}>
<Animated.View style={[styles.content, { opacity: fadeAnim }]}>
<View style={styles.header}>
<View style={styles.successIconContainer}>
<Icon name="mail" size={60} color="#10b981" />
</View>
<Text style={styles.title}>Check Your Email</Text>
<Text style={styles.subtitle}>
We've sent password reset instructions to{'\n'}
<Text style={styles.emailText}>{email}</Text>
</Text>
</View>
<View style={styles.form}>
<View style={styles.instructionsContainer}>
<Text style={styles.instructionsTitle}>Next Steps:</Text>
<View style={styles.instructionItem}>
<Icon name="check-circle" size={16} color="#10b981" />
<Text style={styles.instructionText}>Check your email inbox</Text>
</View>
<View style={styles.instructionItem}>
<Icon name="check-circle" size={16} color="#10b981" />
<Text style={styles.instructionText}>Click the reset link in the email</Text>
</View>
<View style={styles.instructionItem}>
<Icon name="check-circle" size={16} color="#10b981" />
<Text style={styles.instructionText}>Create a new password</Text>
</View>
</View>
<TouchableOpacity 
style={styles.resendButton}
onPress={handleResendEmail}
activeOpacity={0.8}
>
<Icon name="refresh-cw" size={20} color="#00cc99" />
<Text style={styles.resendButtonText}>Resend Email</Text>
</TouchableOpacity>
<TouchableOpacity 
style={styles.backButton}
onPress={onNavigateToLogin}
activeOpacity={0.8}
>
<Text style={styles.backButtonText}>Back to Login</Text>
</TouchableOpacity>
</View>
</Animated.View>
</ScrollView>
</KeyboardAvoidingView>
);
}
return (
<KeyboardAvoidingView 
style={styles.container} 
behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
>
<ScrollView 
contentContainerStyle={styles.scrollContainer}
keyboardShouldPersistTaps="handled"
showsVerticalScrollIndicator={false}
>
<Animated.View style={[styles.content, { opacity: fadeAnim }]}>
{/* Header */}
<View style={styles.header}>
<View style={styles.iconContainer}>
<Icon name="lock" size={60} color="#00cc99" />
</View>
<Text style={styles.title}>Forgot Password?</Text>
<Text style={styles.subtitle}>
No worries! Enter your email address and we'll send you instructions to reset your password.
</Text>
</View>
{/* Form */}
<View style={styles.form}>
{/* Email Input */}
<View style={styles.inputContainer}>
<Icon name="mail" size={20} color="#666" style={styles.inputIcon} />
<TextInput
placeholder="Email Address"
placeholderTextColor="#aaa"
style={[styles.input, formErrors.email && styles.inputError]}
onChangeText={setEmail}
value={email}
keyboardType="email-address"
autoCapitalize="none"
autoCorrect={false}
returnKeyType="done"
onSubmitEditing={handleForgotPassword}
/>
</View>
{formErrors.email ? <Text style={styles.errorText}>{formErrors.email}</Text> : null}
{/* Send Reset Button */}
<TouchableOpacity 
style={[styles.button, loading && styles.buttonDisabled]} 
onPress={handleForgotPassword}
disabled={loading}
activeOpacity={0.8}
>
{loading ? (
<View style={styles.loadingContainer}>
<Icon name="refresh-cw" size={20} color="#fff" style={styles.spinner} />
<Text style={styles.buttonText}>Sending...</Text>
</View>
) : (
<Text style={styles.buttonText}>Send Reset Instructions</Text>
)}
</TouchableOpacity>
{/* Back to Login */}
<TouchableOpacity 
style={styles.backToLoginButton}
onPress={onNavigateToLogin}
activeOpacity={0.8}
>
<Icon name="arrow-left" size={20} color="#00cc99" />
<Text style={styles.backToLoginText}>Back to Login</Text>
</TouchableOpacity>
</View>
</Animated.View>
</ScrollView>
</KeyboardAvoidingView>
);
}
const styles = StyleSheet.create({
container: {
flex: 1,
backgroundColor: '#f8fafc',
},
scrollContainer: {
flexGrow: 1,
justifyContent: 'center',
paddingHorizontal: 24,
paddingVertical: 40,
},
content: {
flex: 1,
justifyContent: 'center',
},
header: {
alignItems: 'center',
marginBottom: 40,
},
iconContainer: {
width: 120,
height: 120,
borderRadius: 60,
backgroundColor: '#f0fdf4',
justifyContent: 'center',
alignItems: 'center',
marginBottom: 24,
},
successIconContainer: {
width: 120,
height: 120,
borderRadius: 60,
backgroundColor: '#f0fdf4',
justifyContent: 'center',
alignItems: 'center',
marginBottom: 24,
},
title: {
fontSize: 28,
fontWeight: 'bold',
color: '#1e293b',
marginBottom: 12,
textAlign: 'center',
},
subtitle: {
fontSize: 16,
color: '#64748b',
textAlign: 'center',
lineHeight: 22,
paddingHorizontal: 20,
},
emailText: {
fontWeight: '600',
color: '#00cc99',
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
},
inputContainer: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#f8fafc',
borderRadius: 12,
marginBottom: 8,
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
inputError: {
borderColor: '#ef4444',
backgroundColor: '#fef2f2',
},
errorText: {
color: '#ef4444',
fontSize: 14,
marginBottom: 16,
marginLeft: 4,
},
button: {
backgroundColor: '#00cc99',
borderRadius: 12,
paddingVertical: 16,
alignItems: 'center',
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
backToLoginButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
paddingVertical: 12,
},
backToLoginText: {
color: '#00cc99',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
instructionsContainer: {
backgroundColor: '#f8fafc',
borderRadius: 12,
padding: 20,
marginBottom: 24,
},
instructionsTitle: {
fontSize: 18,
fontWeight: '600',
color: '#1e293b',
marginBottom: 16,
textAlign: 'center',
},
instructionItem: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 12,
},
instructionText: {
fontSize: 16,
color: '#374151',
marginLeft: 12,
flex: 1,
},
resendButton: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
backgroundColor: '#f8fafc',
borderRadius: 12,
paddingVertical: 16,
marginBottom: 16,
borderWidth: 1,
borderColor: '#e2e8f0',
},
resendButtonText: {
color: '#00cc99',
fontSize: 16,
fontWeight: '600',
marginLeft: 8,
},
backButton: {
backgroundColor: '#00cc99',
borderRadius: 12,
paddingVertical: 16,
alignItems: 'center',
},
backButtonText: {
color: '#ffffff',
fontSize: 16,
fontWeight: '600',
},
});
