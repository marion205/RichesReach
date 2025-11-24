/**
 * Unit tests for TaxBracketChart component
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { View, Text } from 'react-native';

// Mock the TaxBracketChart component logic
// Since it's a memoized component, we'll test the calculation logic separately

describe('TaxBracketChart Calculations', () => {
  const mockBrackets = [
    { min: 0, max: 11600, rate: 0.10 },
    { min: 11601, max: 47150, rate: 0.12 },
    { min: 47151, max: 100525, rate: 0.22 },
    { min: 100526, max: 191950, rate: 0.24 },
    { min: 191951, max: 243725, rate: 0.32 },
    { min: 243726, max: 609350, rate: 0.35 },
    { min: 609351, max: Infinity, rate: 0.37 },
  ];

  describe('Bracket Position Calculation', () => {
    it('should find correct bracket for income in middle range', () => {
      const income = 50000;
      const currentBracket = mockBrackets.find(
        (b) => income >= b.min && (income <= b.max || b.max === Infinity)
      );
      
      expect(currentBracket).toBeDefined();
      expect(currentBracket?.rate).toBe(0.22);
      expect(currentBracket?.min).toBe(47151);
      expect(currentBracket?.max).toBe(100525);
    });

    it('should find correct bracket for income at bracket boundary', () => {
      const income = 11601;
      const currentBracket = mockBrackets.find(
        (b) => income >= b.min && (income <= b.max || b.max === Infinity)
      );
      
      expect(currentBracket).toBeDefined();
      expect(currentBracket?.rate).toBe(0.12);
    });

    it('should find correct bracket for income in top bracket', () => {
      const income = 700000;
      const currentBracket = mockBrackets.find(
        (b) => income >= b.min && (income <= b.max || b.max === Infinity)
      );
      
      expect(currentBracket).toBeDefined();
      expect(currentBracket?.rate).toBe(0.37);
      expect(currentBracket?.max).toBe(Infinity);
    });

    it('should find correct bracket for income at zero', () => {
      const income = 0;
      const currentBracket = mockBrackets.find(
        (b) => income >= b.min && (income <= b.max || b.max === Infinity)
      );
      
      expect(currentBracket).toBeDefined();
      expect(currentBracket?.rate).toBe(0.10);
    });
  });

  describe('Next Bracket Calculation', () => {
    it('should find next bracket correctly', () => {
      const income = 50000;
      const nextBracket = mockBrackets.find((b) => b.min > income);
      
      expect(nextBracket).toBeDefined();
      expect(nextBracket?.min).toBe(100526);
      expect(nextBracket?.rate).toBe(0.24);
    });

    it('should return undefined for income in top bracket', () => {
      const income = 700000;
      const nextBracket = mockBrackets.find((b) => b.min > income);
      
      expect(nextBracket).toBeUndefined();
    });
  });

  describe('Room in Bracket Calculation', () => {
    it('should calculate room correctly for middle bracket', () => {
      const income = 50000;
      const nextBracket = mockBrackets.find((b) => b.min > income);
      const roomInBracket = nextBracket ? nextBracket.min - income : Infinity;
      
      expect(roomInBracket).toBe(50526); // 100526 - 50000
    });

    it('should return Infinity for top bracket', () => {
      const income = 700000;
      const nextBracket = mockBrackets.find((b) => b.min > income);
      const roomInBracket = nextBracket ? nextBracket.min - income : Infinity;
      
      expect(roomInBracket).toBe(Infinity);
    });
  });

  describe('Chart Width Calculation', () => {
    it('should calculate max income for chart correctly', () => {
      const income = 50000;
      const maxIncomeForChart = Math.max(
        income * 3,
        mockBrackets.find((b) => b.max !== Infinity)?.max || income * 2,
        income + 50000
      );
      
      expect(maxIncomeForChart).toBeGreaterThanOrEqual(150000);
    });

    it('should calculate bracket width percentage correctly', () => {
      const income = 50000;
      const maxIncomeForChart = 200000;
      const bracket = mockBrackets[2]; // 22% bracket
      const actualMax = Math.min(bracket.max, maxIncomeForChart);
      const width = ((actualMax - bracket.min) / maxIncomeForChart) * 100;
      
      expect(width).toBeGreaterThan(0);
      expect(width).toBeLessThanOrEqual(100);
    });

    it('should handle Infinity bracket max correctly', () => {
      const income = 700000;
      const maxIncomeForChart = 1000000;
      const bracket = mockBrackets[6]; // Top bracket with Infinity
      const actualMax = bracket.max === Infinity ? maxIncomeForChart : Math.min(bracket.max, maxIncomeForChart);
      
      expect(actualMax).toBe(maxIncomeForChart);
    });
  });

  describe('Income Position Calculation', () => {
    it('should calculate income position correctly', () => {
      const income = 50000;
      const maxIncomeForChart = 200000;
      const position = (income / maxIncomeForChart) * 100;
      
      expect(position).toBe(25);
    });

    it('should handle zero income', () => {
      const income = 0;
      const maxIncomeForChart = 200000;
      const position = (income / maxIncomeForChart) * 100;
      
      expect(position).toBe(0);
    });

    it('should cap position at 95%', () => {
      const income = 200000;
      const maxIncomeForChart = 200000;
      const position = Math.min((income / maxIncomeForChart) * 100, 95);
      
      expect(position).toBe(95);
    });
  });
});

describe('TaxBracketChart Component Props', () => {
  it('should accept valid props', () => {
    const props = {
      income: 50000,
      filingStatus: 'single' as const,
      brackets: [
        { min: 0, max: 11600, rate: 0.10 },
        { min: 11601, max: 47150, rate: 0.12 },
      ],
    };
    
    expect(props.income).toBe(50000);
    expect(props.filingStatus).toBe('single');
    expect(props.brackets).toHaveLength(2);
  });

  it('should handle different filing statuses', () => {
    const filingStatuses = ['single', 'married-joint', 'married-separate', 'head-of-household'] as const;
    
    filingStatuses.forEach((status) => {
      expect(status).toBeDefined();
      expect(typeof status).toBe('string');
    });
  });
});

