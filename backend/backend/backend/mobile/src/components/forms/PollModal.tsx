import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { gql, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const COLORS = {
  card: '#fff',
  text: '#1F2937',
  subtext: '#6B7280',
  primary: '#00cc99',
  border: '#E2E8F0',
  muted: '#F3F4F6',
};

export const CREATE_POLL = gql`
  mutation CreatePoll($input: CreatePostInput!) {
    createPost(input: $input) {
      success
      message
      post {
        id
        kind
        poll {
          question
          closesAt
          options {
            id
            label
            votes
          }
        }
      }
    }
  }
`;

type Props = {
  visible: boolean;
  onClose: () => void;
  onCreated?: () => void;
};

export default function PollModal({ visible, onClose, onCreated }: Props) {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState<string[]>(['Yes', 'No']);
  const [days, setDays] = useState<number>(3);
  const [createPoll, { loading }] = useMutation(CREATE_POLL);

  const addOption = () => options.length < 5 && setOptions([...options, '']);
  const setOpt = (i: number, v: string) => setOptions(options.map((o, idx) => (idx === i ? v : o)));
  const canPost =
    question.trim().length > 5 && options.filter((o) => o.trim().length > 0).length >= 2;

  const publish = async () => {
    if (!canPost) return;
    await createPoll({
      variables: {
        input: {
          kind: 'POLL',
          content: question.trim(),
          poll: {
            question: question.trim(),
            closesInDays: days,
            options: options
              .filter((o) => o.trim().length > 0)
              .map((label) => ({ label: label.trim() })),
          },
        },
      },
    });
    onCreated?.();
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={st.scrim}
      >
        <View style={st.sheet}>
          <View style={st.header}>
            <Text style={st.title}>Create Poll</Text>
            <TouchableOpacity onPress={onClose}>
              <Icon name="x" size={22} color={COLORS.subtext} />
            </TouchableOpacity>
          </View>

          <Text style={st.label}>Question</Text>
          <TextInput
            style={st.input}
            value={question}
            onChangeText={setQuestion}
            placeholder="Will $NVDA beat EPS next quarter?"
          />

          <Text style={st.label}>Options (2–5)</Text>
          {options.map((opt, i) => (
            <TextInput
              key={i}
              style={st.input}
              value={opt}
              onChangeText={(v) => setOpt(i, v)}
              placeholder={`Option ${i + 1}`}
            />
          ))}
          {options.length < 5 && (
            <TouchableOpacity onPress={addOption} style={st.add}>
              <Icon name="plus" size={16} color={COLORS.primary} />
              <Text style={st.addTxt}>Add option</Text>
            </TouchableOpacity>
          )}

          <Text style={st.label}>Closes in</Text>
          <View style={st.row}>
            {[1, 3, 7, 14].map((d) => (
              <TouchableOpacity
                key={d}
                onPress={() => setDays(d)}
                style={[st.chip, days === d && st.chipActive]}
              >
                <Text style={[st.chipTxt, days === d && st.chipTxtActive]}>
                  {d} day{d > 1 ? 's' : ''}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[st.primary, !canPost && { opacity: 0.6 }]}
            disabled={!canPost || loading}
            onPress={publish}
          >
            <Text style={st.primaryTxt}>{loading ? 'Publishing…' : 'Publish Poll'}</Text>
          </TouchableOpacity>
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
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  title: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  label: { marginTop: 12, marginBottom: 6, color: COLORS.subtext, fontWeight: '600' },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
    backgroundColor: '#fff',
    marginBottom: 8,
  },
  add: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  addTxt: { color: COLORS.primary, fontWeight: '600' },
  row: { flexDirection: 'row', gap: 8 },
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
  primary: { marginTop: 14, backgroundColor: COLORS.primary, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  primaryTxt: { color: '#fff', fontWeight: '700' },
});
