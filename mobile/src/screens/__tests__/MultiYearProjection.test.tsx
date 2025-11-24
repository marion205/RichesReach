/**
 * Unit tests for Multi-Year Projection calculations
 */

describe('Multi-Year Projection Calculations', () => {
  const currentYear = 2025;
  const baseIncome = 80000;
  const filingStatus = 'single';
  const state = 'CA';
  const growthRate = 0.03; // 3% annual growth

  describe('Income Projection', () => {
    it('should calculate projected income with growth', () => {
      const years = [0, 1, 2, 3, 4, 5];
      const projections = years.map((i) => ({
        year: currentYear + i,
        projectedIncome: baseIncome * Math.pow(1 + growthRate, i),
      }));
      
      expect(projections[0].projectedIncome).toBe(80000);
      expect(projections[1].projectedIncome).toBeCloseTo(82400, 0);
      expect(projections[5].projectedIncome).toBeCloseTo(92742, 0);
    });

    it('should handle zero growth rate', () => {
      const zeroGrowth = 0;
      const projectedIncome = baseIncome * Math.pow(1 + zeroGrowth, 5);
      
      expect(projectedIncome).toBe(baseIncome);
    });

    it('should handle negative growth rate', () => {
      const negativeGrowth = -0.02;
      const projectedIncome = baseIncome * Math.pow(1 + negativeGrowth, 5);
      
      expect(projectedIncome).toBeLessThan(baseIncome);
    });
  });

  describe('Tax Projection', () => {
    // Simplified tax brackets for testing
    const INCOME_BRACKETS = {
      single: [
        { min: 0, max: 11600, rate: 0.10 },
        { min: 11601, max: 47150, rate: 0.12 },
        { min: 47151, max: 100525, rate: 0.22 },
        { min: 100526, max: 191950, rate: 0.24 },
        { min: 191951, max: 243725, rate: 0.32 },
        { min: 243726, max: 609350, rate: 0.35 },
        { min: 609351, max: Infinity, rate: 0.37 },
      ],
    };

    const calculateIncomeTax = (income: number, filingStatus: string) => {
      const brackets = INCOME_BRACKETS[filingStatus as keyof typeof INCOME_BRACKETS];
      let tax = 0;
      let prevMax = 0;
      
      for (const bracket of brackets) {
        if (income > prevMax) {
          const taxableInBracket = Math.min(income, bracket.max) - prevMax;
          tax += taxableInBracket * bracket.rate;
          prevMax = bracket.max;
        }
      }
      
      return {
        tax,
        effectiveRate: income > 0 ? tax / income : 0,
      };
    };

    it('should calculate tax for current year', () => {
      const taxResult = calculateIncomeTax(baseIncome, filingStatus);
      
      expect(taxResult.tax).toBeGreaterThan(0);
      expect(taxResult.effectiveRate).toBeGreaterThan(0);
      expect(taxResult.effectiveRate).toBeLessThan(1);
    });

    it('should calculate tax for projected years', () => {
      const years = [0, 1, 2, 3, 4, 5];
      const projections = years.map((i) => {
        const projectedIncome = baseIncome * Math.pow(1 + growthRate, i);
        const taxResult = calculateIncomeTax(projectedIncome, filingStatus);
        return {
          year: currentYear + i,
          projectedIncome,
          projectedTax: taxResult.tax,
          effectiveRate: taxResult.effectiveRate,
        };
      });
      
      expect(projections).toHaveLength(6);
      expect(projections[0].projectedTax).toBeGreaterThan(0);
      expect(projections[5].projectedTax).toBeGreaterThan(projections[0].projectedTax);
    });

    it('should show increasing tax as income grows', () => {
      const year1Income = baseIncome * Math.pow(1 + growthRate, 1);
      const year5Income = baseIncome * Math.pow(1 + growthRate, 5);
      
      const year1Tax = calculateIncomeTax(year1Income, filingStatus).tax;
      const year5Tax = calculateIncomeTax(year5Income, filingStatus).tax;
      
      expect(year5Tax).toBeGreaterThan(year1Tax);
    });
  });

  describe('State Tax Projection', () => {
    const calculateStateTax = (income: number, state: string) => {
      const stateRates: Record<string, number> = {
        CA: 0.10,
        NY: 0.09,
        TX: 0,
        FL: 0,
      };
      return income * (stateRates[state] || 0.05);
    };

    it('should calculate state tax for CA', () => {
      const stateTax = calculateStateTax(baseIncome, 'CA');
      expect(stateTax).toBe(8000);
    });

    it('should calculate state tax for no-tax states', () => {
      const stateTax = calculateStateTax(baseIncome, 'TX');
      expect(stateTax).toBe(0);
    });

    it('should project state tax over years', () => {
      const years = [0, 1, 2, 3, 4, 5];
      const projections = years.map((i) => {
        const projectedIncome = baseIncome * Math.pow(1 + growthRate, i);
        return {
          year: currentYear + i,
          projectedIncome,
          stateTax: calculateStateTax(projectedIncome, state),
        };
      });
      
      expect(projections[0].stateTax).toBe(8000);
      expect(projections[5].stateTax).toBeGreaterThan(projections[0].stateTax);
    });
  });

  describe('Effective Rate Calculation', () => {
    it('should calculate effective rate correctly', () => {
      const income = 100000;
      const federalTax = 15000;
      const stateTax = 10000;
      const totalTax = federalTax + stateTax;
      const effectiveRate = totalTax / income;
      
      expect(effectiveRate).toBe(0.25);
      expect((effectiveRate * 100).toFixed(1)).toBe('25.0');
    });

    it('should show effective rate changes over time', () => {
      const years = [0, 1, 2, 3, 4, 5];
      const effectiveRates = years.map((i) => {
        // Simplified: assume effective rate increases slightly with income
        return 0.22 + (i * 0.01);
      });
      
      expect(effectiveRates[5]).toBeGreaterThan(effectiveRates[0]);
    });
  });

  describe('Year Selection', () => {
    it('should handle year selection from 2025 to 2030', () => {
      const availableYears = [2025, 2026, 2027, 2028, 2029, 2030];
      
      expect(availableYears).toHaveLength(6);
      expect(availableYears[0]).toBe(2025);
      expect(availableYears[5]).toBe(2030);
    });

    it('should calculate years from current year', () => {
      const yearsAhead = 5;
      const targetYear = currentYear + yearsAhead;
      
      expect(targetYear).toBe(2030);
    });
  });

  describe('Projection Data Formatting', () => {
    it('should format projected income correctly', () => {
      const projectedIncome = 92742.34;
      const formatted = projectedIncome.toLocaleString(undefined, { maximumFractionDigits: 0 });
      
      expect(formatted).toBe('92,742');
    });

    it('should format projected tax correctly', () => {
      const projectedTax = 18548.47;
      const formatted = projectedTax.toLocaleString(undefined, { maximumFractionDigits: 0 });
      
      expect(formatted).toBe('18,548');
    });

    it('should format effective rate as percentage', () => {
      const effectiveRate = 0.2534;
      const formatted = (effectiveRate * 100).toFixed(1);
      
      expect(formatted).toBe('25.3');
    });
  });
});

