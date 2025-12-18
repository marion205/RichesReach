import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';

interface Room { id: string; title: string; startsAt: string; }

const demoRooms: Room[] = [
  { id: 'r1', title: 'Fireside • Market Open Check-in', startsAt: 'Today 9:15 AM' },
  { id: 'r2', title: 'Fireside • Options Risk Tactics', startsAt: 'Today 4:30 PM' },
];

export default function FiresideRoomsScreen() {
  const navigation = useNavigation<any>();
  console.log('[FiresideRoomsScreen] Component mounted');
  
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Fireside Exchanges</Text>
        <Text style={styles.subtitle}>Invite-only voice rooms with AI facilitation</Text>
      </View>
      <FlatList
        data={demoRooms}
        keyExtractor={(r) => r.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.room} onPress={() => {
            console.log('[FiresideRoomsScreen] Room pressed:', item.id);
            try {
              navigation.navigate('fireside-room');
              console.log('[FiresideRoomsScreen] Navigation successful');
            } catch (error) {
              console.error('[FiresideRoomsScreen] Navigation error:', error);
            }
          }}>
            <Icon name="mic" size={18} color="#8E8E93" />
            <View style={{ flex: 1, marginLeft: 10 }}>
              <Text style={styles.roomTitle}>{item.title}</Text>
              <Text style={styles.roomMeta}>{item.startsAt}</Text>
            </View>
            <Icon name="chevron-right" size={16} color="#8E8E93" />
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  header: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 },
  title: { fontSize: 20, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { fontSize: 13, color: '#6B7280', marginTop: 4 },
  room: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 14, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: '#E5E5EA' },
  roomTitle: { fontSize: 15, fontWeight: '600', color: '#1C1C1E' },
  roomMeta: { fontSize: 12, color: '#6B7280', marginTop: 2 },
});


