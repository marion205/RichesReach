import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Props = {
  equity: number;                   // total eligible equity basis
  apr?: number;                     // e.g. 8.5 (not 0.085)
  ltv?: number;                     // e.g. 50 (not 0.50)
  eligibleEquity?: number;          // optional: subset of equity that's borrowable
  loading?: boolean;
  onOpenCalculator?: () => void;
  onLearnMore?: () => void;
};

const SblocWidget: React.FC<Props> = ({
  equity,
  apr = 8.5,
  ltv = 50,
  eligibleEquity,
  loading,
  onOpenCalculator,
  onLearnMore,
}) => {
  const base = Number.isFinite(eligibleEquity!) ? Math.max(0, eligibleEquity || 0) : Math.max(0, equity || 0);
  const borrowingPower = Math.floor(base * (ltv / 100));
  const barPct = Math.max(0, Math.min(100, ltv));

  return (
    <View style={ui.card} accessible accessibilityRole="summary" accessibilityLabel="Securities-based line of credit borrowing power">
      {/* Header */}
      <View style={ui.headerRow}>
        <Text style={ui.title}>Borrowing Power</Text>

        {/* APR pill */}
        <View style={ui.aprPill} accessibilityLabel={`APR ${apr}%`}>
          <Text style={ui.aprText}>{apr.toFixed(1)}% APR</Text>
        </View>
      </View>

      {/* Amount row */}
      {loading ? (
        <View style={ui.loadingRow}>
          <ActivityIndicator color="#007AFF" />
          <Text style={ui.loadingText}>Calculating…</Text>
        </View>
      ) : (
        <View style={ui.amountWrap}>
          <Text style={ui.amount}>${borrowingPower.toLocaleString()}</Text>
          <Text style={ui.caption}>Up to {ltv}% of eligible securities</Text>
        </View>
      )}

      {/* Meta tiles */}
      <View style={ui.metaRow}>
        <View style={ui.metaTile}>
          <Text style={ui.metaLabel}>Eligible Equity</Text>
          <Text style={ui.metaValue}>${base.toLocaleString()}</Text>
        </View>
        <View style={ui.metaDivider} />
        <View style={ui.metaTile}>
          <Text style={ui.metaLabel}>LTV</Text>
          <Text style={ui.metaValue}>{ltv}%</Text>
        </View>
      </View>

      {/* Progress (visualizing LTV policy, not utilization) */}
      <View style={ui.progressTrack} accessibilityLabel={`Maximum LTV ${ltv}%`}>
        <View style={[ui.progressFill, { width: `${barPct}%` }]} />
      </View>

      {/* Actions */}
      <View style={ui.actionsRow}>
        <TouchableOpacity
          style={ui.primaryBtn}
          activeOpacity={0.85}
          onPress={onOpenCalculator}
          accessibilityRole="button"
          accessibilityLabel="Estimate and apply"
        >
          <Text style={ui.primaryBtnText}>Estimate & Apply</Text>
          <Icon name="chevron-right" size={16} color="#fff" style={{ marginLeft: 6 }} />
        </TouchableOpacity>

        <TouchableOpacity 
          onPress={onLearnMore || (() => {})} 
          hitSlop={{ top:8, bottom:8, left:8, right:8 }}
        >
          <Text style={ui.linkText}>Learn more</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const ui = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  headerRow:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between' },
  title:{ fontSize:16, fontWeight:'800', color:'#1C1C1E' },
  aprPill:{
    flexDirection:'row', alignItems:'center',
    backgroundColor:'#E7F1FF', borderRadius:999, paddingHorizontal:10, paddingVertical:4,
  },
  aprText:{ color:'#007AFF', fontWeight:'700', fontSize:12 },

  loadingRow:{ flexDirection:'row', alignItems:'center', marginTop:12 },
  loadingText:{ marginLeft:8, color:'#8E8E93' },

  amountWrap:{ marginTop:8 },
  amount:{ fontSize:28, fontWeight:'900', color:'#0F172A' },
  caption:{ marginTop:2, color:'#64748B', fontSize:12, fontWeight:'600' },

  metaRow:{
    flexDirection:'row', alignItems:'center', marginTop:14,
    backgroundColor:'#F8FAFC', borderRadius:12, padding:10,
  },
  metaTile:{ flex:1 },
  metaLabel:{ color:'#94A3B8', fontSize:11, fontWeight:'700', letterSpacing:0.3 },
  metaValue:{ color:'#0F172A', fontSize:14, fontWeight:'800', marginTop:2 },
  metaDivider:{ width:1, height:24, backgroundColor:'#E2E8F0', marginHorizontal:10 },

  progressTrack:{
    height:8, backgroundColor:'#EEF2F6', borderRadius:999, overflow:'hidden', marginTop:12,
  },
  progressFill:{ height:'100%', backgroundColor:'#22C55E' },

  actionsRow:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginTop:14 },
  primaryBtn:{
    flexDirection:'row', alignItems:'center', justifyContent:'center',
    backgroundColor:'#007AFF', borderRadius:10, paddingHorizontal:14, paddingVertical:12,
  },
  primaryBtnText:{ color:'#fff', fontWeight:'800' },
  linkText:{ color:'#007AFF', fontWeight:'700' },
});

export default SblocWidget;