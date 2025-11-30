import { useMemo } from 'react';
import { useAlpacaPositions } from '../features/stocks/hooks/useAlpacaPositions';
import { AlpacaPosition } from '../features/stocks/types';

interface OptionsPosition extends AlpacaPosition {
  underlyingSymbol?: string;
  strike?: number;
  expiration?: string;
  optionType?: 'call' | 'put';
  daysToExp?: number;
}

/**
 * Hook to filter and parse options positions from Alpaca positions
 * Options contracts have OCC format symbols like "AAPL240119C00150000"
 */
export const useOptionsPositions = (accountId: number | null) => {
  const { positions, loading, error, refetch, isOffline, isUsingCache } = useAlpacaPositions(accountId);

  // Filter and parse options positions
  const optionsPositions = useMemo<OptionsPosition[]>(() => {
    return positions
      .filter((pos: AlpacaPosition) => {
        // Options contracts have OCC format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits)
        // Example: AAPL240119C00150000
        const symbol = pos.symbol || '';
        const isOptions = /^[A-Z]+\d{6}[CP]\d{8}$/.test(symbol);
        return isOptions;
      })
      .map((pos: AlpacaPosition) => {
        const symbol = pos.symbol || '';
        const parsed = parseOptionsSymbol(symbol);
        
        return {
          ...pos,
          underlyingSymbol: parsed.underlyingSymbol,
          strike: parsed.strike,
          expiration: parsed.expiration,
          optionType: parsed.optionType,
          daysToExp: parsed.daysToExp,
        };
      });
  }, [positions]);

  return {
    positions: optionsPositions,
    loading,
    error,
    refetch,
    isOffline,
    isUsingCache,
  };
};

/**
 * Parse OCC contract symbol to extract underlying, strike, expiration, type
 * Format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits)
 * Example: AAPL240119C00150000 = AAPL, Jan 19 2024, Call, $150.00
 */
function parseOptionsSymbol(contractSymbol: string): {
  underlyingSymbol: string;
  strike: number;
  expiration: string;
  optionType: 'call' | 'put';
  daysToExp: number;
} {
  const match = contractSymbol.match(/^([A-Z]+)(\d{6})([CP])(\d{8})$/);
  
  if (!match) {
    return {
      underlyingSymbol: contractSymbol,
      strike: 0,
      expiration: '',
      optionType: 'call',
      daysToExp: 0,
    };
  }

  const underlyingSymbol = match[1];
  const dateStr = match[2];
  const optionType = match[3] === 'C' ? 'call' : 'put';
  const strike = parseInt(match[4]) / 1000;

  // Parse date: YYMMDD
  const year = 2000 + parseInt(dateStr.substring(0, 2));
  const month = parseInt(dateStr.substring(2, 4)) - 1;
  const day = parseInt(dateStr.substring(4, 6));
  const expDate = new Date(year, month, day);
  const expiration = expDate.toISOString().split('T')[0];

  // Calculate days to expiration
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  expDate.setHours(0, 0, 0, 0);
  const daysToExp = Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  return {
    underlyingSymbol,
    strike,
    expiration,
    optionType,
    daysToExp: Math.max(0, daysToExp),
  };
}

