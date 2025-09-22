import React, { useState, useRef } from 'react';
import { useMutation, useApolloClient, gql } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_AUTH } from '../../../graphql/auth';

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
const inFlight = useRef(false);
const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
const client = useApolloClient();

const [tokenAuth, { loading: loginLoading, error: loginError }] = useMutation(TOKEN_AUTH, {
  fetchPolicy: "no-cache",          // critical for auth flows
  context: { noRetry: true },       // our retryLink respects this
  onCompleted: async (data) => {
    console.log('🎉 Login completed! Data:', data);
    const token = data?.tokenAuth?.token;
    if (!token) {
      console.error('❌ No token in response:', data);
      throw new Error("No token in tokenAuth response");
    }
    console.log('✅ Token received:', token);
    await AsyncStorage.setItem('token', token);
    console.log('✅ Token stored in AsyncStorage');
    await client.resetStore();
    console.log('✅ Apollo store reset');
    inFlight.current = false;
    console.log('✅ Calling onLogin with token');
    onLogin(token);
  },
  onError: (e) => { 
    console.error('❌ Login error:', e);
    inFlight.current = false; 
  },
});
const handleSignup = async () => {
try {
const res = await signup({ variables: { email, name, password } });
// User created successfully
} catch (err) {
console.error('Signup error:', err);
}
};
const handleLogin = async () => {
  console.log('🚀 Starting login process...');
  
  // Validate inputs
  if (!email.trim() || !password.trim()) {
    console.error('❌ Email or password is empty');
    return;
  }
  
  // Single-flight guard
  if (loginLoading || inFlight.current) {
    console.log('⏳ Login already in progress, skipping...');
    return;
  }
  
  inFlight.current = true;
  console.log('✅ Starting tokenAuth mutation...');
  
  try {
    const loginEmail = email.trim().toLowerCase();
    const loginPassword = password;
    console.log('📤 Sending login request for:', loginEmail);
    
    const result = await tokenAuth({ 
      variables: { 
        email: loginEmail, 
        password: loginPassword 
      }
    });
    
    console.log('📥 TokenAuth result:', result);
    
    // Handle the response directly (since onCompleted is getting wrong data)
    if (result.data?.tokenAuth?.token) {
      console.log('✅ Handling response directly');
      const token = result.data.tokenAuth.token;
      console.log('✅ Token extracted:', token);
      await AsyncStorage.setItem('token', token);
      console.log('✅ Token stored in AsyncStorage');
      await client.resetStore();
      console.log('✅ Apollo store reset');
      inFlight.current = false;
      console.log('✅ Calling onLogin with token');
      onLogin(token);
    } else {
      console.error('❌ No token in result:', result);
      console.error('❌ Result data:', result.data);
      inFlight.current = false;
    }
  } catch (err) {
    console.error('❌ Login failed:', err);
    inFlight.current = false;
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
{loginLoading || inFlight.current ? 'Logging In...' : 'Log In'}
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