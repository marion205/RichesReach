import React, { useEffect, useMemo, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated } from 'react-native';
import { gql, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const COLORS = {
  card: '#fff',
  text: '#111827',
  subtext: '#6B7280',
  primary: '#00cc99',
  border: '#E5E7EB',
  muted: '#F3F4F6',
};

export const VOTE_POLL = gql`
  mutation VotePoll($postId: ID!, $optionId: ID!) {
    votePoll(postId: $postId, optionId: $optionId) {
      success
      post {
        id
        poll {
          options {
            id
            votes
          }
        }
      }
    }
  }
`;

type Opt = { id: string; label: string; votes: number };
type Poll = { question: string; closesAt?: string | null; options: Opt[] };
type Props = { postId: string; poll: Poll };

export default function PollCard({ postId, poll }: Props) {
  const total = useMemo(() => poll.options.reduce((s, o) => s + (o.votes || 0), 0), [poll.options]);
  const [vote] = useMutation(VOTE_POLL);

  // animated widths
  const bars = useRef(poll.options.map(() => new Animated.Value(0))).current;
  useEffect(() => {
    poll.options.forEach((o, i) => {
      const pct = total > 0 ? o.votes / total : 0;
      Animated.timing(bars[i], { toValue: pct, duration: 500, useNativeDriver: false }).start();
    });
  }, [poll.options, total]);

  const onVote = (optionId: string) => {
    // optimistic bump
    vote({
      variables: { postId, optionId },
      optimisticResponse: {
        votePoll: {
          __typename: 'VotePollPayload',
          success: true,
          post: {
            __typename: 'Post',
            id: postId,
            poll: {
              __typename: 'Poll',
              options: poll.options.map((o) => ({
                __typename: 'PollOption',
                id: o.id,
                votes: o.id === optionId ? o.votes + 1 : o.votes,
              })),
            },
          },
        },
      },
    });
  };

  return (
    <View style={s.wrap}>
      <Text style={s.q}>{poll.question}</Text>
      <View style={{ marginTop: 8 }}>
        {poll.options.map((o, i) => {
          const width = bars[i].interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] });
          const pct = total > 0 ? Math.round((o.votes / total) * 100) : 0;
          return (
            <TouchableOpacity
              key={o.id}
              style={s.opt}
              onPress={() => onVote(o.id)}
              activeOpacity={0.9}
            >
              <View style={s.barBg}>
                <Animated.View style={[s.barFill, { width }]} />
              </View>
              <View style={s.optRow}>
                <Text style={s.optLabel}>{o.label}</Text>
                <Text style={s.optPct}>{pct}%</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
      <View style={s.footer}>
        <Text style={s.meta}>{total} votes</Text>
        {poll.closesAt && (
          <View style={s.metaRow}>
            <Icon name="clock" size={12} color={COLORS.subtext} />
            <Text style={s.meta}>Closes {new Date(poll.closesAt).toLocaleDateString()}</Text>
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  q: { fontSize: 16, fontWeight: '700', color: COLORS.text },
  opt: { marginTop: 10 },
  barBg: { height: 28, backgroundColor: COLORS.muted, borderRadius: 8, overflow: 'hidden' },
  barFill: { height: '100%', backgroundColor: COLORS.primary },
  optRow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
  },
  optLabel: { color: COLORS.text, fontWeight: '600' },
  optPct: { color: COLORS.subtext, fontWeight: '700' },
  footer: { marginTop: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  meta: { color: COLORS.subtext, fontSize: 12 },
});
