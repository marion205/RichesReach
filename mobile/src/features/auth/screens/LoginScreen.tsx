import React, { useState, useRef } from 'react';
import { useMutation, useApolloClient, gql } from '@apollo/client';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, Image, ScrollView, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_AUTH } from '../../../graphql/auth';
import RestAuthService from '../services/RestAuthService';
import { API_GRAPHQL } from '../../../config/api';

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
const inFlight = useRef(false);
const [signup, { loading: signupLoading, error: signupError }] = useMutation(SIGNUP);
const client = useApolloClient();

// REST Auth Service for fallback
const restAuthService = RestAuthService.getInstance();

// REST-based login function
const loginWithRest = async () => {
  if (inFlight.current) return;
  inFlight.current = true;
  
  try {
    console.log('🔄 Trying REST auth...');
    const { token } = await restAuthService.login(email, password);
    console.log('✅ REST login successful!');
    await AsyncStorage.setItem('token', token);
    // Clear cache safely without resetting store while queries are in flight
    await client.cache.reset();
    onLogin(token);
  } catch (error) {
    console.error('❌ REST login failed:', error);
    Alert.alert('Login Failed', error instanceof Error ? error.message : 'An error occurred');
  } finally {
    inFlight.current = false;
  }
};

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
    // Clear cache safely without resetting store while queries are in flight
    await client.cache.reset();
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
  try {
    // GraphQL endpoint probe for debugging
    const GQL_URL = API_GRAPHQL;
    try {
      const probeResponse = await fetch(GQL_URL, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ query: '{ __typename }' }),
      });
      const probeText = await probeResponse.text();
      console.log('🔌 GraphQL raw response:', probeText);
    } catch (e) {
      console.log('🔌 GraphQL fetch error:', e);
    }

    // Dev fallback for testing
    const USE_MOCK_AUTH = __DEV__;
    if (USE_MOCK_AUTH) {
      // Create a proper mock JWT token with 3 parts (header.payload.signature)
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({ 
        user_id: '1', 
        email: email, 
        username: 'dev',
        exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours from now
      }));
      const signature = btoa('mock-signature-' + Date.now());
      const mockToken = `${header}.${payload}.${signature}`;
      
      const mock = { token: mockToken, user: { id:'1', email, username:'dev' } };
      await AsyncStorage.setItem('token', mock.token);
      // Clear cache safely without resetting store while queries are in flight
    await client.cache.reset();
      onLogin(mock.token);
      return;
    }

    const variables = { email: email.trim(), password };
    let finalToken: string | undefined;
    let lastError: any;

    for (const m of MUTATIONS) {
      try {
        const res = await client.mutate({
          mutation: m.doc,
          variables,
          fetchPolicy: 'no-cache',
          errorPolicy: 'all',
        });

        console.log(`🔎 ${m.key} result:`, JSON.stringify(res, null, 2));

        if (res?.errors?.length) {
          lastError = res.errors[0];
          continue;
        }
        const token = m.pick(res?.data);
        if (token) {
          finalToken = token;
          break;
        }
      } catch (e) {
        lastError = e;
        continue;
      }
    }

    if (!finalToken) {
      console.error('❌ No token from server. Last error:', lastError);
      const msg =
        lastError?.message ||
        lastError?.extensions?.exception?.message ||
        'No token returned from server';
      Alert.alert('Login failed', msg);
      return;
    }

    // success path
    console.log('✅ Logged in. JWT:', finalToken.slice(0, 16) + '…');
    await AsyncStorage.setItem('token', finalToken);
    // Clear cache safely without resetting store while queries are in flight
    await client.cache.reset();
    onLogin(finalToken);
  } catch (e:any) {
    console.error('🌐 Network error:', e);
    Alert.alert('Network error', e?.message ?? 'Could not reach server');
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