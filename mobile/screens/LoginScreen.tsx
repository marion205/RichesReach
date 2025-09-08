import React, { useState } from 'react';
import { gql, useMutation, useApolloClient } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';


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

const LOGIN = gql`
  mutation TokenAuth($email: String!, $password: String!) {
    tokenAuth(email: $email, password: $password) {
      token
    }
  }
`;

export default function LoginScreen({ onLogin, onNavigateToSignUp, onNavigateToForgotPassword }: { onLogin: (token: string) => void; onNavigateToSignUp: () => void; onNavigateToForgotPassword: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
  const [tokenAuth, { loading: loginLoading, error: loginError }] = useMutation(LOGIN);
  const client = useApolloClient();

  const handleSignup = async () => {
    try {
      const res = await signup({ variables: { email, name, password } });
      // User created successfully
    } catch (err) {
      console.error('Signup error:', err);
    }
  };

  const handleLogin = async () => {
    // Validate inputs
    if (!email.trim() || !password.trim()) {
      console.error('Email or password is empty');
      return;
    }
    
    try {
      const loginEmail = email.trim().toLowerCase();
      const loginPassword = password;
      
      const response = await tokenAuth({ 
        variables: { 
          email: loginEmail, 
          password: loginPassword 
        },
        errorPolicy: 'all'
      });
      
      if (response.errors) {
        throw new Error('GraphQL errors in response');
      }
      
      const token = response.data?.tokenAuth?.token;
      if (!token) {
        throw new Error('No token received');
      }
      
      // Store the token for future requests
      await AsyncStorage.setItem('token', token);
      
      onLogin(token);
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Image source={require('../assets/whitelogo1.png')} style={styles.logo} resizeMode="contain" />

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

        <TouchableOpacity style={styles.button} onPress={handleLogin}>
          <Text style={styles.buttonText}>
            {loginLoading ? 'Logging In...' : 'Log In'}
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