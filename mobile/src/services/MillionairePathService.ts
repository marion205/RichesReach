/**
 * MillionairePathService
 * ======================
 * Tracks user actions and their impact on the millionaire timeline.
 * This is the core of the "Wealth Arrival" system.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface WealthAction {
  id: string;
  type: 'leak_redirect' | 'contribution_increase' | 'debt_payoff' | 'match_capture' | 'portfolio_optimization';
  description: string;
  monthlyAmount: number;
  oneTimeAmount: number;
  futureValue: number;
  daysCloser: number;
  timestamp: string;
}

export interface MillionairePath {
  // Current state
  currentPortfolioValue: number;
  monthlyContribution: number;
  goalAmount: number;
  
  // Timeline
  originalGoalDate: Date;
  currentGoalDate: Date;
  daysAccelerated: number;
  
  // Progress
  progressPercent: number;
  monthsRemaining: number;
  
  // Actions
  recentActions: WealthAction[];
  totalMonthlyRedirected: number;
  totalFutureValueAdded: number;
}

export interface TimelineProjection {
  year: number;
  age: number;
  projectedValue: number;
  contributionsTotal: number;
  growthTotal: number;
  milestone?: string;
}

const ASSUMED_ANNUAL_RETURN = 0.07;
const STORAGE_KEY = '@rr_millionaire_path';

class MillionairePathService {
  private actions: WealthAction[] = [];

  async initialize(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.actions = JSON.parse(stored);
      }
    } catch (error) {
      console.warn('Failed to load millionaire path data:', error);
    }
  }

  async recordAction(action: Omit<WealthAction, 'id' | 'timestamp' | 'futureValue' | 'daysCloser'>): Promise<WealthAction> {
    const futureValue = this.calculateFutureValue(action.monthlyAmount, 20);
    const daysCloser = this.calculateDaysCloser(action.monthlyAmount + action.oneTimeAmount, 1000000, 50000);
    
    const newAction: WealthAction = {
      ...action,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      futureValue,
      daysCloser,
    };

    this.actions.unshift(newAction);
    if (this.actions.length > 50) {
      this.actions = this.actions.slice(0, 50);
    }

    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(this.actions));
    } catch (error) {
      console.warn('Failed to save action:', error);
    }

    return newAction;
  }

  /**
   * Calculate future value of monthly contributions.
   */
  calculateFutureValue(monthlyAmount: number, years: number): number {
    const r = ASSUMED_ANNUAL_RETURN / 12;
    const n = years * 12;
    if (r === 0) return monthlyAmount * n;
    return monthlyAmount * (((1 + r) ** n - 1) / r);
  }

  /**
   * Calculate how many days closer to goal based on an action.
   */
  calculateDaysCloser(
    actionValue: number,
    goalAmount: number,
    currentValue: number,
    monthlyContribution: number = 500,
  ): number {
    if (actionValue <= 0) return 0;
    
    const remaining = goalAmount - currentValue;
    if (remaining <= 0) return 0;

    // Approximate days saved
    const r = ASSUMED_ANNUAL_RETURN / 365;
    const dailyProgress = monthlyContribution / 30;
    const baseTimeYears = Math.log((remaining * r / dailyProgress) + 1) / Math.log(1 + r) / 365;
    const newTimeYears = Math.log(((remaining - actionValue) * r / dailyProgress) + 1) / Math.log(1 + r) / 365;
    
    return Math.max(0, Math.round((baseTimeYears - newTimeYears) * 365));
  }

  /**
   * Get the current millionaire path state.
   */
  async getPath(
    currentPortfolioValue: number,
    monthlyContribution: number,
    goalAmount: number = 1000000,
    currentAge: number = 35,
  ): Promise<MillionairePath> {
    const remaining = goalAmount - currentPortfolioValue;
    
    // Calculate months to goal
    const r = ASSUMED_ANNUAL_RETURN / 12;
    let monthsRemaining = 0;
    if (remaining > 0 && monthlyContribution > 0) {
      monthsRemaining = Math.log((remaining * r / monthlyContribution) + 1) / Math.log(1 + r);
      monthsRemaining = Math.max(0, Math.ceil(monthsRemaining));
    }

    // Calculate total redirected from actions
    const totalMonthlyRedirected = this.actions.reduce((sum, a) => sum + a.monthlyAmount, 0);
    const totalFutureValueAdded = this.actions.reduce((sum, a) => sum + a.futureValue, 0);
    const daysAccelerated = this.actions.reduce((sum, a) => sum + a.daysCloser, 0);

    // Calculate dates
    const now = new Date();
    const originalDate = new Date(now);
    originalDate.setMonth(originalDate.getMonth() + monthsRemaining + Math.round(daysAccelerated / 30));
    
    const currentDate = new Date(now);
    currentDate.setMonth(currentDate.getMonth() + monthsRemaining);

    return {
      currentPortfolioValue,
      monthlyContribution: monthlyContribution + totalMonthlyRedirected,
      goalAmount,
      originalGoalDate: originalDate,
      currentGoalDate: currentDate,
      daysAccelerated,
      progressPercent: Math.min(100, (currentPortfolioValue / goalAmount) * 100),
      monthsRemaining,
      recentActions: this.actions.slice(0, 5),
      totalMonthlyRedirected,
      totalFutureValueAdded,
    };
  }

  /**
   * Generate year-by-year projection.
   */
  generateProjection(
    currentValue: number,
    monthlyContribution: number,
    currentAge: number,
    goalAmount: number = 1000000,
    years: number = 30,
  ): TimelineProjection[] {
    const projections: TimelineProjection[] = [];
    let value = currentValue;
    let totalContributions = currentValue;

    for (let i = 1; i <= years; i++) {
      const yearlyContribution = monthlyContribution * 12;
      const growth = value * ASSUMED_ANNUAL_RETURN;
      value = value + growth + yearlyContribution;
      totalContributions += yearlyContribution;

      let milestone: string | undefined;
      if (value >= 100000 && projections.every(p => !p.milestone?.includes('$100K'))) {
        milestone = '🎉 $100K Milestone!';
      } else if (value >= 500000 && projections.every(p => !p.milestone?.includes('$500K'))) {
        milestone = '🚀 $500K Milestone!';
      } else if (value >= goalAmount && projections.every(p => !p.milestone?.includes('Millionaire'))) {
        milestone = '🏆 Millionaire!';
      }

      projections.push({
        year: new Date().getFullYear() + i,
        age: currentAge + i,
        projectedValue: Math.round(value),
        contributionsTotal: Math.round(totalContributions),
        growthTotal: Math.round(value - totalContributions),
        milestone,
      });

      if (value >= goalAmount * 1.5) break;
    }

    return projections;
  }

  /**
   * Get comparison scenarios (conservative, baseline, optimistic).
   */
  getScenarios(
    currentValue: number,
    monthlyContribution: number,
    goalAmount: number = 1000000,
  ): {
    conservative: { years: number; value: number };
    baseline: { years: number; value: number };
    optimistic: { years: number; value: number };
  } {
    const calculate = (rate: number) => {
      const r = rate / 12;
      const remaining = goalAmount - currentValue;
      if (remaining <= 0) return { years: 0, value: currentValue };
      
      const months = Math.log((remaining * r / monthlyContribution) + 1) / Math.log(1 + r);
      return {
        years: Math.ceil(months / 12),
        value: this.calculateFutureValue(monthlyContribution, Math.ceil(months / 12)) + currentValue,
      };
    };

    return {
      conservative: calculate(0.04), // 4% return
      baseline: calculate(0.07),     // 7% return
      optimistic: calculate(0.10),   // 10% return
    };
  }

  /**
   * Get recent actions for display.
   */
  getRecentActions(): WealthAction[] {
    return this.actions.slice(0, 10);
  }

  /**
   * Clear all actions (for testing).
   */
  async clearActions(): Promise<void> {
    this.actions = [];
    await AsyncStorage.removeItem(STORAGE_KEY);
  }
}

export default new MillionairePathService();
