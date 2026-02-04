import React, { useState, useRef } from 'react';
import { useMutation, useApolloClient, gql } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_AUTH } from '../../../graphql/auth';
import RestAuthService from '../services/RestAuthService';
import { API_GRAPHQL } from '../../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';
import { useLoadingTimeout } from '../../../hooks/useLoadingTimeout';
import logger from '../../../utils/logger';

// Three common JWT mutations
const MUTATIONS = [
  {
    key: 'tokenAuth',
    doc: gql`mutation ($email:String!, $password:String!) {
      tokenAuth(email:$email, password:$password) { token user { id email username } }
    }`,
    pick: (d:any) => d?.tokenAuth?.token,
  },
  {
    key: 'tokenCreate',
    doc: gql`mutation ($email:String!, $password:String!) {
      tokenCreate(email:$email, password:$password) { token user { id email username } }
    }`,
    pick: (d:any) => d?.tokenCreate?.token,
  },
  {
    key: 'obtainJSONWebToken',
    doc: gql`mutation ($email:String!, $password:String!) {
      obtainJSONWebToken(email:$email, password:$password) { token }
    }`,
    pick: (d:any) => d?.obtainJSONWebToken?.token,
  },
];

const SIGNUP = gql`
mutation Signup($email: String!, $name: String!, $password: String!) {
createUser(email: $email, name: $name, password: $password) {
user {
id
email
name
}
}
}
`;

export default function LoginScreen({ onLogin, onNavigateToSignUp, onNavigateToForgotPassword }: { onLogin: (token: string) => void; onNavigateToSignUp: () => void; onNavigateToForgotPassword: () => void }) {
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('demo123');
  const [name, setName] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<Error | null>(null);
  const inFlight = useRef(false);
  const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
  const client = useApolloClient();
  const { login: authLogin, isAuthenticated, user } = useAuth();

  // REST Auth Service for fallback
  const restAuthService = RestAuthService.getInstance();

  // Prevent infinite spinner: if login takes >15s, clear loading and alert user
  useLoadingTimeout(loginLoading, {
    timeoutMs: 15000,
    onTimeout: () => {
      setLoginLoading(false);
      inFlight.current = false;
      Alert.alert(
        'Request timed out',
        'Login is taking longer than expected. Please check your connection and try again.'
      );
    },
  });

  // REST-based login function
  const loginWithRest = async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    
    try {
      const success = await authLogin(email, password);
      if (success) {
        onLogin('success');
      } else {
        throw new Error('Login failed');
      }
    } catch (error) {
      logger.error('❌ REST login failed:', error);
      Alert.alert('Login Failed', error instanceof Error ? error.message : 'An error occurred');
    } finally {
      inFlight.current = false;
    }
  };

  // Simplified login function that uses only AuthContext
  const handleLogin = async () => {
    if (inFlight.current || loginLoading) return;
    inFlight.current = true;
    setLoginLoading(true);
    setLoginError(null);
    
    try {
      const success = await authLogin(email, password);
      if (success) {
        // Clear any previous errors before navigating
        setLoginError(null);
        onLogin('success');
        return; // Exit early on success
      } else {
        throw new Error('Login failed: Authentication returned false');
      }
    } catch (error) {
      logger.error('❌ Login failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setLoginError(new Error(errorMessage));
      // Only show alert if login actually failed (don't navigate)
      Alert.alert('Login Failed', errorMessage);
    } finally {
      inFlight.current = false;
      setLoginLoading(false);
    }
  };

  const handleSignup = async () => {
    try {
      const res = await signup({ variables: { email, name, password } });
      // User created successfully
    } catch (err) {
      logger.error('Signup error:', err);
    }
  };


  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Image source={require('../../../../assets/optimized/whitelogo1.webp')} style={styles.logo} resizeMode="contain" />
      <Text style={styles.tagline}>Think Rich. Reach Further.</Text>
      <View style={styles.form}>
        <TextInput
          placeholder="Email"
          placeholderTextColor="#aaa"
          style={styles.input}
          onChangeText={setEmail}
          value={email}
        />
        <TextInput
          placeholder="Password"
          placeholderTextColor="#aaa"
          style={styles.input}
          onChangeText={setPassword}
          value={password}
          secureTextEntry
        />
        <TouchableOpacity 
          style={[styles.button, (loginLoading || inFlight.current) && styles.buttonDisabled]} 
          onPress={handleLogin}
          disabled={loginLoading || inFlight.current}
        >
          <Text style={styles.buttonText}>
            {loginLoading || inFlight.current ? 'Logging In...' : 'Login'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNavigateToForgotPassword}>
          <Text style={{ textAlign: 'center', marginTop: 10, color: '#007aff' }}>
            Forgot Password?
          </Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onNavigateToSignUp}>
          <Text style={{ textAlign: 'center', marginTop: 10, color: '#007aff' }}>
            Don't have an account? Sign up here.
          </Text>
        </TouchableOpacity>
        
        {loginError && <Text style={styles.error}>ERROR: {loginError.message}</Text>}
        {signupError && <Text style={styles.error}>ERROR: {signupError.message}</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  logo: {
    width: '80%',
    height: 200,
    marginBottom: 30,
    resizeMode: 'contain',
  },
  tagline: {
    fontSize: 16,
    fontWeight: '600',
    color: '#00cc99',
    marginTop: -20,
    marginBottom: 20,
  },
  form: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: 'rgba(0,0,0,0.05)',
    borderRadius: 10,
    padding: 20,
  },
  input: {
    backgroundColor: '#fff',
    marginBottom: 15,
    padding: 12,
    borderRadius: 6,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#00cc99',
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  error: {
    color: 'red',
    marginTop: 10,
  },
});