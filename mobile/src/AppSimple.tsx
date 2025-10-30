import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const AppSimple = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>RichesReach App</Text>
      <Text style={styles.subtext}>Loading...</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtext: {
    fontSize: 16,
    color: '#666',
    marginTop: 10,
  },
});

export default AppSimple;
