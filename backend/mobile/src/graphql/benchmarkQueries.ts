import { gql } from '@apollo/client';

export interface BenchmarkDataPoint {
  timestamp: string;
  value: number;
  change: number;
  changePercent: number;
}

export interface BenchmarkSeries {
  symbol: string;
  name: string;
  timeframe: string;
  dataPoints: BenchmarkDataPoint[];
  startValue: number;
  endValue: number;
  totalReturn: number;
  totalReturnPercent: number;
  volatility: number;
}

export interface BenchmarkQueryData {
  benchmarkSeries: BenchmarkSeries | null;
}

export interface BenchmarkQueryVars {
  symbol: string;
  timeframe: string;
}

export interface AvailableBenchmarksQueryData {
  availableBenchmarks: string[];
}

// Query to get benchmark series data
export const GET_BENCHMARK_SERIES = gql`
  query GetBenchmarkSeries($symbol: String!, $timeframe: String!) {
    benchmarkSeries(symbol: $symbol, timeframe: $timeframe) {
      symbol
      name
      timeframe
      dataPoints {
        timestamp
        value
        change
        changePercent
      }
      startValue
      endValue
      totalReturn
      totalReturnPercent
      volatility
    }
  }
`;

// Query to get available benchmark symbols
export const GET_AVAILABLE_BENCHMARKS = gql`
  query GetAvailableBenchmarks {
    availableBenchmarks
  }
`;

// Hook for getting benchmark series data
export const useBenchmarkSeries = (symbol: string, timeframe: string) => {
  return {
    query: GET_BENCHMARK_SERIES,
    variables: { symbol, timeframe },
    skip: !symbol || !timeframe,
  };
};

// Hook for getting available benchmarks
export const useAvailableBenchmarks = () => {
  return {
    query: GET_AVAILABLE_BENCHMARKS,
  };
};

// Utility function to extract values from benchmark series
export const extractBenchmarkValues = (series: BenchmarkSeries | null): number[] => {
  if (!series || !series.dataPoints) {
    return [];
  }
  return series.dataPoints.map(point => point.value);
};

// Utility function to get benchmark performance summary
export const getBenchmarkSummary = (series: BenchmarkSeries | null) => {
  if (!series) {
    return {
      totalReturn: 0,
      totalReturnPercent: 0,
      volatility: 0,
      startValue: 0,
      endValue: 0,
    };
  }

  return {
    totalReturn: series.totalReturn,
    totalReturnPercent: series.totalReturnPercent,
    volatility: series.volatility,
    startValue: series.startValue,
    endValue: series.endValue,
  };
};

// Utility function to calculate alpha (portfolio return - benchmark return)
export const calculateAlpha = (portfolioReturnPercent: number, benchmarkReturnPercent: number): number => {
  return portfolioReturnPercent - benchmarkReturnPercent;
};

// Utility function to format benchmark symbol for display
export const formatBenchmarkSymbol = (symbol: string): string => {
  const symbolMap: Record<string, string> = {
    'SPY': 'S&P 500',
    'QQQ': 'NASDAQ-100',
    'IWM': 'Russell 2000',
    'VTI': 'Total Stock Market',
    'VEA': 'Developed Markets',
    'VWO': 'Emerging Markets',
    'AGG': 'Total Bond Market',
    'TLT': 'Long-term Treasury',
    'GLD': 'Gold',
    'SLV': 'Silver',
  };
  
  return symbolMap[symbol] || symbol;
};

// Utility function to get benchmark color for charts
export const getBenchmarkColor = (symbol: string, isDark: boolean = false): string => {
  const colorMap: Record<string, { light: string; dark: string }> = {
    'SPY': { light: '#64748B', dark: '#8B9DB3' },
    'QQQ': { light: '#3B82F6', dark: '#60A5FA' },
    'IWM': { light: '#8B5CF6', dark: '#A78BFA' },
    'VTI': { light: '#10B981', dark: '#34D399' },
    'VEA': { light: '#F59E0B', dark: '#FBBF24' },
    'VWO': { light: '#EF4444', dark: '#F87171' },
    'AGG': { light: '#6B7280', dark: '#9CA3AF' },
    'TLT': { light: '#8B5CF6', dark: '#A78BFA' },
    'GLD': { light: '#F59E0B', dark: '#FBBF24' },
    'SLV': { light: '#6B7280', dark: '#9CA3AF' },
  };
  
  const colors = colorMap[symbol] || { light: '#64748B', dark: '#8B9DB3' };
  return isDark ? colors.dark : colors.light;
};
