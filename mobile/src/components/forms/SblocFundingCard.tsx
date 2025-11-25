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
  const handlePress = () => {
    console.log('🔵 SblocFundingCard: Button pressed, calling onPress');
    console.log('🔵 SblocFundingCard: onPress type:', typeof onPress);
    console.log('🔵 SblocFundingCard: onPress value:', onPress);
    if (onPress) {
      console.log('🔵 SblocFundingCard: Calling onPress now...');
      try {
        onPress();
        console.log('✅ SblocFundingCard: onPress called successfully');
      } catch (error) {
        console.error('❌ SblocFundingCard: Error calling onPress:', error);
      }
    } else {
      console.error('❌ SblocFundingCard: onPress is not defined!');
    }
  };

  return (
    <View style={styles.card} pointerEvents="box-none">
      <View style={styles.row}>
        <View style={styles.iconWrap}><Icon name="shield" size={18} color="#10B981" /></View>
        <Text style={[styles.title, { marginLeft: 8 }]}>Borrow against portfolio</Text>
      </View>
      <Text style={styles.sub}>Up to {fmt(maxBorrow)} available • {(aprPct || 0).toFixed(1)}% APR</Text>
      <TouchableOpacity 
        style={styles.cta} 
        onPress={handlePress}
        onPressIn={() => {
          console.log('🔵 SblocFundingCard: onPressIn triggered');
        }}
        onPressOut={() => {
          console.log('🔵 SblocFundingCard: onPressOut triggered');
        }}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityLabel="Estimate and draw from portfolio"
        hitSlop={{ top: 20, bottom: 20, left: 20, right: 20 }}
        disabled={false}
        delayPressIn={0}
        delayPressOut={0}
      >
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
    overflow: 'visible',
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
    paddingHorizontal:16,
    shadowColor:'#10B981',
    shadowOffset:{width:0,height:2},
    shadowOpacity:0.2,
    shadowRadius:4,
    elevation:3,
    minHeight:48,
    zIndex:10,
  },
  ctaText:{ 
    color:'#fff', 
    fontWeight:'700',
    fontSize:16
  },
});

export default SblocFundingCard;
