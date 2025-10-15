import React, { memo, useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Props = {
  discussion: any;
  onPress: (id: string) => void;
  onUpvote: (id: string) => void;
  onDownvote: (id: string) => void;
  onComment: (id: string) => void;
  onFollow: (userId: string) => void;
};

const timeAgo = (iso?: string) => {
  if (!iso) return '';
  const d = new Date(iso).getTime();
  const diff = Math.max(1, Math.round((Date.now() - d) / 1000));
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
};

const DiscussionItem = memo<Props>(({ discussion, onPress, onUpvote, onDownvote, onComment, onFollow }) => {
  const score = discussion?.score ?? 0;
  const name = discussion?.user?.name || 'user';
  const created = timeAgo(discussion?.createdAt);
  const stockSymbol = discussion?.stock?.symbol;
  const commentCount = discussion?.commentCount ?? 0;

  const title = discussion?.title ?? '';
  const contentPreview = useMemo(() => {
    const clean = (discussion?.content || '').replace(/\[(IMAGE|VIDEO):\s*[^\]]+\]/g, '').trim();
    return clean.length > 160 ? `${clean.slice(0, 160)}…` : clean;
  }, [discussion?.content]);

  return (
    <TouchableOpacity style={styles.postRow} activeOpacity={0.85} onPress={() => onPress(discussion.id)}>
      <View style={styles.voteCol}>
        <TouchableOpacity style={styles.voteBtn} onPress={() => onUpvote(discussion.id)}>
          <Icon name="arrow-up" size={20} />
        </TouchableOpacity>
        <Text style={styles.score}>{score}</Text>
        <TouchableOpacity style={styles.voteBtn} onPress={() => onDownvote(discussion.id)}>
          <Icon name="arrow-down" size={20} />
        </TouchableOpacity>
      </View>

      <View style={styles.postBody}>
        <View style={styles.metaRow}>
          <Text style={styles.subreddit}>r/stocks</Text>
          <Text style={styles.dot}>•</Text>
          <Text style={styles.user}>u/{name}</Text>
          <Text style={styles.dot}>•</Text>
          <Text style={styles.time}>{created}</Text>
          {!!stockSymbol && <Text style={styles.flair}>{stockSymbol}</Text>}
        </View>

        <Text style={styles.title} numberOfLines={3}>{title}</Text>
        {!!contentPreview && <Text style={styles.preview} numberOfLines={3}>{contentPreview}</Text>}

        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.actionPill} onPress={() => onComment(discussion.id)}>
            <Icon name="message-circle" size={16} />
            <Text style={styles.pillText}>{commentCount} Comments</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionPill} onPress={() => onPress(discussion.id)}>
            <Icon name="share-2" size={16} />
            <Text style={styles.pillText}>Share</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionPill} onPress={() => onFollow(discussion?.user?.id)}>
            <Icon name="user-plus" size={16} />
            <Text style={styles.pillText}>Follow</Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
});

const styles = StyleSheet.create({
  postRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  voteCol: {
    width: 44,
    alignItems: 'center',
    marginRight: 10,
  },
  voteBtn: {
    paddingVertical: 4,
  },
  score: {
    fontWeight: '700',
    marginVertical: 2,
    color: '#1C1C1E',
  },
  postBody: {
    flex: 1,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    flexWrap: 'wrap',
    gap: 6,
  },
  subreddit: { fontWeight: '700', color: '#1C1C1E' },
  dot: { color: '#8E8E93', marginHorizontal: 4 },
  user: { color: '#8E8E93' },
  time: { color: '#8E8E93' },
  flair: {
    marginLeft: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#007AFF',
    color: '#007AFF',
    overflow: 'hidden',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
    color: '#1C1C1E',
  },
  preview: {
    color: '#3A3A3C',
    marginBottom: 10,
    lineHeight: 20,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  actionPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  pillText: { fontWeight: '600', color: '#1C1C1E' },
});

export default DiscussionItem;
