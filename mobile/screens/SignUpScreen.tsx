import React, { useState } from 'react';
import { View, TextInput, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { gql, useMutation } from '@apollo/client';
import { useNavigation } from '@react-navigation/native';

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

export default function SignUpScreen() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [signup, { loading, error }] = useMutation(SIGNUP);
  const navigation = useNavigation();

  const handleSignup = async () => {
    try {
      const res = await signup({ variables: { email, name, password } });
      console.log('✅ User created:', res.data.createUser.user);
      navigation.navigate('Login');
    } catch (err) {
      console.error('Signup error:', err);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.form}>
        <TextInput placeholder="Name" style={styles.input} value={name} onChangeText={setName} />
        <TextInput placeholder="Email" style={styles.input} value={email} onChangeText={setEmail} />
        <TextInput placeholder="Password" secureTextEntry style={styles.input} value={password} onChangeText={setPassword} />

        <TouchableOpacity style={styles.button} onPress={handleSignup}>
          <Text style={styles.buttonText}>{loading ? 'Creating Account...' : 'Sign Up'}</Text>
        </TouchableOpacity>

        {error && <Text style={styles.error}>❌ {error.message}</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  form: { backgroundColor: '#eee', padding: 20, borderRadius: 8 },
  input: { backgroundColor: '#fff', marginBottom: 10, padding: 10, borderRadius: 6 },
  button: { backgroundColor: '#00cc99', padding: 12, borderRadius: 6, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: 'bold' },
  error: { color: 'red', marginTop: 10 },
});