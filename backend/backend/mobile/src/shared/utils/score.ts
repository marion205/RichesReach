export const getScoreColor = (score: number) => {
  if (score >= 90) return '#4CAF50'; // Green
  if (score >= 80) return '#8BC34A'; // Light Green
  if (score >= 70) return '#FFC107'; // Yellow
  return '#FF5722'; // Red
};

export const getBuyRecommendation = (score: number) => {
  if (score >= 90) return { text: 'STRONG BUY', color: '#4CAF50', backgroundColor: '#E8F5E8' };
  if (score >= 80) return { text: 'BUY',         color: '#8BC34A', backgroundColor: '#F1F8E9' };
  if (score >= 70) return { text: 'HOLD',        color: '#FFC107', backgroundColor: '#FFF8E1' };
  return                { text: 'AVOID',       color: '#FF5722', backgroundColor: '#FFEBEE' };
};

export const n = (x: any, f = 1) =>
  Number.isFinite(Number(x)) ? Number(x).toFixed(f) : 'N/A';

export const formatMarketCap = (marketCap?: number | string | null) => {
  if (marketCap == null) return 'N/A';
  const num = typeof marketCap === 'string' ? parseInt(marketCap, 10) : marketCap;
  if (!Number.isFinite(num)) return 'N/A';
  if (num >= 1e12) return `$${(num / 1e12).toFixed(1)}T`;
  if (num >= 1e9)  return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6)  return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
};
