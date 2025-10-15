import React from 'react';
import { View } from 'react-native';
import Shimmer from '../Shimmer';

export function GraphSkeleton() {
  return (
    <View style={{ backgroundColor: '#fff', marginHorizontal: 16, marginTop: 12, borderRadius: 16, padding: 16 }}>
      <Shimmer style={{ width: 140, height: 18, marginBottom: 12 }} />
      <Shimmer style={{ width: '100%', height: 180, borderRadius: 16 }} />
    </View>
  );
}

export function HoldingsSkeleton() {
  return (
    <View style={{ backgroundColor: '#fff', marginHorizontal: 16, marginTop: 12, borderRadius: 16, padding: 16 }}>
      {[...Array(3)].map((_, i) => (
        <View key={i} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
          <Shimmer style={{ width: 36, height: 36, borderRadius: 18, marginRight: 12 }} />
          <View style={{ flex: 1 }}>
            <Shimmer style={{ width: '60%', height: 14, marginBottom: 6 }} />
            <Shimmer style={{ width: '35%', height: 12 }} />
          </View>
          <Shimmer style={{ width: 64, height: 18, marginLeft: 12 }} />
        </View>
      ))}
    </View>
  );
}
