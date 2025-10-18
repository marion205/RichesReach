import React, { useState, useRef } from 'react';
import { useMutation, useApolloClient, gql } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_AUTH } from '../../../graphql/auth';
import RestAuthService from '../services/RestAuthService';
import { API_GRAPHQL } from '../../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';

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
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [name, setName] = useState('');
const [loginLoading, setLoginLoading] = useState(false);
const [loginError, setLoginError] = useState<Error | null>(null);
const inFlight = useRef(false);
const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
const client = useApolloClient();
const { login: authLogin } = useAuth();

// REST Auth Service for fallback
const restAuthService = RestAuthService.getInstance();

// REST-based login function
const loginWithRest = async () => {
  if (inFlight.current) return;
  inFlight.current = true;
  
  try {
    console.log('🔄 Trying REST auth...');
    const success = await authLogin(email, password);
    if (success) {
      console.log('✅ REST login successful!');
      onLogin('success');
    } else {
      throw new Error('Login failed');
    }
  } catch (error) {
    console.error('❌ REST login failed:', error);
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
    console.log('🔄 Attempting login...');
    const success = await authLogin(email, password);
    if (success) {
      console.log('✅ Login successful!');
      onLogin('success');
    } else {
      throw new Error('Login failed');
    }
  } catch (error) {
    console.error('❌ Login failed:', error);
    setLoginError(error instanceof Error ? error : new Error('An error occurred'));
    Alert.alert('Login Failed', error instanceof Error ? error.message : 'An error occurred');
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
console.error('Signup error:', err);
}
};
return (
<ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
<Image source={require('../../../../assets/whitelogo1.png')} style={styles.logo} resizeMode="contain" />
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