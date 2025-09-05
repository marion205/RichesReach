import React, { useState, useEffect } from 'react';
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
  Animated,
  Dimensions
} from 'react-native';
import { gql, useMutation, useApolloClient } from '@apollo/client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Icon from 'react-native-vector-icons/Feather';
import * as LocalAuthentication from 'expo-local-authentication';

const { width } = Dimensions.get('window');

const LOGIN = gql`
  mutation TokenAuth($email: String!, $password: String!) {
    tokenAuth(email: $email, password: $password) {
      token
    }
  }
`;

interface EnhancedLoginScreenProps {
  onLogin: (token: string) => void;
  onNavigateToSignUp: () => void;
}

export default function EnhancedLoginScreen({ onLogin, onNavigateToSignUp }: EnhancedLoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [formErrors, setFormErrors] = useState({ email: '', password: '' });
  const [isBiometricAvailable, setIsBiometricAvailable] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));

  const [tokenAuth, { loading: loginLoading, error: loginError }] = useMutation(LOGIN);
  const client = useApolloClient();

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();

    checkBiometricAvailability();
    loadRememberedCredentials();
  }, []);

  const checkBiometricAvailability = async () => {
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      setIsBiometricAvailable(hasHardware && isEnrolled);
    } catch (error) {
      console.log('Biometric check failed:', error);
    }
  };

  const loadRememberedCredentials = async () => {
    try {
      const remembered = await AsyncStorage.getItem('rememberMe');
      const lastEmail = await AsyncStorage.getItem('lastLoginEmail');
      
      if (remembered === 'true' && lastEmail) {
        setEmail(lastEmail);
        setRememberMe(true);
      }
    } catch (error) {
      console.log('Failed to load remembered credentials:', error);
    }
  };

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const errors = { email: '', password: '' };
    let isValid = true;

    if (!email.trim()) {
      errors.email = 'Email is required';
      isValid = false;
    } else if (!validateEmail(email)) {
      errors.email = 'Please enter a valid email address';
      isValid = false;
    }

    if (!password.trim()) {
      errors.password = 'Password is required';
      isValid = false;
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const getErrorMessage = (error: any) => {
    if (error.message.includes('Invalid credentials')) {
      return 'Email or password is incorrect. Please try again.';
    }
    if (error.message.includes('User not found')) {
      return 'No account found with this email address.';
    }
    if (error.message.includes('Account locked')) {
      return 'Account temporarily locked. Please try again later.';
    }
    return 'Login failed. Please check your credentials and try again.';
  };

  const authenticateWithBiometrics = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate to access RichesReach',
        fallbackLabel: 'Use Passcode',
        cancelLabel: 'Cancel',
      });

      if (result.success) {
        // Try to login with stored credentials
        const storedEmail = await AsyncStorage.getItem('lastLoginEmail');
        if (storedEmail) {
          setEmail(storedEmail);
          // You could store a hashed password or use a different auth method
          Alert.alert('Biometric Success', 'Please enter your password to complete login.');
        }
      }
    } catch (error) {
      console.log('Biometric authentication failed:', error);
      Alert.alert('Authentication Failed', 'Biometric authentication failed. Please try again.');
    }
  };

  const handleLogin = async () => {
    if (!validateForm()) return;

    try {
      await client.clearStore();
      
      const response = await tokenAuth({ 
        variables: { 
          email: email.trim().toLowerCase(), 
          password: password 
        },
        errorPolicy: 'all'
      });
      
      if (response.errors) {
        throw new Error(response.errors[0].message);
      }
      
      const token = response.data?.tokenAuth?.token;
      if (!token) {
        throw new Error('No token received');
      }
      
      // Store token securely
      await AsyncStorage.setItem('token', token);
      
      // Handle remember me
      if (rememberMe) {
        await AsyncStorage.setItem('rememberMe', 'true');
        await AsyncStorage.setItem('lastLoginEmail', email.trim().toLowerCase());
      } else {
        await AsyncStorage.removeItem('rememberMe');
        await AsyncStorage.removeItem('lastLoginEmail');
      }
      
      onLogin(token);
    } catch (err: any) {
      console.error('Login failed:', err);
      Alert.alert('Login Failed', getErrorMessage(err));
    }
  };

  const handleForgotPassword = () => {
    Alert.alert(
      'Forgot Password',
      'Password reset functionality will be available soon. Please contact support for assistance.',
      [{ text: 'OK' }]
    );
  };

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
            <Icon name="trending-up" size={60} color="#00cc99" />
            <Text style={styles.title}>Welcome Back</Text>
            <Text style={styles.subtitle}>Sign in to continue your financial journey</Text>
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
                returnKeyType="next"
              />
            </View>
            {formErrors.email ? <Text style={styles.errorText}>{formErrors.email}</Text> : null}

            {/* Password Input */}
            <View style={styles.inputContainer}>
              <Icon name="lock" size={20} color="#666" style={styles.inputIcon} />
              <TextInput
                placeholder="Password"
                placeholderTextColor="#aaa"
                style={[styles.input, formErrors.password && styles.inputError]}
                onChangeText={setPassword}
                value={password}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
              />
              <TouchableOpacity 
                style={styles.eyeIcon} 
                onPress={() => setShowPassword(!showPassword)}
              >
                <Icon name={showPassword ? "eye-off" : "eye"} size={20} color="#666" />
              </TouchableOpacity>
            </View>
            {formErrors.password ? <Text style={styles.errorText}>{formErrors.password}</Text> : null}

            {/* Remember Me & Forgot Password */}
            <View style={styles.optionsRow}>
              <TouchableOpacity 
                style={styles.rememberMeContainer}
                onPress={() => setRememberMe(!rememberMe)}
                activeOpacity={0.7}
              >
                <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                  {rememberMe && <Icon name="check" size={16} color="#fff" />}
                </View>
                <Text style={styles.rememberMeText}>Remember me</Text>
              </TouchableOpacity>

              <TouchableOpacity onPress={handleForgotPassword} activeOpacity={0.7}>
                <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
              </TouchableOpacity>
            </View>

            {/* Login Button */}
            <TouchableOpacity 
              style={[styles.button, loginLoading && styles.buttonDisabled]} 
              onPress={handleLogin}
              disabled={loginLoading}
              activeOpacity={0.8}
            >
              {loginLoading ? (
                <View style={styles.loadingContainer}>
                  <Icon name="refresh-cw" size={20} color="#fff" style={styles.spinner} />
                  <Text style={styles.buttonText}>Signing In...</Text>
                </View>
              ) : (
                <Text style={styles.buttonText}>Sign In</Text>
              )}
            </TouchableOpacity>

            {/* Biometric Login */}
            {isBiometricAvailable && (
              <TouchableOpacity 
                style={styles.biometricButton}
                onPress={authenticateWithBiometrics}
                activeOpacity={0.8}
              >
                <Icon name="smartphone" size={20} color="#00cc99" />
                <Text style={styles.biometricButtonText}>Use Biometric</Text>
              </TouchableOpacity>
            )}

            {/* Error Display */}
            {loginError && (
              <View style={styles.errorContainer}>
                <Icon name="alert-circle" size={16} color="#ef4444" />
                <Text style={styles.errorMessage}>{getErrorMessage(loginError)}</Text>
              </View>
            )}

            {/* Sign Up Link */}
            <View style={styles.signupContainer}>
              <Text style={styles.signupText}>Don't have an account? </Text>
              <TouchableOpacity onPress={onNavigateToSignUp} activeOpacity={0.7}>
                <Text style={styles.signupLinkText}>Sign up here</Text>
              </TouchableOpacity>
            </View>
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
  eyeIcon: {
    padding: 16,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 14,
    marginBottom: 16,
    marginLeft: 4,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  rememberMeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#d1d5db',
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#00cc99',
    borderColor: '#00cc99',
  },
  rememberMeText: {
    fontSize: 14,
    color: '#64748b',
  },
  forgotPasswordText: {
    fontSize: 14,
    color: '#00cc99',
    fontWeight: '600',
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
  biometricButton: {
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
  biometricButtonText: {
    color: '#00cc99',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
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
  errorMessage: {
    color: '#dc2626',
    marginLeft: 8,
    fontSize: 14,
    flex: 1,
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  signupText: {
    color: '#64748b',
    fontSize: 16,
  },
  signupLinkText: {
    color: '#00cc99',
    fontSize: 16,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
