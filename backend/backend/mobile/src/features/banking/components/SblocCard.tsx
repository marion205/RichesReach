import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

export function SblocCard({ maxBorrowUsd, apr }: { maxBorrowUsd: number; apr: number }) {
  return (
    <View style={{ backgroundColor:'#fff', borderRadius:12, padding:16 }}>
      <Text style={{ fontWeight:'700', fontSize:16 }}>Borrow against your portfolio</Text>
      <Text style={{ marginTop:4, color:'#555' }}>
        Up to ${Math.round(maxBorrowUsd).toLocaleString()} • { (apr*100).toFixed(2)}% APR (est.)
      </Text>
      <TouchableOpacity
        accessibilityLabel="Get SBLOC offers"
        style={{ marginTop:12, backgroundColor:'#111', padding:12, borderRadius:8, flexDirection:'row', alignItems:'center' }}
        onPress={() => {/* navigate to Advanced selector */}}
      >
        <Icon name="zap" size={18} color="#fff" />
        <Text style={{ color:'#fff', marginLeft:8, fontWeight:'600' }}>Get offers</Text>
      </TouchableOpacity>
      <Text style={{ marginTop:8, fontSize:12, color:'#888' }}>
        Not an offer of credit. Terms subject to provider approval.
      </Text>
    </View>
  );
}
