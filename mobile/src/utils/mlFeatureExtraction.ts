/**
 * Feature extraction utilities for ML model inference
 * Converts market data into feature vectors for TensorFlow Lite models
 */

import logger from './logger';

export interface MarketFeatures {
  volatility: number;
  volume: number;
  momentum: number;
  regime: number; // 0 = bearish, 1 = neutral, 2 = bullish
  spread: number;
  atr: number; // Average True Range
  rsi: number; // Relative Strength Index (0-100)
  macd: number; // MACD signal
  trend: number; // -1 = down, 0 = sideways, 1 = up
  timeOfDay: number; // Normalized hour (0-1)
}

/**
 * Extract market features from raw market data
 * This is a simplified version - in production, you'd get this from your market data API
 */
export function extractMarketFeatures(
  marketData: {
    volatility?: number;
    volume?: number;
    momentum?: number;
    regime?: 'bearish' | 'neutral' | 'bullish';
    spread?: number;
    atr?: number;
    rsi?: number;
    macd?: number;
    trend?: 'down' | 'sideways' | 'up';
    timestamp?: number;
  } = {}
): number[] {
  const {
    volatility = 0.02,
    volume = 1000000,
    momentum = 0,
    regime = 'neutral',
    spread = 0.0001,
    atr = 0.01,
    rsi = 50,
    macd = 0,
    trend = 'sideways',
    timestamp = Date.now(),
  } = marketData;

  // Normalize regime to number
  const regimeMap: Record<string, number> = {
    bearish: 0,
    neutral: 1,
    bullish: 2,
  };
  const regimeNum = regimeMap[regime] ?? 1;

  // Normalize trend to number
  const trendMap: Record<string, number> = {
    down: -1,
    sideways: 0,
    up: 1,
  };
  const trendNum = trendMap[trend] ?? 0;

  // Normalize time of day (0-1, where 0 = midnight, 1 = 11:59 PM)
  const date = new Date(timestamp);
  const hour = date.getHours();
  const minute = date.getMinutes();
  const timeOfDay = (hour * 60 + minute) / (24 * 60);

  // Normalize RSI (0-100 -> 0-1)
  const rsiNormalized = rsi / 100;

  // Normalize volume (assuming max volume of 10M, adjust based on your data)
  const volumeNormalized = Math.min(volume / 10000000, 1);

  // Normalize ATR (assuming max ATR of 0.1, adjust based on your data)
  const atrNormalized = Math.min(atr / 0.1, 1);

  // Normalize MACD (assuming range of -0.1 to 0.1, adjust based on your data)
  const macdNormalized = Math.max(-1, Math.min(1, macd / 0.1));

  // Feature vector (10 features as per the example model)
  const features = [
    volatility,           // 0: Volatility (0-1)
    volumeNormalized,     // 1: Normalized volume (0-1)
    momentum,             // 2: Momentum (-1 to 1)
    regimeNum / 2,        // 3: Regime (0-1)
    spread * 10000,       // 4: Spread in basis points (normalized)
    atrNormalized,        // 5: Normalized ATR (0-1)
    rsiNormalized,        // 6: Normalized RSI (0-1)
    macdNormalized,       // 7: Normalized MACD (-1 to 1)
    (trendNum + 1) / 2,   // 8: Trend (0-1)
    timeOfDay,            // 9: Time of day (0-1)
  ];

  logger.log('Extracted market features:', {
    features: features.map((f, i) => `F${i}: ${f.toFixed(4)}`).join(', '),
  });

  return features;
}

/**
 * Extract features from a trading context
 * Used for bandit strategy selection
 */
export function extractTradingContextFeatures(context: {
  marketRegime?: string;
  volatility?: number;
  accountSize?: number;
  openPositions?: number;
  recentWinRate?: number;
}): number[] {
  const {
    marketRegime = 'neutral',
    volatility = 0.02,
    accountSize = 25000,
    openPositions = 0,
    recentWinRate = 0.5,
  } = context;

  // Normalize account size (assuming max of 1M)
  const accountSizeNormalized = Math.min(accountSize / 1000000, 1);

  // Normalize open positions (assuming max of 10)
  const positionsNormalized = Math.min(openPositions / 10, 1);

  // Regime encoding
  const regimeMap: Record<string, number> = {
    bearish: 0,
    neutral: 0.5,
    bullish: 1,
  };
  const regimeNum = regimeMap[marketRegime.toLowerCase()] ?? 0.5;

  return [
    volatility,
    accountSizeNormalized,
    positionsNormalized,
    recentWinRate,
    regimeNum,
  ];
}

