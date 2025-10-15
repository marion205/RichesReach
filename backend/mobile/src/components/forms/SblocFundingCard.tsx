// components/SblocFundingCard.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Props = {
  onPress: () => void;
  maxBorrow: number;
  aprPct: number;
  portfolioValue?: number;
};

const fmt = (n:number) => `$${Math.max(0, Math.round(n)).toLocaleString()}`;

const SblocFundingCard: React.FC<Props> = ({ onPress, maxBorrow, aprPct, portfolioValue }) => {
  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.iconWrap}><Icon name="shield" size={18} color="#10B981" /></View>
        <Text style={[styles.title, { marginLeft: 8 }]}>Borrow against portfolio</Text>
      </View>
      <Text style={styles.sub}>Up to {fmt(maxBorrow)} available • {(aprPct).toFixed(1)}% APR</Text>
      <TouchableOpacity style={styles.cta} onPress={onPress}>
        <Text style={styles.ctaText}>Estimate & Draw</Text>
        <Icon name="chevron-right" size={18} color="#fff" style={{ marginLeft: 6 }} />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  card:{ 
    backgroundColor:'#FFFFFF', 
    borderRadius:14, 
    padding:16, 
    marginTop:8,
    borderWidth:1,
    borderColor:'#E5E7EB',
    shadowColor:'#000', 
    shadowOffset:{width:0,height:2}, 
    shadowOpacity:0.06, 
    shadowRadius:8,
    elevation:2,
  },
  row:{ 
    flexDirection:'row', 
    alignItems:'center' 
  },
  iconWrap:{ 
    backgroundColor:'#ECFDF5', 
    borderRadius:10, 
    padding:10,
    borderWidth:1,
    borderColor:'#A7F3D0'
  },
  title:{ 
    fontSize:16, 
    fontWeight:'700', 
    color:'#111827' 
  },
  sub:{ 
    color:'#6B7280', 
    marginTop:6, 
    marginBottom:16,
    fontSize:14
  },
  cta:{ 
    flexDirection:'row', 
    alignItems:'center', 
    justifyContent:'center',
    backgroundColor:'#10B981', 
    borderRadius:10, 
    paddingVertical:14,
    shadowColor:'#10B981',
    shadowOffset:{width:0,height:2},
    shadowOpacity:0.2,
    shadowRadius:4,
    elevation:3,
  },
  ctaText:{ 
    color:'#fff', 
    fontWeight:'700',
    fontSize:16
  },
});

export default SblocFundingCard;
