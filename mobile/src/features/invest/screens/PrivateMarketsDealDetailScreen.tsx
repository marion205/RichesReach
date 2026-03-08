/**
 * Private Markets — Deal Detail (V1)
 * Five pillars: proprietary scoring, portfolio-fit intelligence, decision infra, trust layer, better-than-market context.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Linking,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Feather from '@expo/vector-icons/Feather';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { COLORS } from '../theme/privateMarketsTheme';
import CircularScore from '../components/CircularScore';
import { getDemoDealDetail } from '../data/demoDealDetail';
import { getPrivateMarketsService } from '../services/privateMarketsService';
import type { Deal, DealDetail, DealDataProvenance, InstitutionalDiligence, DiligenceItemStatus } from '../types/privateMarketsTypes';

type DealDetailParams = { dealId?: string; deal?: Deal };

const DILIGENCE_CHECKLIST_KEY = (dealId: string) => `privateMarkets_diligenceChecklist_${dealId}`;

const DILIGENCE_STATUS_ORDER: DiligenceItemStatus[] = ['not_started', 'requested', 'received', 'reviewed'];
const DILIGENCE_STATUS_LABELS: Record<DiligenceItemStatus, string> = {
  not_started: 'Not started',
  requested: 'Requested',
  received: 'Received',
  reviewed: 'Reviewed',
};

const getProgressColor = (score: number) => {
  if (score >= 80) return '#10B981';
  if (score >= 60) return '#3B82F6';
  return '#F59E0B';
};

function SectionCard({ children, style, ...props }: { children: React.ReactNode; style?: any }) {
  return (
    <View style={[styles.sectionCard, style]} {...props}>
      {children}
    </View>
  );
}

export default function PrivateMarketsDealDetailScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<RouteProp<{ params: DealDetailParams }, 'params'>>();
  const params = route.params ?? {};
  const deal: Deal = params.deal ?? { id: '1', name: 'Series B — Fintech', tagline: 'B2B payments infrastructure', score: 72, category: 'fintech' };
  const detail: DealDetail = getDemoDealDetail(deal);

  const [provenance, setProvenance] = useState<DealDataProvenance | null>(null);
  const [diligence, setDiligence] = useState<InstitutionalDiligence | null>(null);
  const [diligenceStatus, setDiligenceStatus] = useState<Record<string, DiligenceItemStatus>>({});

  useEffect(() => {
    getPrivateMarketsService().getDataProvenance(detail.id).then(setProvenance);
    getPrivateMarketsService().getDiligence(detail.id).then(setDiligence);
  }, [detail.id]);

  useEffect(() => {
    if (!detail.whatWouldChangeScore?.length) return;
    const key = DILIGENCE_CHECKLIST_KEY(detail.id);
    AsyncStorage.getItem(key)
      .then((raw) => {
        if (!raw) return;
        try {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            const record: Record<string, DiligenceItemStatus> = {};
            parsed.forEach((line: string) => { record[line] = 'reviewed'; });
            setDiligenceStatus(record);
          } else if (parsed && typeof parsed === 'object') {
            setDiligenceStatus(parsed as Record<string, DiligenceItemStatus>);
          }
        } catch (_) {}
      })
      .catch(() => {});
  }, [detail.id, detail.whatWouldChangeScore?.length]);

  const setDiligenceItemStatus = useCallback((line: string, status: DiligenceItemStatus) => {
    setDiligenceStatus((prev) => {
      const next = { ...prev, [line]: status };
      AsyncStorage.setItem(DILIGENCE_CHECKLIST_KEY(detail.id), JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, [detail.id]);

  const handleRequestFromGP = useCallback((line: string) => {
    setDiligenceItemStatus(line, 'requested');
    Alert.alert(
      'Request from GP',
      'In a full implementation, this would send a request to the issuer/GP. Mark as Received when you have the document.',
      [{ text: 'OK' }]
    );
  }, [setDiligenceItemStatus]);

  const handlePartnerCta = () => {
    Linking.openURL('https://richesreach.com/private-markets-partner').catch(() => {});
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Pressable style={({ pressed }) => [styles.backRow, pressed && styles.backRowPressed]} onPress={() => navigation.goBack()}>
        <Feather name="chevron-left" size={24} color={COLORS.primary} />
        <Text style={styles.backLabel}>Back to deals</Text>
      </Pressable>

      <View style={styles.header}>
        <Text style={styles.dealName}>{detail.name}</Text>
        <Text style={styles.dealTagline}>{detail.tagline}</Text>
      </View>

      {/* 1. Score hero + components */}
      {detail.scoreBreakdown && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI Deal Score</Text>
          <View style={styles.scoreHero}>
            <CircularScore
              score={detail.scoreBreakdown.overall}
              size={180}
              strokeWidth={16}
              progressColor={getProgressColor(detail.scoreBreakdown.overall)}
              trackColor="#E2E8F0"
              textColor={COLORS.primary}
            />
          </View>
          {(detail.confidence || detail.confidenceDetail) && (
            <View style={[styles.confidenceStrip, styles[`confidence_${detail.confidenceDetail?.level ?? detail.confidence}` as keyof typeof styles]]}>
              <Feather
                name={(detail.confidenceDetail?.level ?? detail.confidence) === 'high' ? 'shield' : (detail.confidenceDetail?.level ?? detail.confidence) === 'moderate' ? 'info' : 'alert-circle'}
                size={18}
                color={(detail.confidenceDetail?.level ?? detail.confidence) === 'high' ? '#059669' : (detail.confidenceDetail?.level ?? detail.confidence) === 'moderate' ? '#B45309' : '#DC2626'}
              />
              <View style={styles.confidenceTextBlock}>
                <Text style={styles.confidenceLabel}>
                  {(detail.confidenceDetail?.level ?? detail.confidence) === 'high'
                    ? 'High confidence'
                    : (detail.confidenceDetail?.level ?? detail.confidence) === 'moderate'
                      ? `Moderate confidence${detail.confidenceDetail?.percent != null ? ` (${detail.confidenceDetail.percent}%)` : ''}`
                      : `Limited data${detail.confidenceDetail?.percent != null ? ` (${detail.confidenceDetail.percent}%)` : ''}`}
                </Text>
                {detail.confidenceDetail?.factors && detail.confidenceDetail.factors.length > 0 ? (
                  <>
                    <Text style={styles.confidenceFactorsLabel}>Affected by:</Text>
                    <Text style={styles.confidenceSub}>{detail.confidenceDetail.factors.join(', ')}</Text>
                  </>
                ) : (
                  <Text style={styles.confidenceSub}>
                    {(detail.confidenceDetail?.level ?? detail.confidence) === 'high'
                      ? 'Score and fit based on full diligence.'
                      : (detail.confidenceDetail?.level ?? detail.confidence) === 'moderate'
                        ? 'Based on partial diligence; consider additional verification.'
                        : 'Diligence limited; score and recommendation have lower confidence.'}
                  </Text>
                )}
              </View>
            </View>
          )}
          {detail.scoreBreakdown.benchmark && (
            <View style={styles.benchmarkBadge}>
              <Feather name="bar-chart-2" size={16} color="#64748B" />
              <Text style={styles.benchmarkText}>
                {detail.scoreBreakdown.benchmark.trend === 'above_peer' ? 'Above' : 'Below or in line with'} peers
                {detail.scoreBreakdown.benchmark.percentileAmongPeers != null &&
                  ` • Top ${100 - detail.scoreBreakdown.benchmark.percentileAmongPeers}%`}
              </Text>
            </View>
          )}
          {detail.scoreInputs && detail.scoreInputs.length > 0 && (
            <SectionCard style={styles.scoreInputsCard}>
              <Text style={styles.subsectionTitle}>What feeds this score</Text>
              {detail.scoreInputs.map((cat) => (
                <View key={cat.id} style={styles.scoreInputCategory}>
                  <Text style={styles.scoreInputCatLabel}>{cat.label}</Text>
                  {cat.items.map((item, i) => (
                    <View key={i} style={styles.scoreInputItem}>
                      <Text style={styles.scoreInputItemLabel}>{item.label}</Text>
                      <Text style={styles.scoreInputItemValue}>{item.value}</Text>
                      {item.source && <Text style={styles.scoreInputSource}>{item.source}</Text>}
                    </View>
                  ))}
                </View>
              ))}
            </SectionCard>
          )}
          {detail.whatWouldChangeScore && detail.whatWouldChangeScore.length > 0 && (
            <SectionCard style={styles.whatWouldChangeCard}>
              <Text style={styles.subsectionTitle}>What would change this score?</Text>
              <Text style={styles.whatWouldChangeSubtitle}>Track your diligence workflow</Text>
              {detail.whatWouldChangeScore.map((line, i) => {
                const status = diligenceStatus[line] ?? 'not_started';
                const canRequest = status === 'not_started' || status === 'requested';
                return (
                  <View key={i} style={styles.whatWouldChangeItemBlock}>
                    <Text style={[styles.whatWouldChangeText, status === 'reviewed' && styles.whatWouldChangeTextReviewed]}>{line}</Text>
                    <View style={styles.whatWouldChangeStatusRow}>
                      {DILIGENCE_STATUS_ORDER.map((s) => (
                        <Pressable
                          key={s}
                          style={({ pressed }) => [
                            styles.diligencePill,
                            status === s && styles.diligencePillActive,
                            pressed && styles.diligencePillPressed,
                          ]}
                          onPress={() => setDiligenceItemStatus(line, s)}
                        >
                          <Text style={[styles.diligencePillText, status === s && styles.diligencePillTextActive]} numberOfLines={1}>
                            {DILIGENCE_STATUS_LABELS[s]}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                    {canRequest && (
                      <Pressable
                        style={({ pressed }) => [styles.requestFromGPButton, pressed && styles.requestFromGPPressed]}
                        onPress={() => handleRequestFromGP(line)}
                      >
                        <Feather name="send" size={14} color={COLORS.primary} />
                        <Text style={styles.requestFromGPText}>Request from issuer/GP</Text>
                      </Pressable>
                    )}
                  </View>
                );
              })}
            </SectionCard>
          )}
          <SectionCard>
            <Text style={styles.subsectionTitle}>Score components</Text>
            <View style={styles.componentsList}>
              {detail.scoreBreakdown.components.map((c, i) => (
                <View key={i} style={styles.componentRow}>
                  <View style={styles.componentMain}>
                    <Text style={styles.componentLabel}>{c.label}</Text>
                    <Text style={styles.componentWeight}>Weight: {c.weight}</Text>
                  </View>
                  <View style={styles.componentRight}>
                    <Text style={[styles.componentScore, { color: getProgressColor(c.score) }]}>{c.score}</Text>
                  </View>
                  <Text style={styles.componentReason}>{c.shortReason}</Text>
                </View>
              ))}
            </View>
          </SectionCard>
        </View>
      )}

      {/* 2. Why this score */}
      {detail.whyScore && detail.whyScore.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Why this score</Text>
          <SectionCard>
            <View style={styles.bulletList}>
              {detail.whyScore.map((line, i) => (
                <View key={i} style={styles.bulletRow}>
                  <Feather name="check-circle" size={18} color="#10B981" style={styles.bulletIcon} />
                  <Text style={styles.bulletText}>{line}</Text>
                </View>
              ))}
            </View>
          </SectionCard>
        </View>
      )}

      {/* 3. Key risks & mitigants */}
      {detail.riskFraming && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key risks & mitigants</Text>
          <SectionCard style={styles.riskCard}>
            {detail.riskFraming.mainRisks.map((r, i) => (
              <View key={i} style={styles.riskRow}>
                <Feather name="alert-triangle" size={18} color="#F59E0B" style={styles.riskIcon} />
                <View style={styles.riskBlock}>
                  <Text style={styles.riskLabel}>{r.label}</Text>
                  <Text style={styles.riskText}>{r.description}</Text>
                </View>
              </View>
            ))}
            {(detail.riskFraming.concentrationNote || detail.riskFraming.liquidityNote) && (
              <View style={styles.riskNotes}>
                {detail.riskFraming.concentrationNote && <Text style={styles.riskNote}>• {detail.riskFraming.concentrationNote}</Text>}
                {detail.riskFraming.liquidityNote && <Text style={styles.riskNote}>• {detail.riskFraming.liquidityNote}</Text>}
              </View>
            )}
          </SectionCard>
        </View>
      )}

      {/* 4. Portfolio-fit intelligence */}
      {detail.portfolioFit && detail.portfolioFit.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Portfolio fit analysis</Text>
          {detail.portfolioFit.map((fit, i) => (
            <SectionCard key={i} style={fit.positive ? styles.fitPositiveCard : styles.fitConcernCard}>
              <Feather
                name={fit.positive ? 'check-circle' : 'alert-circle'}
                size={20}
                color={fit.positive ? '#10B981' : '#F59E0B'}
                style={styles.fitIcon}
              />
              <View style={styles.fitContent}>
                <Text style={styles.fitHeadline}>{fit.headline}</Text>
                <Text style={styles.fitBody}>{fit.body}</Text>
              </View>
            </SectionCard>
          ))}
        </View>
      )}

      {/* 5. Better-than-market context */}
      {detail.context && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Market & strategic context</Text>
          <SectionCard>
            <View style={styles.contextPair}>
              <Text style={styles.contextQ}>Attractive vs similar deals?</Text>
              <Text style={styles.contextA}>{detail.context.relativeAttractiveness}</Text>
            </View>
            <View style={styles.contextPair}>
              <Text style={styles.contextQ}>Best investor profile?</Text>
              <Text style={styles.contextA}>{detail.context.investorFit}</Text>
            </View>
            <View style={styles.contextPair}>
              <Text style={styles.contextQ}>Main hidden risk</Text>
              <Text style={styles.contextA}>{detail.context.mainHiddenRisk}</Text>
            </View>
            <View style={styles.contextPair}>
              <Text style={styles.contextQ}>How to sit in a portfolio</Text>
              <Text style={styles.contextA}>{detail.context.portfolioPlacement}</Text>
            </View>
          </SectionCard>
        </View>
      )}

      {/* 6. Trust: methodology */}
      {detail.methodology && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How we score</Text>
          <SectionCard style={styles.methodologyCard}>
            <Text style={styles.methodologyName}>{detail.methodology.name}</Text>
            <Text style={styles.methodologySummary}>{detail.methodology.summary}</Text>
            <View style={styles.pillarsRow}>
              {detail.methodology.pillars.map((p, i) => (
                <View key={i} style={styles.pillarChip}>
                  <Text style={styles.pillarText}>{p}</Text>
                </View>
              ))}
            </View>
            {detail.methodology.lastUpdated && (
              <Text style={styles.methodologyUpdated}>Methodology updated {detail.methodology.lastUpdated}</Text>
            )}
          </SectionCard>
        </View>
      )}

      {/* Data provenance — source, refresh, coverage, missing data */}
      {provenance && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data sources</Text>
          <SectionCard style={styles.provenanceCard}>
            {provenance.attributions.map((a, i) => (
              <View key={i} style={styles.provenanceRow}>
                <Feather name="database" size={18} color={COLORS.accent} style={styles.provIcon} />
                <View style={styles.provBlock}>
                  <Text style={styles.provSource}>{a.sourceName}</Text>
                  <Text style={styles.provMeta}>Refreshed {new Date(a.lastRefreshedAt).toLocaleDateString()}</Text>
                  {a.coverage && <Text style={styles.provCoverage}>Coverage: {a.coverage}</Text>}
                </View>
              </View>
            ))}
            <Text style={styles.provFullRefresh}>Last full refresh: {new Date(provenance.lastFullRefresh).toLocaleDateString()}</Text>
            {provenance.gaps && provenance.gaps.length > 0 && (
              <View style={styles.gapsBlock}>
                <Text style={styles.gapsTitle}>Missing or limited data</Text>
                {provenance.gaps.map((g, i) => (
                  <Text key={i} style={styles.gapItem}>• {g.replace(/_/g, ' ')}</Text>
                ))}
              </View>
            )}
          </SectionCard>
        </View>
      )}

      {/* Diligence — financials, terms, market, team, legal, governance + completeness */}
      {diligence && diligence.sections.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Diligence</Text>
          {diligence.overallCompleteness && (
            <View style={styles.diligenceOverall}>
              <Text style={styles.diligenceOverallLabel}>Overall</Text>
              <View style={[styles.completenessBadge, styles[`completeness_${diligence.overallCompleteness}` as keyof typeof styles]]}>
                <Text style={styles.completenessText}>{diligence.overallCompleteness}</Text>
              </View>
            </View>
          )}
          {diligence.sections.map((sec) => (
            <SectionCard key={sec.id} style={styles.diligenceSectionCard}>
              <View style={styles.diligenceSectionHeader}>
                <Text style={styles.diligenceSectionLabel}>{sec.label}</Text>
                {sec.completeness && (
                  <View style={[styles.completenessBadge, styles[`completeness_${sec.completeness}` as keyof typeof styles]]}>
                    <Text style={styles.completenessText}>{sec.completeness}</Text>
                  </View>
                )}
              </View>
              {sec.summary && <Text style={styles.diligenceSummary}>{sec.summary}</Text>}
              {sec.items.map((item, i) => (
                <View key={i} style={styles.diligenceItem}>
                  <Text style={styles.diligenceItemLabel}>{item.label}</Text>
                  <Text style={styles.diligenceItemValue}>{item.value}</Text>
                  {item.detail && <Text style={styles.diligenceItemDetail}>{item.detail}</Text>}
                </View>
              ))}
              {sec.documentRefs && sec.documentRefs.length > 0 && (
                <View style={styles.docRefs}>
                  {sec.documentRefs.map((ref, i) => (
                    <Text key={i} style={styles.docRef}>📎 {ref.label}</Text>
                  ))}
                </View>
              )}
            </SectionCard>
          ))}
        </View>
      )}

      {/* 7. Decision support */}
      {detail.decisionSupport && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Decision guidance</Text>
          <SectionCard style={styles.decisionCard}>
            {detail.confidence && detail.confidence !== 'high' && (
              <View style={styles.diligenceImpact}>
                <Feather name="info" size={16} color="#B45309" />
                <Text style={styles.diligenceImpactText}>
                  Diligence is {detail.confidence === 'moderate' ? 'partial' : 'limited'}; recommendation confidence is {detail.confidence}.
                </Text>
              </View>
            )}
            {detail.decisionSupport.suggestedPositionSize && (
              <View style={styles.decisionHighlight}>
                <Text style={styles.decisionLabelBig}>Recommended allocation</Text>
                <Text style={styles.decisionValueBig}>{detail.decisionSupport.suggestedPositionSize}</Text>
              </View>
            )}
            {detail.decisionSupport.concentrationWarning && (
              <View style={styles.concentrationCard}>
                <View style={styles.concentrationHeader}>
                  <Feather name="alert-circle" size={16} color="#F59E0B" />
                  <Text style={styles.decisionLabel}>Concentration</Text>
                </View>
                <Text style={styles.concentrationText}>{detail.decisionSupport.concentrationWarning}</Text>
              </View>
            )}
            {detail.decisionSupport.tradeoffSummary && (
              <Text style={styles.tradeoffText}>{detail.decisionSupport.tradeoffSummary}</Text>
            )}
          </SectionCard>
        </View>
      )}

      {/* 8. Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Actions</Text>
        <View style={styles.actionsRow}>
          <Pressable style={({ pressed }) => [styles.actionBtn, pressed && styles.actionBtnPressed]}>
            <Feather name="book-open" size={18} color={COLORS.accent} />
            <Text style={styles.actionBtnText}>Learn</Text>
          </Pressable>
          <Pressable
            style={({ pressed }) => [styles.actionBtn, pressed && styles.actionBtnPressed]}
            onPress={() => navigation.navigate('PrivateMarketsCompare', { dealIds: [detail.id, ...(detail.decisionSupport?.compareDealIds ?? [])].slice(0, 4) })}
          >
            <Feather name="layers" size={18} color={COLORS.accent} />
            <Text style={styles.actionBtnText}>Compare</Text>
          </Pressable>
          <Pressable style={({ pressed }) => [styles.actionBtn, pressed && styles.actionBtnPressed]}>
            <Feather name="bookmark" size={18} color={COLORS.accent} />
            <Text style={styles.actionBtnText}>Save</Text>
          </Pressable>
        </View>
      </View>

      {/* 9. Partner CTA */}
      <View style={styles.section}>
        <Pressable style={({ pressed }) => [styles.partnerCta, pressed && styles.partnerCtaPressed]} onPress={handlePartnerCta}>
          <Text style={styles.partnerCtaText}>Invest via partner</Text>
          <Feather name="external-link" size={18} color="#FFF" />
        </Pressable>
        <Text style={styles.partnerDisclaimer}>Execution happens with a licensed partner. RichesReach does not execute trades.</Text>
      </View>

      <View style={styles.bottomPad} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 48 },
  backRow: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 4, marginBottom: 16, paddingVertical: 4, paddingRight: 8 },
  backRowPressed: { opacity: 0.7 },
  backLabel: { fontSize: 16, fontWeight: '600', color: COLORS.primary },
  header: { marginBottom: 28 },
  dealName: { fontSize: 26, fontWeight: 'bold', color: COLORS.primary, letterSpacing: -0.4 },
  dealTagline: { fontSize: 15, color: COLORS.textSecondary, marginTop: 8, lineHeight: 22 },
  section: { marginBottom: 36 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: '#64748B', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 },
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  scoreHero: { alignItems: 'center', marginVertical: 20 },
  confidenceStrip: { flexDirection: 'row', alignItems: 'flex-start', padding: 14, borderRadius: 12, marginBottom: 16, borderWidth: 1 },
  confidence_high: { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' },
  confidence_moderate: { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' },
  confidence_limited: { backgroundColor: '#FEF2F2', borderColor: '#FECACA' },
  confidenceTextBlock: { flex: 1, marginLeft: 12 },
  confidenceLabel: { fontSize: 15, fontWeight: '700', color: COLORS.primary },
  confidenceSub: { fontSize: 13, color: COLORS.textSecondary, marginTop: 4, lineHeight: 18 },
  confidenceFactorsLabel: { fontSize: 12, fontWeight: '600', color: COLORS.textSecondary, marginTop: 4 },
  scoreInputsCard: { marginBottom: 16 },
  whatWouldChangeCard: { marginBottom: 16 },
  whatWouldChangeSubtitle: { fontSize: 12, color: '#64748B', marginBottom: 10 },
  whatWouldChangeItemBlock: { marginBottom: 16, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E2E8F0' },
  whatWouldChangeText: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 18, marginBottom: 8 },
  whatWouldChangeTextReviewed: { color: '#94A3B8', textDecorationLine: 'line-through' },
  whatWouldChangeStatusRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  diligencePill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: '#E2E8F0', backgroundColor: '#F8FAFC' },
  diligencePillActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  diligencePillPressed: { opacity: 0.8 },
  diligencePillText: { fontSize: 11, fontWeight: '600', color: '#64748B' },
  diligencePillTextActive: { color: '#FFF' },
  requestFromGPButton: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 6, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8, backgroundColor: 'rgba(59, 130, 246, 0.1)' },
  requestFromGPPressed: { opacity: 0.8 },
  requestFromGPText: { fontSize: 12, fontWeight: '600', color: COLORS.primary },
  scoreInputCategory: { marginBottom: 14 },
  scoreInputCatLabel: { fontSize: 14, fontWeight: '700', color: COLORS.primary, marginBottom: 6 },
  scoreInputItem: { marginBottom: 4 },
  scoreInputItemLabel: { fontSize: 13, color: '#64748B' },
  scoreInputItemValue: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  scoreInputSource: { fontSize: 11, color: '#94A3B8', marginTop: 1 },
  diligenceImpact: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12, padding: 10, backgroundColor: 'rgba(245, 158, 11, 0.12)', borderRadius: 10 },
  diligenceImpactText: { flex: 1, fontSize: 13, color: '#92400E', lineHeight: 18 },
  benchmarkBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    alignSelf: 'center',
    marginBottom: 20,
  },
  benchmarkText: { fontSize: 14, color: '#475569', fontWeight: '500' },
  subsectionTitle: { fontSize: 15, fontWeight: '700', color: COLORS.primary, marginBottom: 12 },
  componentsList: { gap: 0 },
  componentRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  componentMain: { marginBottom: 4, flex: 1, minWidth: 100 },
  componentRight: { alignSelf: 'flex-start', marginBottom: 4 },
  componentScore: { fontSize: 20, fontWeight: '800' },
  componentWeight: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  componentLabel: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  componentReason: { width: '100%', fontSize: 13, color: COLORS.textSecondary, lineHeight: 20, marginTop: 4 },
  bulletList: { gap: 4 },
  bulletRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 14 },
  bulletIcon: { marginRight: 12, marginTop: 3 },
  bulletText: { flex: 1, fontSize: 15, color: '#1E293B', lineHeight: 24 },
  riskCard: { backgroundColor: '#FFF7ED', borderColor: 'rgba(252, 211, 77, 0.4)' },
  riskRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 14 },
  riskIcon: { marginRight: 12, marginTop: 3 },
  riskBlock: { flex: 1 },
  riskLabel: { fontSize: 14, fontWeight: '600', color: '#92400E', marginBottom: 2 },
  riskText: { fontSize: 14, color: '#92400E', lineHeight: 22 },
  riskNotes: { marginTop: 8 },
  riskNote: { fontSize: 13, color: '#B45309', lineHeight: 20, marginBottom: 4 },
  fitPositiveCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
    marginBottom: 10,
  },
  fitConcernCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFFBEB',
    borderColor: '#FCD34D',
    marginBottom: 10,
  },
  fitIcon: { marginRight: 10, marginTop: 2 },
  fitContent: { flex: 1 },
  fitHeadline: { fontSize: 14, fontWeight: '600', color: '#1E293B', marginBottom: 4 },
  fitBody: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 20 },
  contextPair: { marginTop: 14 },
  contextQ: { fontSize: 12, fontWeight: '700', color: '#64748B', marginBottom: 4, textTransform: 'uppercase' },
  contextA: { fontSize: 14, color: '#1E293B', lineHeight: 22 },
  methodologyCard: {},
  methodologyName: { fontSize: 16, fontWeight: '700', color: COLORS.primary, marginBottom: 8 },
  methodologySummary: { fontSize: 14, color: COLORS.textSecondary, lineHeight: 22, marginBottom: 12 },
  pillarsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  pillarChip: { backgroundColor: '#F1F5F9', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  pillarText: { fontSize: 12, fontWeight: '600', color: '#475569' },
  methodologyUpdated: { fontSize: 12, color: '#94A3B8' },
  provenanceCard: { backgroundColor: '#F8FAFC', borderColor: '#E2E8F0' },
  provenanceRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12 },
  provIcon: { marginRight: 10, marginTop: 2 },
  provBlock: { flex: 1 },
  provSource: { fontSize: 15, fontWeight: '600', color: COLORS.primary },
  provMeta: { fontSize: 13, color: '#64748B', marginTop: 2 },
  provCoverage: { fontSize: 13, color: '#64748B', marginTop: 2 },
  provFullRefresh: { fontSize: 13, color: '#64748B', marginTop: 8 },
  gapsBlock: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#E2E8F0' },
  gapsTitle: { fontSize: 13, fontWeight: '600', color: '#B45309', marginBottom: 6 },
  gapItem: { fontSize: 13, color: '#92400E', lineHeight: 20 },
  diligenceOverall: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  diligenceOverallLabel: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  completenessBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  completeness_full: { backgroundColor: '#D1FAE5' },
  completeness_partial: { backgroundColor: '#FEF3C7' },
  completeness_limited: { backgroundColor: '#FEE2E2' },
  completeness_missing: { backgroundColor: '#F3F4F6' },
  completenessText: { fontSize: 12, fontWeight: '600', color: '#1E293B', textTransform: 'capitalize' },
  diligenceSectionCard: { marginBottom: 10 },
  diligenceSectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  diligenceSectionLabel: { fontSize: 15, fontWeight: '700', color: COLORS.primary },
  diligenceSummary: { fontSize: 13, color: COLORS.textSecondary, marginBottom: 10 },
  diligenceItem: { marginBottom: 8 },
  diligenceItemLabel: { fontSize: 12, fontWeight: '600', color: '#64748B' },
  diligenceItemValue: { fontSize: 14, color: COLORS.primary, marginTop: 2 },
  diligenceItemDetail: { fontSize: 12, color: '#64748B', marginTop: 2 },
  docRefs: { marginTop: 8 },
  docRef: { fontSize: 13, color: COLORS.accent },
  decisionCard: { backgroundColor: '#F0F9FF', borderColor: '#BAE6FD' },
  decisionHighlight: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(59,130,246,0.08)',
    borderRadius: 12,
    marginBottom: 12,
  },
  decisionLabelBig: { fontSize: 15, fontWeight: '600', color: '#1E293B' },
  decisionValueBig: { fontSize: 28, fontWeight: '800', color: COLORS.accent, marginTop: 4 },
  concentrationCard: { padding: 12, borderRadius: 12, backgroundColor: 'rgba(245, 158, 11, 0.12)', marginBottom: 12 },
  concentrationHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  concentrationText: { fontSize: 14, color: '#0369A1', lineHeight: 20 },
  decisionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  decisionRowIcon: { marginTop: 2 },
  decisionLabel: { fontSize: 14, fontWeight: '600', color: '#0C4A6E' },
  decisionValueWrap: { flex: 1, minWidth: 0 },
  decisionValue: { fontSize: 14, color: '#0369A1', lineHeight: 20 },
  tradeoffText: { fontSize: 13, color: '#64748B', lineHeight: 20, marginTop: 6 },
  actionsRow: { flexDirection: 'row', gap: 12 },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, borderRadius: 16, backgroundColor: 'rgba(59,130,246,0.08)', borderWidth: 1, borderColor: 'rgba(59,130,246,0.3)' },
  actionBtnPressed: { opacity: 0.75, transform: [{ scale: 0.97 }] },
  actionBtnText: { fontSize: 15, fontWeight: '600', color: COLORS.accent },
  partnerCta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: COLORS.primary, paddingVertical: 18, borderRadius: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.2, shadowRadius: 16, elevation: 8 },
  partnerCtaPressed: { opacity: 0.92, transform: [{ scale: 0.98 }] },
  partnerCtaText: { fontSize: 17, fontWeight: '700', color: '#FFF' },
  partnerDisclaimer: { fontSize: 12, color: '#94A3B8', marginTop: 12, textAlign: 'center', lineHeight: 18 },
  bottomPad: { height: 60 },
});
