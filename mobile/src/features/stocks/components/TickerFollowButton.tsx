import React, { useMemo } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation, useQuery } from '@apollo/client';
import { FOLLOW_TICKER, GET_MY_FOLLOWS, UNFOLLOW_TICKER } from '../../../tickerFollows';

const C = { primary: '#00cc99', border: '#E5E7EB', text: '#1F2937', muted: '#F3F4F6' };

export default function TickerFollowButton({ symbol, size = 'small' }: { symbol: string; size?: 'small' | 'medium' }) {
  const { data } = useQuery(GET_MY_FOLLOWS, { 
    fetchPolicy: 'cache-first',
    errorPolicy: 'ignore'
  });
  
  const set: Set<string> = useMemo(() => new Set(data?.me?.followedTickers || []), [data]);
  const isFollowing = set.has(symbol);

  const [follow] = useMutation(FOLLOW_TICKER, {
    variables: { symbol },
    optimisticResponse: {
      followTicker: true,
    },
    update(cache) {
      const prev = cache.readQuery<any>({ query: GET_MY_FOLLOWS });
      if (!prev?.me) return;
      const followedTickers = prev.me.followedTickers || [];
      if (followedTickers.includes(symbol)) return;
      cache.writeQuery({
        query: GET_MY_FOLLOWS,
        data: { me: { ...prev.me, followedTickers: [...followedTickers, symbol] } },
      });
    },
  });

  const [unfollow] = useMutation(UNFOLLOW_TICKER, {
    variables: { symbol },
    optimisticResponse: {
      unfollowTicker: true,
    },
    update(cache) {
      const prev = cache.readQuery<any>({ query: GET_MY_FOLLOWS });
      if (!prev?.me) return;
      const followedTickers = prev.me.followedTickers || [];
      cache.writeQuery({
        query: GET_MY_FOLLOWS,
        data: { me: { ...prev.me, followedTickers: followedTickers.filter((s: string) => s !== symbol) } },
      });
    },
  });

  const onPress = () => (isFollowing ? unfollow() : follow());

  return (
    <TouchableOpacity
      onPress={onPress}
      style={[s.btn, size === 'medium' && s.btnMd, isFollowing && s.btnOn]}
      activeOpacity={0.9}
    >
      <Icon name={isFollowing ? 'check' : 'plus'} size={size === 'medium' ? 16 : 14} color={isFollowing ? '#fff' : C.primary} />
      <Text style={[s.txt, isFollowing && s.txtOn]}>{isFollowing ? 'Following' : 'Follow'}</Text>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  btnMd: { paddingHorizontal: 12, paddingVertical: 8 },
  btnOn: { backgroundColor: C.primary, borderColor: C.primary },
  txt: { color: C.primary, fontWeight: '700', fontSize: 12 },
  txtOn: { color: '#fff' },
});
