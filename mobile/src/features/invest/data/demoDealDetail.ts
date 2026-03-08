/**
 * Demo deal detail data for Private Markets (five pillars).
 * Replace with API/backend when available.
 */

import type { Deal, DealDetail, DealScore, PortfolioFitInsight, DealContext, RiskFraming, MethodologySummary, DecisionSupport, DealConfidence, ConfidenceDetail, ScoreInputCategory } from '../types/privateMarketsTypes';

export const METHODOLOGY: MethodologySummary = {
  id: 'rr-v1',
  name: 'RichesReach Deal Score',
  summary: 'Our score is built from four weighted pillars, benchmarked against similar deals, and updated with a consistent methodology so you can compare apples to apples.',
  pillars: ['Unit economics & path to profitability', 'Team & execution', 'Market & traction', 'Risk & downside'],
  lastUpdated: 'Jan 2025',
};

function buildScore(overall: number): DealScore {
  const components = [
    { label: 'Unit economics', score: Math.min(100, overall + 4), weight: '30%', shortReason: 'Strong path to profitability.' },
    { label: 'Team', score: Math.min(100, overall + 6), weight: '25%', shortReason: 'Prior exits in sector.' },
    { label: 'Market & traction', score: Math.min(100, overall - 2), weight: '30%', shortReason: 'TAM and growth support case.' },
    { label: 'Risk & downside', score: Math.min(100, overall - 5), weight: '15%', shortReason: 'Concentration and regulatory noted.' },
  ];
  const percentile = overall >= 75 ? 78 : overall >= 65 ? 62 : 45;
  return {
    overall,
    components,
    benchmark: {
      percentileAmongPeers: percentile,
      peerCount: 124,
      segmentLabel: 'Series B Fintech',
      trend: overall >= 70 ? 'above_peer' : 'in_line',
    },
    methodologyId: METHODOLOGY.id,
  };
}

function buildRisks(): RiskFraming {
  return {
    mainRisks: [
      { label: 'Regulatory', description: 'Evolving payments regulation in key markets.' },
      { label: 'Concentration', description: 'Top 3 customers >40% of revenue.' },
      { label: 'Competition', description: 'Incumbents moving into same space.' },
    ],
    concentrationNote: 'Consider sizing to limit single-deal concentration.',
    liquidityNote: 'Typical hold 5–8 years; no secondary assumed.',
  };
}

function buildPortfolioFit(deal: Deal): PortfolioFitInsight[] {
  const isFintech = (deal.category ?? '').toLowerCase() === 'fintech';
  return [
    {
      kind: 'overlap',
      headline: isFintech ? 'Overlaps with your public tech exposure' : 'Adds sector diversification',
      body: isFintech
        ? 'Your portfolio is already heavy in public tech. This deal adds more fintech exposure—consider whether you want more concentration here.'
        : 'This adds diversification vs. your current public equity heavy allocation.',
      positive: !isFintech,
    },
    {
      kind: 'diversification',
      headline: 'Improves alternatives diversification',
      body: 'Within your private sleeve, this adds a different stage and sector. Fits a growth-oriented alternatives bucket.',
      positive: true,
    },
    {
      kind: 'liquidity',
      headline: 'Illiquidity matches your profile',
      body: 'You’ve indicated a 5+ year horizon for illiquid assets. This deal fits that profile; no need to size for early exit.',
      positive: true,
    },
  ];
}

function buildContext(deal: Deal): DealContext {
  return {
    relativeAttractiveness: 'This deal ranks above the median for Series B fintech on our score. Valuation is in line with peers; the differentiator is unit economics and team.',
    investorFit: 'Best for growth-oriented investors with 5–8 year horizon and some tolerance for illiquidity. Not ideal for those seeking income or short-term liquidity.',
    mainHiddenRisk: 'Customer concentration: a single large client could drive >25% of revenue. Diligence on contract durability and expansion pipeline is key.',
    portfolioPlacement: 'Treat as a satellite position within an alternatives sleeve (e.g. 2–5% of that sleeve). Complements, rather than replaces, core public equity.',
  };
}

function buildDecisionSupport(): DecisionSupport {
  return {
    suggestedPositionSize: '2–5% of alternatives sleeve',
    concentrationWarning: 'Keep single-deal exposure under 10% of private allocation.',
    tradeoffSummary: 'Strong score and fit; main tradeoff is illiquidity and regulatory uncertainty.',
    compareDealIds: ['2', '3'],
  };
}

