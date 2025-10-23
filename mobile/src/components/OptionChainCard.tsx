import React from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, Modal, TouchableOpacity, Dimensions } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { UI } from '../shared/constants';

/* ===================== Types ===================== */

type Side = 'CALL' | 'PUT';

type Greeks = {
  delta?: number;
  gamma?: number;
  theta?: number;  // per day
  vega?: number;   // per 1% IV
  rho?: number;
  iv?: number;     // 0..1
  probITM?: number;// 0..1
};

type Row = {
  strike: number;
  bid: number;
  ask: number;
  volume: number;
  optionType: Side;
  greeks?: Greeks;
};

type Selected = Row & { expiration: string };
type Density = 'compact' | 'comfortable' | 'spacious';
type Mode = 'market' | 'greeks';

const AUTO_DENSITY: Density = (() => {
  const w = Dimensions.get('window').width;
  if (w <= 360) return 'compact';
  if (w <= 400) return 'comfortable';
  return 'spacious';
})();

type Props = {
  symbol: string;
  expiration: string;           // e.g. "2024-02-16"
  underlyingPrice?: number;
  calls: Row[];
  puts: Row[];
  selected?: Selected | null;
  onSelect: (o: Selected) => void;
  density?: Density;            // default 'spacious'
  defaultMode?: Mode;           // default 'market'
  fullBleed?: boolean;          // default false
  gutter?: number;              // default 20, used to cancel page padding
};

/* ===================== Utils ===================== */

const money = (n?: number) =>
  Number.isFinite(n) ? `$${(Number(n) || 0).toFixed(2)}` : '—';

const num = (n?: number, dp = 2) =>
  Number.isFinite(n) ? (Number(n) || 0).toFixed(dp) : '—';

const pct = (n?: number, dp = 0) =>
  Number.isFinite(n) ? `${((Number(n) || 0) * 100).toFixed(dp)}%` : '—';

const volFmt = (n?: number) =>
  Number.isFinite(n) ? (n! >= 1000 ? `${((n || 0) / 1000).toFixed(1)}k` : String(n)) : '—';

const spreadColor = (bid?: number, ask?: number) => {
  if (!Number.isFinite(bid) || !Number.isFinite(ask)) return '#ef4444';
  const mid = ((bid as number) + (ask as number)) / 2;
  const spr = (ask as number) - (bid as number);
  const pct = spr / Math.max(0.01, mid);
  if (pct < 0.02) return '#16a34a'; // tight
  if (pct < 0.05) return '#f59e0b'; // okay
  return '#ef4444';                 // wide
};

const isITM = (row: Row, underlying?: number) => {
  if (!Number.isFinite(underlying)) return false;
  return row.optionType === 'CALL'
    ? row.strike < (underlying as number)
    : row.strike > (underlying as number);
};

/* ===================== Help Copy ===================== */

type Topic =
  | 'mode' | 'strike' | 'bid' | 'ask' | 'vol' | 'action'
  | 'delta' | 'gamma' | 'theta' | 'vega' | 'iv' | 'probITM'
  | 'itm' | 'spread';

const HELP: Record<Topic, { title: string; body: string[] }> = {
  mode: {
    title: 'Market vs Greeks',
    body: [
      'Market shows tradable fields (Bid/Ask/Volume).',
      'Greeks shows risk sensitivities (Δ, Γ, Θ, Vega, IV).',
      'Use Greeks to understand how price/time/volatility impact an option.',
    ],
  },
  strike: { title: 'Strike', body: ['The price at which you can buy (call) or sell (put) the underlying if exercised.'] },
  bid:    { title: 'Bid',    body: ['Highest price buyers are willing to pay. Often lower than Ask. Mid ≈ (Bid + Ask) / 2.'] },
  ask:    { title: 'Ask',    body: ['Lowest price sellers will accept. Tight spreads are generally better for trading.'] },
  vol:    { title: 'Volume', body: ['Number of contracts traded today. Higher volume can imply better liquidity.'] },
  action: { title: 'Action', body: ['Tap Select to stage an order with this contract.'] },
  delta:  { title: 'Delta (Δ)', body: ['Approximate $ change in option price per $1 move in the underlying.', 'Also approximates probability of being in-the-money at expiration.'] },
  gamma:  { title: 'Gamma (Γ)', body: ['Rate of change of Delta per $1 move in the underlying. High Γ = Delta can change quickly.'] },
  theta:  { title: 'Theta (Θ)', body: ['Daily time decay of the option price. Usually negative for long options.'] },
  vega:   { title: 'Vega', body: ['Change in option price for a 1% change in implied volatility (IV).'] },
  iv:     { title: 'Implied Volatility (IV)', body: ['Market-implied future volatility. Higher IV → higher option prices.'] },
  probITM:{ title: 'Prob. ITM', body: ['Estimated probability the option expires in-the-money.'] },
  itm:    { title: 'In The Money (ITM)', body: ['Calls ITM when Strike < Underlying. Puts ITM when Strike > Underlying.'] },
  spread: { title: 'Bid–Ask Spread', body: ['Difference between ask and bid. Tight spreads reduce slippage.'] },
};

