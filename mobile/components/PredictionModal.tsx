import React, { useMemo, useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { gql, useMutation } from '@apollo/client';
import TickerAutocomplete from './TickerAutocomplete';
import TickerFollowButton from './TickerFollowButton';

const COLORS = {
  card: '#FFFFFF',
  border: '#E2E8F0',
  text: '#1F2937',
  subtext: '#6B7280',
  primary: '#00cc99',
  danger: '#EF4444',
  muted: '#F3F4F6',
};

export const CREATE_PREDICTION = gql`
  mutation CreatePrediction($input: CreatePostInput!) {
    createPost(input: $input) {
      success
      message
      post {
        id
        kind
        title
        tickers
        score
        commentCount
        prediction {
          direction
          horizonDays
          targetPrice
          confidence
        }
        user {
          id
          name
        }
        createdAt
      }
    }
  }
`;

/** Optional fallback if your backend doesn't have createPost yet */
export const CREATE_STOCK_DISCUSSION = gql`
  mutation CreateStockDiscussion(
    $title: String!
    $content: String!
    $stockSymbol: String
    $discussionType: String
    $visibility: String
  ) {
    createStockDiscussion(
      title: $title
      content: $content
      stockSymbol: $stockSymbol
      discussionType: $discussionType
      visibility: $visibility
    ) {
      success
      message
      discussion {
        id
        title
        content
        createdAt
      }
    }
  }
`;

type Dir = 'bullish' | 'bearish' | 'neutral';

type Props = {
  visible: boolean;
  onClose: () => void;
  onCreated?: () => void;
  defaultTicker?: string;
};

export default function PredictionModal({ visible, onClose, onCreated, defaultTicker }: Props) {
  const [symbol, setSymbol] = useState(defaultTicker || '');
  const [dir, setDir] = useState<Dir>('bullish');
  const [horizon, setHorizon] = useState<number>(30);
  const [target, setTarget] = useState<string>('');
  const [confidence, setConfidence] = useState<number>(0.7);
  const [why, setWhy] = useState('');

  const [createPrediction, { loading }] = useMutation(CREATE_PREDICTION);
  const [fallbackCreate] = useMutation(CREATE_STOCK_DISCUSSION);

  const ready = useMemo(
    () => symbol.trim().length > 0 && horizon > 0 && confidence >= 0.5,
    [symbol, horizon, confidence]
  );

  const chip = (label: string, active: boolean, onPress: () => void) => (
    <TouchableOpacity onPress={onPress} style={[st.chip, active && st.chipActive]}>
      <Text style={[st.chipTxt, active && st.chipTxtActive]}>{label}</Text>
    </TouchableOpacity>
  );

  const post = async () => {
    if (!ready) return;

    // preferred: structured API
    try {
      const { data } = await createPrediction({
        variables: {
          input: {
            kind: 'PREDICTION',
            tickers: [symbol.trim().toUpperCase()],
            content: why.trim(),
            prediction: {
              direction: dir,
              horizonDays: horizon,
              targetPrice: target ? Number(target) : null,
              confidence,
            },
          },
        },
      });
      if (data?.createPost?.success) {
        onCreated?.();
        onClose();
        return;
      }
    } catch (e) {
      // fall back to your existing createStockDiscussion (encodes a JSON block)
      const payload = {
        kind: 'PREDICTION',
        direction: dir,
        horizonDays: horizon,
        targetPrice: target ? Number(target) : null,
        confidence,
      };
      await fallbackCreate({
        variables: {
          title: `$${symbol.toUpperCase()} ${dir.toUpperCase()} call`,
          stockSymbol: symbol.toUpperCase(),
          discussionType: 'prediction',
          visibility: 'public',
          content: `${why.trim()}\n\n[PREDICTION:${JSON.stringify(payload)}]`,
        },
      });
      onCreated?.();
      onClose();
    }
  };

  const confSteps = [0.5, 0.6, 0.7, 0.8, 0.9];

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={st.scrim}
      >
        <View style={st.sheet}>
          <View style={st.header}>
            <Text style={st.title}>Make a Call</Text>
            <TouchableOpacity onPress={onClose}>
              <Icon name="x" size={22} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {/* Ticker */}
          <Text style={st.label}>Ticker</Text>
          <TickerAutocomplete
            value={symbol}
            onChangeText={setSymbol}
            onSelect={(row) => setSymbol(row.symbol)}
            placeholder="e.g., AAPL"
            autoFocus
          />
          {symbol && (
            <View style={{ marginTop: 6 }}>
              <TickerFollowButton symbol={symbol.toUpperCase()} size="medium" />
            </View>
          )}

          {/* Direction */}
          <Text style={st.label}>Direction</Text>
          <View style={st.row}>
            {chip('Bullish', dir === 'bullish', () => setDir('bullish'))}
            {chip('Bearish', dir === 'bearish', () => setDir('bearish'))}
            {chip('Neutral', dir === 'neutral', () => setDir('neutral'))}
          </View>

          {/* Horizon */}
          <Text style={st.label}>Time Horizon</Text>
          <View style={st.row}>
            {[7, 14, 30, 60, 90].map((d) => chip(`${d}d`, horizon === d, () => setHorizon(d)))}
          </View>

          {/* Target price & confidence */}
          <View style={[st.row, { marginTop: 8 }]}>
            <View style={{ flex: 1 }}>
              <Text style={st.label}>Target Price (optional)</Text>
              <TextInput
                keyboardType="decimal-pad"
                value={target}
                onChangeText={setTarget}
                placeholder="$"
                style={st.input}
              />
            </View>
            <View style={{ width: 14 }} />
            <View style={{ flex: 1 }}>
              <Text style={st.label}>Confidence</Text>
              <View style={st.rowWrap}>
                {confSteps.map((c) =>
                  chip(`${Math.round(c * 100)}%`, confidence === c, () => setConfidence(c))
                )}
              </View>
            </View>
          </View>

          {/* Rationale */}
          <Text style={st.label}>Why?</Text>
          <TextInput
            style={[st.input, { height: 100, textAlignVertical: 'top' }]}
            multiline
            placeholder="Your brief thesis (channel checks, catalysts, valuation, etc.)"
            value={why}
            onChangeText={setWhy}
            maxLength={800}
          />

          {/* CTA */}
          <TouchableOpacity
            style={[st.primary, !ready && { opacity: 0.6 }]}
            disabled={!ready || loading}
            onPress={post}
          >
            <Text style={st.primaryTxt}>{loading ? 'Publishing…' : 'Publish Prediction'}</Text>
          </TouchableOpacity>

          <Text style={st.note}>
            Educational discussion. No non-public insider info. By posting you attest this is public
            information.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const st = StyleSheet.create({
  scrim: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' },
  sheet: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 16,
    maxHeight: '92%',
  },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  title: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  label: { marginTop: 12, marginBottom: 6, color: COLORS.subtext, fontWeight: '600' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  rowWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 999,
    backgroundColor: COLORS.muted,
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipTxt: { color: '#374151', fontWeight: '600' },
  chipTxtActive: { color: '#fff' },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  primary: { marginTop: 16, backgroundColor: COLORS.primary, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  primaryTxt: { color: '#fff', fontWeight: '700' },
  note: { marginTop: 10, color: COLORS.subtext, fontSize: 12, textAlign: 'center' },
});
