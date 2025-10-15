import React, { memo } from 'react';
import { View, Text, StyleSheet, Pressable, Image, Platform } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { renderWithTickers } from '../utils/tickers';
import PollCard from './PollCard';
import TickerChips from './TickerChips';
import TickerFollowButton from './TickerFollowButton';

const COLORS = {
  bg: '#FFFFFF',
  text: '#111827',
  sub: '#6B7280',
  line: '#E5E7EB',
  primary: '#00cc99',
  up: '#059669',
  down: '#EF4444',
  chip: '#F3F4F6',
};

type PostRowProps = {
  discussion: any;
  onPress?: () => void;
  onUpvote?: () => void;
  onDownvote?: () => void;
  onComment?: () => void;
  onFollow?: (userId: string) => void;
  onShare?: () => void;
  onSave?: () => void;
  onPressTicker?: (symbol: string) => void;
  liveQuotes?: Record<string, { price: number; chg: number }>;
  followedTickerSet?: Set<string>;
};

const PostRow: React.FC<PostRowProps> = ({
  discussion,
  onPress,
  onUpvote,
  onDownvote,
  onComment,
  onFollow,
  onShare,
  onSave,
  onPressTicker,
  liveQuotes,
  followedTickerSet,
}) => {
  const name = discussion?.user?.name ?? 'User';
  const initial = (name?.[0] || 'U').toUpperCase();
  const created = discussion?.createdAt ? new Date(discussion.createdAt) : null;

  return (
    <Pressable
      onPress={onPress}
      android_ripple={{ color: '#E5E7EB' }}
      style={styles.row}
    >
      {/* left avatar */}
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{initial}</Text>
      </View>

      {/* content */}
      <View style={styles.body}>
        {/* header line */}
        <View style={styles.header}>
          <Text style={styles.name}>{name}</Text>
          {created && (
            <Text style={styles.dot}>·</Text>
          )}
          {created && (
            <Text style={styles.meta}>
              {created.toLocaleDateString()}
            </Text>
          )}
          {!!discussion?.stock?.symbol && (
            <View style={styles.stockChip}>
              <Text style={styles.stockChipText}>
                ${discussion.stock.symbol}
              </Text>
            </View>
          )}
          {!!discussion?.stock?.symbol && (
            <TickerFollowButton 
              symbol={discussion.stock.symbol} 
              size="small" 
            />
          )}
          {!!discussion?.discussionType && (
            <View style={[styles.stockChip, { backgroundColor: COLORS.chip }]}>
              <Text style={[styles.stockChipText, { color: COLORS.sub }]}>
                {String(discussion.discussionType || 'unknown').toUpperCase()}
              </Text>
            </View>
          )}
        </View>

        {/* title */}
        {!!discussion?.title && (
          <Text style={styles.title}>
            {discussion.title}
          </Text>
        )}

        {/* content preview with ticker rendering */}
        {!!discussion?.content && (
          <View style={styles.contentContainer}>
            {discussion?.tickers?.length ? (
              <TickerChips
                symbols={discussion.tickers}
                onPressSymbol={onPressTicker}
              />
            ) : (
              <Text style={styles.preview}>
                {String(discussion.content).replace(/\[(IMAGE|VIDEO):\s*[^\]]+\]/g, '').trim()}
              </Text>
            )}
          </View>
        )}

        {/* Prediction specific UI */}
        {discussion?.kind === 'PREDICTION' && discussion?.prediction && (
          <View style={styles.predictionCard}>
            <View style={styles.predictionHeader}>
              <View style={[
                styles.directionChip,
                { backgroundColor: discussion.prediction.direction === 'bullish' ? '#ECFDF5' : '#FEF2F2' }
              ]}>
                <Icon 
                  name={discussion.prediction.direction === 'bullish' ? 'trending-up' : 'trending-down'} 
                  size={14} 
                  color={discussion.prediction.direction === 'bullish' ? '#10B981' : '#EF4444'} 
                />
                <Text style={[
                  styles.directionText,
                  { color: discussion.prediction.direction === 'bullish' ? '#10B981' : '#EF4444' }
                ]}>
                  {discussion.prediction.direction.toUpperCase()}
                </Text>
              </View>
              {discussion.prediction.targetPrice && (
                <Text style={styles.targetText}>
                  Target ${discussion.prediction.targetPrice} in {discussion.prediction.horizonDays}d
                </Text>
              )}
              <Text style={styles.confidenceText}>
                {Math.round(discussion.prediction.confidence * 100)}% confidence
              </Text>
            </View>
          </View>
        )}

        {/* Poll specific UI */}
        {discussion?.kind === 'POLL' && discussion?.poll && (
          <PollCard postId={discussion.id} poll={discussion.poll} />
        )}

        {/* (optional) first image preview if content embeds one */}
        {renderFirstImage(discussion?.content)}

        {/* actions */}
        <View style={styles.actions}>
          <Pressable onPress={onUpvote} hitSlop={8} style={styles.actionBtn}>
            <Icon name="arrow-up" size={16} color={COLORS.up} />
            <Text style={styles.actionText}>{discussion?.score ?? 0}</Text>
          </Pressable>
          <Pressable onPress={onDownvote} hitSlop={8} style={styles.actionBtn}>
            <Icon name="arrow-down" size={16} color={COLORS.down} />
          </Pressable>
          <Pressable onPress={onComment} hitSlop={8} style={styles.actionBtn}>
            <Icon name="message-circle" size={16} color={COLORS.sub} />
            <Text style={styles.actionText}>{discussion?.commentCount ?? 0}</Text>
          </Pressable>
          <Pressable onPress={onShare} hitSlop={8} style={styles.actionBtn}>
            <Icon name="share-2" size={16} color={COLORS.sub} />
          </Pressable>
          <Pressable onPress={onSave} hitSlop={8} style={styles.actionBtn}>
            <Icon name="bookmark" size={16} color={COLORS.sub} />
          </Pressable>
        </View>
      </View>
    </Pressable>
  );
};

