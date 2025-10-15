// EnhancedLoginScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import JWTAuthService from '../../auth/services/JWTAuthService';

interface EnhancedLoginScreenProps {
  onLogin: () => void;
  onNavigateToSignUp: () => void;
  onNavigateToForgotPassword: () => void;
}

const EnhancedLoginScreen: React.FC<EnhancedLoginScreenProps> = ({
  onLogin,
  onNavigateToSignUp,
  onNavigateToForgotPassword,
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter both email and password');
      return;
    }

    setIsLoading(true);
    try {
      const jwtService = JWTAuthService.getInstance();
      await jwtService.login(email.trim(), password);
      
      Alert.alert('Success', 'Login successful!', [
        {
          text: 'OK',
          onPress: onLogin,
        },
      ]);
    } catch (error: any) {
      console.error('Login error:', error);
      Alert.alert(
        'Login Failed',
        error.message || 'Invalid email or password. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDebugLogin = async () => {
    setIsLoading(true);
    try {
      const jwtService = JWTAuthService.getInstance();
      
      // For development, use a test token
      const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3NTgxNzQxOTMsIm9yaWdJYXQiOjE3NTgxNzA1OTN9.CR_PY5neZzPynWXCVPtIyNM2Kg6d_fckIlhlFEEXhWo';
      
      await jwtService.initializeWithToken(testToken);
      
      Alert.alert('Debug Login', 'Logged in as test user', [
        {
          text: 'OK',
          onPress: onLogin,
        },
      ]);
    } catch (error) {
      console.error('Debug login error:', error);
      Alert.alert('Debug Login Failed', 'Could not login with test user');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Icon name="trending-up" size={48} color="#007AFF" />
            <Text style={styles.title}>RichesReach</Text>
            <Text style={styles.subtitle}>Your Financial Future Starts Here</Text>
          </View>

          {/* Login Form */}
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Icon name="mail" size={20} color="#8E8E93" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor="#8E8E93"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputContainer}>
              <Icon name="lock" size={20} color="#8E8E93" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor="#8E8E93"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.eyeIcon}
                onPress={() => setShowPassword(!showPassword)}
              >
                <Icon
                  name={showPassword ? 'eye-off' : 'eye'}
                  size={20}
                  color="#8E8E93"
                />
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.forgotPassword}
              onPress={onNavigateToForgotPassword}
            >
              <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
              onPress={handleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.loginButtonText}>Sign In</Text>
              )}
            </TouchableOpacity>

            {/* Debug Login for Development */}
            {__DEV__ && (
              <TouchableOpacity
                style={styles.debugButton}
                onPress={handleDebugLogin}
                disabled={isLoading}
              >
                <Text style={styles.debugButtonText}>Debug: Login as Test User</Text>
              </TouchableOpacity>
            )}

            <View style={styles.signupContainer}>
              <Text style={styles.signupText}>Don't have an account? </Text>
              <TouchableOpacity onPress={onNavigateToSignUp}>
                <Text style={styles.signupLink}>Sign Up</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 8,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
    height: 56,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#1C1C1E',
  },
  eyeIcon: {
    padding: 4,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotPasswordText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  loginButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  loginButtonDisabled: {
    backgroundColor: '#E5E5EA',
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  debugButton: {
    backgroundColor: '#FF9500',
    borderRadius: 12,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  debugButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  signupText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  signupLink: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
});

export default EnhancedLoginScreen;