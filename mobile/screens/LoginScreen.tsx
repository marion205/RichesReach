import React, { useState } from 'react';
import { gql, useMutation, useApolloClient } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
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

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
  const [tokenAuth, { loading: loginLoading, error: loginError }] = useMutation(LOGIN);
  const client = useApolloClient();

  const handleSignup = async () => {
    try {
      const res = await signup({ variables: { email, name, password } });
      console.log('✅ User created:', res.data.createUser.user);
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
      // Clear Apollo cache before login attempt
      await client.clearStore();
      console.log('Apollo cache cleared');
      
      const loginEmail = email.trim().toLowerCase();
      const loginPassword = password;
      
      console.log('Attempting login with:', { 
        email: loginEmail, 
        password: loginPassword ? '***' : 'empty',
        emailLength: loginEmail.length,
        passwordLength: loginPassword.length
      });
      
      // Test the exact mutation that will be sent
      const testQuery = `
        mutation TokenAuth($email: String!, $password: String!) {
          tokenAuth(email: $email, password: $password) {
            token
          }
        }
      `;
      console.log('GraphQL Query:', testQuery);
      console.log('Variables:', { email: loginEmail, password: loginPassword });
      
      const response = await tokenAuth({ 
        variables: { 
          email: loginEmail, 
          password: loginPassword 
        },
        errorPolicy: 'all'
      });
      
      if (response.errors) {
        console.error('Response errors:', response.errors);
        throw new Error('GraphQL errors in response');
      }
      
      const token = response.data?.tokenAuth?.token;
      if (!token) {
        console.error('No token in response:', response);
        throw new Error('No token received');
      }
      
      console.log('✅ Logged in! Token:', token);
      
      // Store the token for future requests
      await AsyncStorage.setItem('token', token);
      
      navigation.replace('Home');
    } catch (err) {
      console.error('Login failed:', err);
      console.error('Error details:', {
        message: err?.message,
        graphQLErrors: err?.graphQLErrors,
        networkError: err?.networkError,
        fullError: err
      });
      
      // Log the exact error message
      if (err?.graphQLErrors) {
        err.graphQLErrors.forEach((error, index) => {
          console.error(`GraphQL Error ${index}:`, error);
        });
      }
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

        <TouchableOpacity onPress={() => navigation.navigate('SignUp')}>
          <Text style={{ textAlign: 'center', marginTop: 10, color: '#007aff' }}>
            Don't have an account? Sign up here.
          </Text>
        </TouchableOpacity>

        {loginError && <Text style={styles.error}>❌ {loginError.message}</Text>}
        {signupError && <Text style={styles.error}>❌ {signupError.message}</Text>}
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