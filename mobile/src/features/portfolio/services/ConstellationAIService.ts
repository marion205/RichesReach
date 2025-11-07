/**
 * Constellation AI Service
 * Integrates AI/ML capabilities into Constellation Orb features
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MoneySnapshot } from './MoneySnapshotService';

export interface PersonalizedLifeEvent {
  id: string;
  title: string;
  icon: string;
  targetAmount: number;
  currentProgress: number;
  monthsAway: number;
  suggestion: string;
  color: string;
  aiConfidence: number;
  aiReasoning: string;
  personalizedFactors: string[];
}

export interface MLGrowthProjection {
  scenario: string;
  growthRate: number; // ML-predicted rate
  confidence: number;
  timeframe: number;
  projectedValue: number;
  color: string;
  mlFactors: {
    marketRegime: string;
    volatility: number;
    momentum: number;
    riskLevel: string;
  };
}

export interface AIShieldAnalysis {
  currentRisk: number;
  marketRegime: string;
  recommendedStrategies: Array<{
    id: string;
    priority: number;
    aiReasoning: string;
    expectedImpact: string;
  }>;
  marketOutlook: {
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    keyFactors: string[];
  };
}

export interface PersonalizedRecommendation {
  type: 'life_event' | 'investment' | 'savings' | 'risk_management';
  title: string;
  description: string;
  action: string;
  priority: number;
  aiConfidence: number;
  reasoning: string;
}

class ConstellationAIService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api`;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await AsyncStorage.getItem('token') || await AsyncStorage.getItem('authToken');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Get AI-powered personalized life event suggestions
   */
  async getPersonalizedLifeEvents(
    snapshot: MoneySnapshot,
    userProfile?: {
      age?: number;
      incomeBracket?: string;
      riskTolerance?: string;
      investmentGoals?: string[];
    }
  ): Promise<PersonalizedLifeEvent[]> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/ai/life-events`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          snapshot: {
            netWorth: snapshot.netWorth,
            cashflow: snapshot.cashflow,
            breakdown: snapshot.breakdown,
          },
          userProfile,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.events || [];
    } catch (error) {
      console.warn('[ConstellationAI] Failed to fetch AI life events, using fallback:', error);
      return this.getFallbackLifeEvents(snapshot);
    }
  }

  /**
   * Get ML-enhanced growth projections
   */
  async getMLGrowthProjections(
    snapshot: MoneySnapshot,
    timeframes: number[] = [6, 12, 24, 36]
  ): Promise<MLGrowthProjection[]> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/ai/growth-projections`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          currentValue: snapshot.netWorth,
          monthlySurplus: snapshot.cashflow.delta,
          portfolioValue: snapshot.breakdown.portfolioValue,
          timeframes,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.projections || [];
    } catch (error) {
      console.warn('[ConstellationAI] Failed to fetch ML projections, using fallback:', error);
      return this.getFallbackProjections(snapshot, timeframes);
    }
  }

  /**
   * Get AI market analysis for shield strategies
   */
  async getAIShieldAnalysis(
    snapshot: MoneySnapshot
  ): Promise<AIShieldAnalysis> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/ai/shield-analysis`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          portfolioValue: snapshot.breakdown.portfolioValue,
          bankBalance: snapshot.breakdown.bankBalance,
          positions: snapshot.positions,
          cashflow: snapshot.cashflow,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.analysis;
    } catch (error) {
      console.warn('[ConstellationAI] Failed to fetch AI shield analysis, using fallback:', error);
      return this.getFallbackShieldAnalysis(snapshot);
    }
  }

  /**
   * Get personalized AI recommendations
   */
  async getPersonalizedRecommendations(
    snapshot: MoneySnapshot,
    userBehavior?: {
      recentActions?: string[];
      preferences?: Record<string, any>;
    }
  ): Promise<PersonalizedRecommendation[]> {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseUrl}/ai/recommendations`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          snapshot: {
            netWorth: snapshot.netWorth,
            cashflow: snapshot.cashflow,
            breakdown: snapshot.breakdown,
            positions: snapshot.positions,
          },
          userBehavior,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.recommendations || [];
    } catch (error) {
      console.warn('[ConstellationAI] Failed to fetch AI recommendations, using fallback:', error);
      return this.getFallbackRecommendations(snapshot);
    }
  }

  // Fallback methods for when AI/ML is unavailable
  private getFallbackLifeEvents(snapshot: MoneySnapshot): PersonalizedLifeEvent[] {
    const bankBalance = snapshot?.breakdown?.bankBalance ?? 0;
    const netWorth = snapshot?.netWorth ?? 0;
    const cashflowDelta = snapshot?.cashflow?.delta ?? 100;

    return [
      {
        id: 'emergency',
        title: 'Emergency Fund',
        icon: 'shield',
        targetAmount: netWorth * 0.1,
        currentProgress: bankBalance,
        monthsAway: Math.ceil((netWorth * 0.1 - bankBalance) / Math.max(cashflowDelta, 100)),
        suggestion: `Save $${Math.max(100, Math.floor(cashflowDelta * 0.3)).toFixed(0)}/mo to reach goal`,
        color: '#34C759',
        aiConfidence: 0.85,
        aiReasoning: 'Standard emergency fund recommendation based on financial best practices',
        personalizedFactors: ['Net worth analysis', 'Cash flow patterns'],
      },
    ];
  }

  private getFallbackProjections(
    snapshot: MoneySnapshot,
    timeframes: number[]
  ): MLGrowthProjection[] {
    const currentValue = snapshot.netWorth;
    const monthlySurplus = snapshot.cashflow.delta;

    return timeframes.map((timeframe) => ({
      scenario: 'Moderate Growth',
      growthRate: 8,
      confidence: 0.7,
      timeframe,
      projectedValue: this.calculateProjection(8, timeframe, monthlySurplus * 0.5, currentValue),
      color: '#007AFF',
      mlFactors: {
        marketRegime: 'neutral',
        volatility: 0.15,
        momentum: 0.5,
        riskLevel: 'medium',
      },
    }));
  }

  private calculateProjection(
    growthRate: number,
    months: number,
    monthlyContribution: number,
    currentValue: number
  ): number {
    const monthlyRate = growthRate / 12 / 100;
    let futureValue = currentValue;
    
    for (let i = 0; i < months; i++) {
      futureValue = futureValue * (1 + monthlyRate) + monthlyContribution;
    }
    
    return futureValue;
  }

  private getFallbackShieldAnalysis(snapshot: MoneySnapshot): AIShieldAnalysis {
    return {
      currentRisk: 0.5,
      marketRegime: 'neutral',
      recommendedStrategies: [
        {
          id: 'increase-cash',
          priority: 1,
          aiReasoning: 'Based on current portfolio allocation, increasing cash reserves would improve risk management',
          expectedImpact: 'Reduces portfolio volatility by 10-15%',
        },
      ],
      marketOutlook: {
        sentiment: 'neutral',
        confidence: 0.6,
        keyFactors: ['Current market conditions', 'Portfolio composition'],
      },
    };
  }

  private getFallbackRecommendations(snapshot: MoneySnapshot): PersonalizedRecommendation[] {
    return [
      {
        type: 'savings',
        title: 'Increase Emergency Fund',
        description: 'Consider building a larger emergency fund for better financial security',
        action: 'Set aside 10% of monthly surplus',
        priority: 1,
        aiConfidence: 0.8,
        reasoning: 'Based on your current cash flow and net worth',
      },
    ];
  }
}

// Export singleton instance
export const constellationAIService = new ConstellationAIService();
export default constellationAIService;