function buildConfidence(deal: Deal): DealConfidence {
  return deal.id === '1' ? 'moderate' : 'limited';
}

function buildConfidenceDetail(deal: Deal): ConfidenceDetail {
  const level = buildConfidence(deal);
  const percent = level === 'high' ? 92 : level === 'moderate' ? 68 : 45;
  const factors =
    level === 'high'
      ? []
      : level === 'moderate'
        ? ['Missing legal diligence', 'Incomplete cap table', 'Market comps 6+ months old']
        : ['Limited financials', 'No legal docs', 'Incomplete team data', 'Outdated market comps'];
  return { level, percent, factors };
}

function buildWhatWouldChangeScore(deal: Deal): string[] {
  const level = buildConfidence(deal);
  if (level === 'high') return [];
  return [
    'Score would improve with updated customer concentration data.',
    'Confidence would improve if legal diligence were completed.',
    level === 'limited' ? 'Full financials and cap table would materially improve score reliability.' : 'Updated market comps would strengthen the benchmark.',
  ];
}

function buildScoreInputs(deal: Deal, scoreBreakdown: DealScore): ScoreInputCategory[] {
  const comps = scoreBreakdown.components ?? [];
  const ue = comps.find((c) => c.label === 'Unit economics');
  const team = comps.find((c) => c.label === 'Team');
  const market = comps.find((c) => c.label === 'Market & traction');
  const risk = comps.find((c) => c.label === 'Risk & downside');
  return [
    {
      id: 'unit_economics',
      label: 'Unit economics',
      items: [
        { label: 'Revenue growth', value: '120% YoY', source: 'Financials' },
        { label: 'Path to profitability', value: '18–24 mo', source: 'Model' },
        { label: 'Gross margin', value: ue ? `${ue.score}% score` : '—', source: 'Score input' },
      ],
    },
    {
      id: 'team',
      label: 'Team quality',
      items: [
        { label: 'CEO', value: 'Prior exit (fintech)', source: 'Profile' },
        { label: 'CTO', value: 'Ex-FAANG', source: 'Profile' },
        { label: 'Team score', value: team ? String(team.score) : '—', source: 'Score input' },
      ],
    },
    {
      id: 'market',
      label: 'Market structure',
      items: [
        { label: 'TAM', value: '$12B', source: 'Market' },
        { label: 'SAM (addressable)', value: '$1.2B', source: 'Market' },
        { label: 'Market traction score', value: market ? String(market.score) : '—', source: 'Score input' },
      ],
    },
    {
      id: 'terms',
      label: 'Terms',
      items: [
        { label: 'Valuation (pre)', value: deal.id === '1' ? '$42M' : deal.id === '2' ? '$8M' : '$18M', source: 'Terms' },
        { label: 'Liquidation pref', value: '1x non-participating', source: 'Terms' },
      ],
    },
    {
      id: 'signals',
      label: 'Signals',
      items: [
        { label: 'Risk & downside score', value: risk ? String(risk.score) : '—', source: 'Score input' },
        { label: 'Benchmark', value: 'Vs similar deals', source: 'Proprietary' },
      ],
    },
  ];
}

export function getDemoDealDetail(deal: Deal): DealDetail {
  const scoreBreakdown = buildScore(deal.score);
  const riskFraming = buildRisks();
  const portfolioFit = buildPortfolioFit(deal);
  const context = buildContext(deal);
  const methodology = METHODOLOGY;
  const decisionSupport = buildDecisionSupport();
  const confidence = buildConfidence(deal);
  const confidenceDetail = buildConfidenceDetail(deal);
  const whatWouldChangeScore = buildWhatWouldChangeScore(deal);
  const scoreInputs = buildScoreInputs(deal, scoreBreakdown);
  const whyScore = [
    'Strong unit economics and path to profitability.',
    'Experienced team with prior exits in sector.',
    'Addressable market and traction support growth assumptions.',
  ];

  return {
    ...deal,
    scoreBreakdown,
    whyScore,
    riskFraming,
    portfolioFit,
    context,
    methodology,
    decisionSupport,
    confidence,
    confidenceDetail,
    whatWouldChangeScore,
    scoreInputs,
  };
}