function renderFirstImage(content?: string) {
  if (!content) return null;
  const match = /\[IMAGE:\s*([^\]]+)\]/i.exec(content);
  if (!match) return null;
  const uri = match[1].trim();
  return (
    <View style={styles.mediaWrap}>
      <Image source={{ uri }} style={styles.media} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.bg,
  },
  avatar: {
    width: 42, height: 42, borderRadius: 21,
    backgroundColor: COLORS.primary,
    alignItems: 'center', justifyContent: 'center',
    marginRight: 12,
  },
  avatarText: { color: '#fff', fontWeight: '700' },
  body: { 
    flex: 1,
    minWidth: 0, // Allow flex shrinking
    maxWidth: '100%',
  },
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    flexWrap: 'wrap',
    marginBottom: 4,
  },
  name: { color: COLORS.text, fontWeight: '700' },
  dot: { color: COLORS.sub, marginHorizontal: 6 },
  meta: { color: COLORS.sub },
  stockChip: {
    marginLeft: 8,
    paddingHorizontal: 8,
    paddingVertical: Platform.OS === 'ios' ? 3 : 2,
    borderRadius: 999,
    backgroundColor: '#ECFDF5',
  },
  stockChipText: { color: COLORS.primary, fontSize: 12, fontWeight: '700' },
  title: { marginTop: 4, color: COLORS.text, fontSize: 16, fontWeight: '700' },
  preview: { 
    marginTop: 4, 
    color: COLORS.text, 
    lineHeight: 20,
    flexWrap: 'wrap',
    flexShrink: 1,
  },
  contentContainer: { 
    marginTop: 4, 
    flex: 1,
    maxWidth: '100%',
  },
  textContainer: { 
    flexWrap: 'wrap',
    flexDirection: 'row',
    maxWidth: '100%',
  },
  mediaWrap: { marginTop: 10, borderRadius: 12, overflow: 'hidden' },
  media: { width: '100%', height: 180, resizeMode: 'cover' },
  actions: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  actionText: { color: COLORS.sub, fontSize: 12, fontWeight: '600' },
  // Prediction styles
  predictionCard: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  predictionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  directionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  directionText: {
    fontSize: 12,
    fontWeight: '700',
  },
  targetText: {
    fontSize: 12,
    color: COLORS.sub,
    fontWeight: '600',
  },
  confidenceText: {
    fontSize: 12,
    color: COLORS.sub,
    fontWeight: '600',
  },
});

export default memo(PostRow);
