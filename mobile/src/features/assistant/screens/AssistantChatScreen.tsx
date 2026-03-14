import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { assistantQuery } from '../../../services/aiClient';
import UserProfileService, { ExtendedUserProfile } from '../../user/services/UserProfileService';
import realTimePortfolioService, { PortfolioMetrics } from '../../portfolio/services/RealTimePortfolioService';
import { DEMO_INVESTOR_PROFILE, DEMO_IDENTITY_GAPS } from '../../../services/demoMockData';
import type { ScreenName } from '../../../navigation/types';

interface InvestorBehavioralProfile {
  archetype: string;
  archetypeTitle: string;
  archetypeEmoji: string;
  coachingTone: string;
  maturityStage: string;
  dimensions: {
    riskTolerance: number;
    lossAversion: number;
  };
  activeBiases: Array<{
    biasType: string;
    score: number;
  }>;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  actionCard?: ActionCard;
}

interface ActionCard {
  label: string;
  screen: ScreenName;
  params?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a compact text context block from profile + portfolio + behavioral profile. */
function buildContext(
  profile: ExtendedUserProfile | null,
  portfolio: PortfolioMetrics | null,
  behavioral: InvestorBehavioralProfile | null,
): Record<string, unknown> | undefined {
  if (!profile && !portfolio && !behavioral) return undefined;
  const ctx: Record<string, unknown> = {};
  if (profile) {
    ctx.experience = profile.experienceLevel;
    ctx.risk_tolerance = profile.riskTolerance;
    ctx.time_horizon = profile.timeHorizon;
    ctx.investment_goals = profile.investmentGoals;
    ctx.monthly_investment = profile.monthlyInvestment;
  }
  if (portfolio) {
    ctx.portfolio_value = portfolio.totalValue;
    ctx.total_return_pct = portfolio.totalReturnPercent;
    ctx.day_change_pct = portfolio.dayChangePercent;
    const topHoldings = portfolio.holdings
      .slice(0, 5)
      .map(h => ({ symbol: h.symbol, pct: portfolio.totalValue > 0 ? +(h.totalValue / portfolio.totalValue * 100).toFixed(1) : 0 }));
    ctx.top_holdings = topHoldings;
    const maxWeight = topHoldings.reduce((m, h) => Math.max(m, h.pct), 0);
    ctx.max_holding_weight_pct = maxWeight;
  }
  if (behavioral) {
    ctx.investor_archetype = behavioral.archetypeTitle;
    ctx.coaching_tone = behavioral.coachingTone;
    ctx.maturity_stage = behavioral.maturityStage;
    ctx.behavioral_risk_tolerance = behavioral.dimensions.riskTolerance;
    ctx.loss_aversion = behavioral.dimensions.lossAversion;
    ctx.active_biases = behavioral.activeBiases.map(b => b.biasType);
  }
  return ctx;
}

/** Get coaching persona prompt based on tone. */
function getCoachingPersonaPrompt(tone: string): string {
  const personas: Record<string, string> = {
    'the_guardian': `Speak with empathy about market volatility. Emphasize how saving money creates a safety net. Use phrases like "Protecting your downside" and "Guaranteed wins". Focus on security and risk mitigation.`,
    'the_architect': `Speak with logic and precision. Focus on compounding and automation. Use phrases like "Optimizing the system" and "Time-in-market vs. Timing-the-market". The math is what matters.`,
    'the_scout': `Speak with energy and forward-looking vision. Focus on "Alpha" and strategic positioning. Use phrases like "Capturing growth" and "Strategic allocation". Be direct and action-oriented.`,
    'the_stabilizer': `Speak with calm reassurance. Focus on consistency and the long-term plan. Acknowledge emotions while guiding back to fundamentals. Reduce anxiety through clarity.`,
  };
  return personas[tone] || personas['the_architect'];
}

/** Detect which action card (if any) is relevant for an assistant response. */
function detectAction(text: string): ActionCard | undefined {
  const lower = text.toLowerCase();
  if (/(million|retire|retirement|on track|financial goal|save.*million|path to)/.test(lower)) {
    return { label: 'Set a retirement goal', screen: 'portfolio' };
  }
  if (/(concentration|overweight|single stock|too much in|diversif)/.test(lower)) {
    return { label: 'Review my portfolio', screen: 'portfolio' };
  }
  if (/(budget|spend|track.*spend|monthly)/.test(lower)) {
    return { label: 'Open Budgeting', screen: 'budgeting' };
  }
  if (/(invest|add money|contribute|buy|stock)/.test(lower)) {
    return { label: 'Go to Invest', screen: 'ai-portfolio' };
  }
  return undefined;
}

/** Suggestion chips shown above the input bar. */
function buildSuggestions(
  profile: ExtendedUserProfile | null,
  portfolio: PortfolioMetrics | null,
): string[] {
  const suggestions: string[] = [];

  if (portfolio && portfolio.totalValue > 0) {
    suggestions.push('Am I on track to retire?');

    if (portfolio.holdings.length > 0 && portfolio.totalValue > 0) {
      const maxWeight = portfolio.holdings.reduce(
        (m, h) => Math.max(m, h.totalValue / portfolio.totalValue),
        0,
      );
      if (maxWeight > 0.25) {
        const top = portfolio.holdings.sort((a, b) => b.totalValue - a.totalValue)[0];
        suggestions.push(`Is my ${top.symbol} position too large?`);
      }
    }
    suggestions.push('How do I reach $1M with my portfolio?');
  } else {
    suggestions.push('How much should I save each month?');
    suggestions.push('Am I saving enough for retirement?');
  }

  if (profile?.investmentGoals?.includes('retirement')) {
    if (!suggestions.some(s => s.includes('retire'))) {
      suggestions.push('When can I retire?');
    }
  }

  suggestions.push('Help me build a budget');
  return suggestions.slice(0, 4);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AssistantChatScreen() {
  const [userId] = useState('demo-user');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const [profile, setProfile] = useState<ExtendedUserProfile | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioMetrics | null>(null);
  const [behavioral, setBehavioral] = useState<InvestorBehavioralProfile | null>(null);
  const [loadingContext, setLoadingContext] = useState(true);

  const flatListRef = useRef<FlatList>(null);

  // Load profile + portfolio + behavioral profile on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [p, port] = await Promise.all([
          UserProfileService.getInstance().getProfile(),
          realTimePortfolioService.getPortfolioData().catch(() => null),
        ]);
        if (!cancelled) {
          setProfile(p);
          setPortfolio(port ?? null);
          // Load behavioral profile from demo data
          setBehavioral({
            archetype: DEMO_INVESTOR_PROFILE.archetype,
            archetypeTitle: DEMO_INVESTOR_PROFILE.archetypeTitle,
            archetypeEmoji: DEMO_INVESTOR_PROFILE.archetypeEmoji,
            coachingTone: DEMO_INVESTOR_PROFILE.coachingTone,
            maturityStage: DEMO_INVESTOR_PROFILE.maturityStage,
            dimensions: {
              riskTolerance: DEMO_INVESTOR_PROFILE.dimensions.riskTolerance,
              lossAversion: DEMO_INVESTOR_PROFILE.dimensions.lossAversion,
            },
            activeBiases: DEMO_INVESTOR_PROFILE.biasMatrix.activeBiases.map(b => ({
              biasType: b.biasType,
              score: b.score,
            })),
          });
        }
      } catch {
        // context is best-effort; silently ignore
      } finally {
        if (!cancelled) setLoadingContext(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const suggestions = buildSuggestions(profile, portfolio);

  const onSend = async (text?: string) => {
    const prompt = (text ?? input).trim();
    if (!prompt || sending) return;
    const id = String(Date.now());
    setMessages(prev => [...prev, { id, role: 'user', text: prompt }]);
    setInput('');
    setSending(true);
    try {
      const ctx = buildContext(profile, portfolio, behavioral);
      // Add coaching persona instruction to context
      if (behavioral?.coachingTone) {
        (ctx as any).coaching_persona = getCoachingPersonaPrompt(behavioral.coachingTone);
      }
      const res = await assistantQuery({ user_id: userId, prompt, context: ctx });
      const answer =
        typeof res?.answer === 'string'
          ? res.answer
          : typeof res?.response === 'string'
          ? res.response
          : JSON.stringify(res);
      const actionCard = detectAction(answer);
      setMessages(prev => [
        ...prev,
        { id: id + '-a', role: 'assistant', text: answer, actionCard },
      ]);
    } catch (e: any) {
      setMessages(prev => [
        ...prev,
        { id: id + '-e', role: 'assistant', text: e.message || 'Request failed' },
      ]);
    } finally {
      setSending(false);
    }
  };

  const navigateTo = (screen: ScreenName, params?: Record<string, unknown>) => {
    const w = window as any;
    if (typeof w.__navigateToGlobal === 'function') {
      w.__navigateToGlobal(screen, params);
    }
  };

  const renderItem = ({ item }: { item: Message }) => (
    <View>
      <View
        style={[
          styles.bubble,
          item.role === 'user' ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <Text style={[styles.text, item.role === 'user' && styles.userText]}>
          {item.text}
        </Text>
      </View>
      {item.role === 'assistant' && item.actionCard && (
        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigateTo(item.actionCard!.screen, item.actionCard!.params)}
          activeOpacity={0.8}
        >
          <Text style={styles.actionCardText}>{item.actionCard.label} →</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const coachingToneLabel = behavioral?.coachingTone
    ? behavioral.coachingTone.replace('the_', '').replace('_', ' ')
    : null;

  const contextBanner =
    !loadingContext && (profile || portfolio || behavioral) ? (
      <View style={styles.contextBanner}>
        <Text style={styles.contextBannerText}>
          {portfolio && portfolio.totalValue > 0
            ? `Using your portfolio ($${portfolio.totalValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}) + profile`
            : 'Using your profile'}
        </Text>
        {coachingToneLabel && (
          <View style={styles.personaBadge}>
            <Text style={styles.personaBadgeText}>
              {behavioral?.archetypeEmoji} {coachingToneLabel.toUpperCase()} MODE
            </Text>
          </View>
        )}
      </View>
    ) : null;

  return (
    <View style={styles.container}>
      {contextBanner}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>Ask me anything about your money</Text>
            <Text style={styles.emptySubtitle}>
              {portfolio && portfolio.totalValue > 0
                ? 'I can see your real portfolio and profile — answers are tailored to you.'
                : 'Add your profile to get answers tailored to your situation.'}
            </Text>
          </View>
        }
      />

      {/* Suggestion chips */}
      {messages.length === 0 && !loadingContext && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.chipsRow}
          contentContainerStyle={styles.chipsContent}
        >
          {suggestions.map(s => (
            <TouchableOpacity
              key={s}
              style={styles.chip}
              onPress={() => onSend(s)}
              activeOpacity={0.75}
            >
              <Text style={styles.chipText}>{s}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask anything…"
          placeholderTextColor="#8b8b94"
          multiline
          onSubmitEditing={() => onSend()}
          blurOnSubmit={false}
        />
        <TouchableOpacity
          onPress={() => onSend()}
          style={[styles.sendBtn, (!input.trim() || sending) && styles.sendBtnDisabled]}
          disabled={!input.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.sendText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },

  contextBanner: {
    backgroundColor: '#eff6ff',
    borderBottomWidth: 1,
    borderBottomColor: '#bfdbfe',
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  contextBannerText: {
    fontSize: 11,
    color: '#3b82f6',
    fontWeight: '500',
  },
  personaBadge: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  personaBadgeText: {
    fontSize: 9,
    color: '#FFFFFF',
    fontWeight: '700',
    letterSpacing: 0.5,
  },

  listContent: { padding: 16, paddingBottom: 8 },

  bubble: {
    marginVertical: 4,
    padding: 12,
    borderRadius: 14,
    maxWidth: '85%',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#3b82f6',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#ffffff',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  text: { color: '#1f2937', fontSize: 15, lineHeight: 22 },
  userText: { color: '#ffffff' },

  // Action card shown below assistant bubble
  actionCard: {
    alignSelf: 'flex-start',
    marginTop: 4,
    marginBottom: 8,
    marginLeft: 2,
    backgroundColor: '#0f172a',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
  },
  actionCardText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },

  // Empty state
  emptyState: {
    paddingTop: 40,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },

  // Suggestion chips
  chipsRow: {
    maxHeight: 46,
    marginBottom: 4,
  },
  chipsContent: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    gap: 8,
  },
  chip: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  chipText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },

  // Input row
  inputRow: {
    flexDirection: 'row',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    backgroundColor: '#ffffff',
  },
  input: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    color: '#1f2937',
    padding: 10,
    borderRadius: 12,
    marginRight: 8,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#d1d5db',
    fontSize: 15,
  },
  sendBtn: {
    backgroundColor: '#22c55e',
    paddingHorizontal: 16,
    justifyContent: 'center',
    borderRadius: 12,
    minWidth: 72,
    alignItems: 'center',
  },
  sendBtnDisabled: { opacity: 0.45 },
  sendText: { color: '#ffffff', fontWeight: '700', fontSize: 15 },
});