/* ===================== Component ===================== */

export default function OptionChainCard({
  symbol,
  expiration,
  underlyingPrice,
  calls,
  puts,
  selected,
  onSelect,
  density = AUTO_DENSITY,
  defaultMode = 'market',
  fullBleed = false,
  gutter = 20,
}: Props) {
  const [mode, setMode] = React.useState<Mode>(defaultMode);
  const [helpTopic, setHelpTopic] = React.useState<Topic | null>(null);
  const st = React.useMemo(() => makeStyles(density, fullBleed, gutter), [density, fullBleed, gutter]);

  return (
    <View style={st.card}>
      {/* Header */}
      <View style={st.cardHeader}>
        <View style={{ flex: 1 }}>
          <Text style={st.title}>Options Chain — {symbol}</Text>
          <Text style={st.subtitle}>Expiration: {expiration}</Text>
        </View>

        {Number.isFinite(underlyingPrice) && (
          <View style={st.underlyingPill}>
            <Text style={st.underlyingText}>Underlying {money(underlyingPrice)}</Text>
          </View>
        )}

        <Pressable onPress={() => setHelpTopic('mode')} style={st.helpIconBtn} accessibilityLabel="Help">
          <Icon name="help-circle" size={20} color="#6b7280" />
        </Pressable>
      </View>

      {/* Segmented Control */}
      <View style={st.segment}>
        <Pressable
          onPress={() => setMode('market')}
          style={[st.segmentBtn, mode === 'market' && st.segmentOn]}
          accessibilityRole="button"
          accessibilityState={{ selected: mode === 'market' }}
        >
          <Text style={[st.segmentText, mode === 'market' && st.segmentTextOn]}>Market</Text>
        </Pressable>
        <Pressable
          onPress={() => setMode('greeks')}
          style={[st.segmentBtn, mode === 'greeks' && st.segmentOn]}
          accessibilityRole="button"
          accessibilityState={{ selected: mode === 'greeks' }}
        >
          <Text style={[st.segmentText, mode === 'greeks' && st.segmentTextOn]}>Greeks</Text>
        </Pressable>
      </View>

      {/* Calls */}
      <OptionsSide
        label="Calls"
        side="CALL"
        data={calls}
        expiration={expiration}
        selected={selected}
        onSelect={onSelect}
        underlyingPrice={underlyingPrice}
        mode={mode}
        openTopic={setHelpTopic}
        st={st}
      />

      <View style={st.sectionSpacer} />

      {/* Puts */}
      <OptionsSide
        label="Puts"
        side="PUT"
        data={puts}
        expiration={expiration}
        selected={selected}
        onSelect={onSelect}
        underlyingPrice={underlyingPrice}
        mode={mode}
        openTopic={setHelpTopic}
        st={st}
      />

      {/* Footnote */}
      <View style={st.footer}>
        <Text style={st.footText}>Prices are illustrative. Options involve risk and are not suitable for all investors.</Text>
      </View>

      {/* Help Modal */}
      <HelpModal topic={helpTopic} onClose={() => setHelpTopic(null)} />
    </View>
  );
}

function OptionsSide({
  label, side, data, expiration, selected, onSelect, underlyingPrice, mode, openTopic, st,
}: {
  label: string; side: Side; data: Row[]; expiration: string;
  selected?: Selected | null; onSelect: (o: Selected) => void;
  underlyingPrice?: number; mode: Mode;
  openTopic: (t: Topic) => void; st: ReturnType<typeof makeStyles>;
}) {
  const Header = (
    <View style={st.sectionHeader}>
      <View style={st.sideRow}>
        <Text style={st.sideTitle}>{label}</Text>
        <Pressable onPress={() => openTopic('itm')} style={st.infoPill}>
          <Icon name="info" size={12} color="#64748b" />
          <Text style={st.infoPillText}>What is ITM?</Text>
        </Pressable>
      </View>

             {/* Column headers vary by mode */}
             {mode === 'market' ? (
               <View style={st.headerRow}>
                 <View style={st.colStrike}>
                   <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                     <Text style={st.hText}>Strike</Text>
                     <Pressable onPress={() => openTopic('strike')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>Bid</Text>
                     <Pressable onPress={() => openTopic('bid')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>Ask</Text>
                     <Pressable onPress={() => openTopic('ask')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>Vol</Text>
                     <Pressable onPress={() => openTopic('vol')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colAct}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }}>
                     <Text style={[st.hText, st.hCenter]}>Action</Text>
                     <Pressable onPress={() => openTopic('action')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
               </View>
             ) : (
               <View style={st.headerRow}>
                 <View style={st.colStrike}>
                   <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                     <Text style={st.hText}>Strike</Text>
                     <Pressable onPress={() => openTopic('strike')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>Δ</Text>
                     <Pressable onPress={() => openTopic('delta')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>Θ</Text>
                     <Pressable onPress={() => openTopic('theta')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colNum}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end' }}>
                     <Text style={[st.hText, st.hRight]}>IV</Text>
                     <Pressable onPress={() => openTopic('iv')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
                 <View style={st.colAct}>
                   <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }}>
                     <Text style={[st.hText, st.hCenter]}>Action</Text>
                     <Pressable onPress={() => openTopic('action')} hitSlop={6} style={{ marginLeft: 4 }}>
                       <Icon name="info" size={12} color="#94a3b8" />
                     </Pressable>
                   </View>
                 </View>
               </View>
             )}
    </View>
  );

  return (
    <FlatList
      data={data}
      keyExtractor={(r) => `${side}-${r.strike}`}
      ListHeaderComponent={Header}
      ListHeaderComponentStyle={st.headerBottomSpace}
      ItemSeparatorComponent={() => <View style={st.itemSeparator} />}
      renderItem={({ item }) => (
        <OptionRow
          row={item}
          isSelected={selected?.strike === item.strike && selected?.optionType === item.optionType}
          onPress={() => onSelect({ ...item, expiration })}
          itm={isITM(item, underlyingPrice)}
          mode={mode}
          st={st}
        />
      )}
      contentContainerStyle={st.listContent}
      initialNumToRender={12}
      windowSize={10}
      removeClippedSubviews
    />
  );
}


function OptionRow({
  row, isSelected, onPress, itm, mode, st,
}: {
  row: Row; isSelected: boolean; onPress: () => void; itm: boolean; mode: Mode;
  st: ReturnType<typeof makeStyles>;
}) {
  const mid = (row.bid + row.ask) / 2;
  const sprColor = spreadColor(row.bid, row.ask);

         return (
           <Pressable
             onPress={onPress}
             accessibilityRole="button"
             style={({ pressed }) => [
               st.row,
               itm && st.rowITM,
               isSelected && st.rowSelected,
               pressed && st.rowPressed,
             ]}
             android_ripple={{ color: '#e5e7eb' }}
           >
             {/* Strike */}
             <View style={st.colStrike}>
               <Text style={st.cellStrike}>{row.strike}</Text>
             </View>
       
             {mode === 'market' ? (
               <>
                 {/* Bid */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{money(row.bid)}</Text>
                   <Text style={st.subTiny}>mid {money(mid)}</Text>
                 </View>
       
                 {/* Ask */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{money(row.ask)}</Text>
                   <Text style={[st.subTiny, { color: sprColor }]}>spr {((row.ask || 0) - (row.bid || 0)).toFixed(2)}</Text>
                 </View>
       
                 {/* Vol */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{volFmt(row.volume)}</Text>
                 </View>
               </>
             ) : (
               <>
                 {/* Δ */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{num(row.greeks?.delta, 2)}</Text>
                   <Text style={st.subTiny}>Γ {num(row.greeks?.gamma, 3)}</Text>
                 </View>
       
                 {/* Θ */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{num(row.greeks?.theta, 2)}</Text>
                   <Text style={st.subTiny}>Vega {num(row.greeks?.vega, 2)}</Text>
                 </View>
       
                 {/* IV */}
                 <View style={st.colNum}>
                   <Text style={st.cellNum}>{pct(row.greeks?.iv, 0)}</Text>
                 </View>
               </>
             )}
       
             {/* Action */}
             <View style={st.colAct}>
               <View style={[st.selectPill, isSelected && st.selectPillOn]}>
                 {isSelected ? (
                   <>
                     <Icon name="check" size={10} color="#fff" />
                     <Text style={st.selectTextOn}>Selected</Text>
                   </>
                 ) : (
                   <>
                     <Icon name="plus" size={10} color={UI?.colors?.accent ?? '#00cc99'} />
                     <Text style={st.selectText}>Select</Text>
                   </>
                 )}
               </View>
             </View>
           </Pressable>
         );
}

/* ===================== Help Modal ===================== */

function HelpModal({ topic, onClose }: { topic: Topic | null; onClose: () => void }) {
  if (!topic) return null;
  const copy = HELP[topic];
  return (
    <Modal transparent animationType="fade" onRequestClose={onClose}>
      <View style={sBase.overlay}>
        <View style={sBase.sheet}>
          <View style={sBase.sheetHeader}>
            <Text style={sBase.sheetTitle}>{copy.title}</Text>
            <TouchableOpacity onPress={onClose} style={{ padding: 6 }}>
              <Icon name="x" size={22} color="#6b7280" />
            </TouchableOpacity>
          </View>
          {copy.body.map((p, i) => (
            <Text key={i} style={sBase.sheetText}>• {p}</Text>
          ))}
        </View>
      </View>
    </Modal>
  );
}

/* ===================== Styles ===================== */

function makeStyles(density: Density, fullBleed: boolean, gutter: number) {
  // compact: 0.95, comfortable: 1.05, spacious: 1.2 (slightly gentler than before)
  const mult = density === 'compact' ? 0.95 : density === 'comfortable' ? 1.05 : 1.2;
  const space = (n: number) => Math.round(n * mult);

  // column proportions (use the SAME in header and rows)
  const ACT_W = 80;        // fixed action width prevents wrap
  const STRIKE_FLEX = 1.2;
  const NUM_FLEX = 1;

  return StyleSheet.create({
    /* Card */
    card: {
      backgroundColor: '#fff',
      borderRadius: fullBleed ? 0 : 12,
      paddingVertical: space(12),
      paddingHorizontal: fullBleed ? gutter : space(12),
      marginHorizontal: fullBleed ? -gutter : space(14),
      marginVertical: 12,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.08,
      shadowRadius: 5,
      elevation: 2,
    },
    cardHeader: {
      flexDirection: 'row', alignItems: 'center',
      marginBottom: space(6),
    },
    title: { fontSize: 17, fontWeight: '700', color: '#111' },
    subtitle: { fontSize: 11, color: '#6b7280', marginTop: 1 },
    underlyingPill: {
      marginLeft: 'auto',
      backgroundColor: '#f1f5f9',
      paddingHorizontal: space(8),
      paddingVertical: space(5),
      borderRadius: 999,
    },
    underlyingText: { color: '#111827', fontWeight: '600', fontSize: 12 },
    helpIconBtn: { marginLeft: space(8), padding: 6 },

    /* Segmented toggle */
    segment: {
      flexDirection: 'row',
      backgroundColor: '#f1f5f9',
      borderRadius: 10,
      padding: 2,
      marginTop: space(8),
      marginBottom: space(4),
    },
    segmentBtn: { flex: 1, alignItems: 'center', paddingVertical: space(7), borderRadius: 8 },
    segmentOn: { backgroundColor: UI?.colors?.accent ?? '#00cc99' },
    segmentText: { fontSize: 12, fontWeight: '700', color: '#475569' },
    segmentTextOn: { color: '#fff' },

    /* Section + headers */
    sectionHeader: { marginTop: space(10) },
    sideRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    sideTitle: { fontSize: 15, fontWeight: '800', color: '#111' },
    infoPill: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#eef2f7', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999 },
    infoPillText: { marginLeft: 4, fontSize: 11, color: '#64748b', fontWeight: '600' },

    headerRow: {
      flexDirection: 'row', alignItems: 'center',
      paddingVertical: space(10),
      borderBottomWidth: 1, borderBottomColor: '#eef2f7',
      marginTop: space(8),
    },
    headerBottomSpace: { marginBottom: space(6) },

    /* shared column wrappers — use these for BOTH header and rows */
    colStrike: { flex: STRIKE_FLEX },
    colNum:    { flex: NUM_FLEX, alignItems: 'flex-end' },
    colAct:    { width: ACT_W, alignItems: 'center' },

    hText: { fontSize: 11, fontWeight: '700', color: '#64748b' },
    hRight: { textAlign: 'right' as const },
    hCenter:{ textAlign: 'center' as const },

    /* List & rows */
    listContent: { paddingBottom: space(14) },
    itemSeparator: { height: space(6) },

    row: {
      flexDirection: 'row', alignItems: 'center',
      minHeight: Math.max(46, space(44)),
      paddingVertical: space(10),
      paddingHorizontal: space(6),
      borderWidth: 1, borderColor: '#eef2f7',
      borderRadius: 10,
      backgroundColor: '#fff',
    },
    rowPressed: { opacity: 0.96 },
    rowSelected: { backgroundColor: '#ecfdf5', borderColor: '#bbf7d0' },
    rowITM: { backgroundColor: '#f8fafc' },

    /* Cells */
    cellStrike: {
      flex: STRIKE_FLEX, fontSize: 14, fontWeight: '800', color: '#111827',
      fontVariant: ['tabular-nums'],
    },
    cellNumWrap: { flex: NUM_FLEX, alignItems: 'flex-end' },
    cellNum: { fontSize: 14, fontWeight: '700', color: '#111827', fontVariant: ['tabular-nums'] },
    subTiny: { fontSize: 10, color: '#6b7280', marginTop: 3, fontVariant: ['tabular-nums'] },

    /* Action */
    actWrap: { width: ACT_W, alignItems: 'center' },
    selectPill: {
      flexDirection: 'row', alignItems: 'center',
      borderRadius: 999, paddingVertical: space(4), paddingHorizontal: space(6),
      backgroundColor: '#ecfeff',
      borderWidth: 1, borderColor: UI?.colors?.accent ?? '#00cc99',
      gap: 3,
    },
    selectPillOn: { backgroundColor: UI?.colors?.accent ?? '#00cc99', borderColor: UI?.colors?.accent ?? '#00cc99' },
    selectText: { fontSize: 10, fontWeight: '800', color: UI?.colors?.accent ?? '#00cc99' },
    selectTextOn: { fontSize: 10, fontWeight: '800', color: '#fff' },

    /* Spacers & footer */
    sectionSpacer: { height: space(16) },
    footer: { alignItems: 'center', marginTop: space(8) },
    footText: { fontSize: 11, color: '#9ca3af' },
  });
}

const sBase = StyleSheet.create({
  hCell: { fontSize: 11, fontWeight: '700', color: '#6b7280' },
  overlay: {
    position: 'absolute', top: 0, right: 0, bottom: 0, left: 0,
    backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center',
  },
  sheet: {
    width: '90%', maxWidth: 480,
    backgroundColor: '#fff', borderRadius: 16, padding: 18,
    shadowColor: '#000', shadowOpacity: 0.15, shadowRadius: 12, elevation: 5,
  },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  sheetTitle: { fontSize: 18, fontWeight: '800', color: '#111' },
  sheetText: { fontSize: 14, color: '#344054', lineHeight: 20, marginTop: 6 },
});