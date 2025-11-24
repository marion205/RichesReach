/**
 * Tax Optimization Service
 * Handles API calls to tax optimization endpoints
 */
import { API_BASE_URL } from '../config/api';

export interface TaxOptimizationRequest {
  target_cash?: number;
  lots?: Array<{
    lot_id: string;
    symbol: string;
    shares: number;
    cost_basis: number;
    price: number;
    acquire_date: string;
  }>;
  long_term_days?: number;
  fed_st_rate?: number;
  fed_lt_rate?: number;
  forbid_wash_sale?: boolean;
  recent_buys_30d?: Record<string, number>;
}

export interface TaxOptimizationResponse {
  sells: Array<{
    lot_id: string;
    symbol: string;
    shares: number;
    cost_basis: number;
    price: number;
    tax_cost: number;
    reason: string;
  }>;
  cash_raised: number;
  est_tax_cost: number;
  objective: number;
}

export interface TaxLossHarvestingResponse {
  recommendations: Array<{
    symbol: string;
    current_loss: number;
    potential_savings: number;
    action: 'sell' | 'hold';
    reason: string;
  }>;
  total_potential_savings: number;
}

export interface CapitalGainsOptimizationResponse {
  strategy: {
    short_term_gains: number;
    long_term_gains: number;
    tax_savings: number;
    recommendations: string[];
  };
}

export interface TaxEfficientRebalancingResponse {
  rebalancing_plan: Array<{
    symbol: string;
    current_weight: number;
    target_weight: number;
    action: 'buy' | 'sell' | 'hold';
    tax_impact: number;
  }>;
  total_tax_impact: number;
}

export interface TaxBracketAnalysisResponse {
  current_bracket: string;
  marginal_rate: number;
  effective_rate: number;
  recommendations: string[];
  projected_tax_savings: number;
}

class TaxOptimizationService {
  private getAuthHeaders(token: string) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Get tax optimization summary
   */
  async getOptimizationSummary(token: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/optimization-summary`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching tax optimization summary:', error);
      throw error;
    }
  }

  /**
   * Smart Lot Optimizer - Optimize which lots to sell
   */
  async optimizeLots(request: TaxOptimizationRequest, token: string): Promise<TaxOptimizationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/smart-lot-optimizer-v2`, {
        method: 'POST',
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error optimizing lots:', error);
      throw error;
    }
  }

  /**
   * Tax Loss Harvesting recommendations
   */
  async getTaxLossHarvesting(token: string): Promise<TaxLossHarvestingResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/loss-harvesting`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching tax loss harvesting:', error);
      throw error;
    }
  }

  /**
   * Capital Gains Optimization
   */
  async getCapitalGainsOptimization(token: string): Promise<CapitalGainsOptimizationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/capital-gains-optimization`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching capital gains optimization:', error);
      throw error;
    }
  }

  /**
   * Tax Efficient Rebalancing
   */
  async getTaxEfficientRebalancing(token: string): Promise<TaxEfficientRebalancingResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/tax-efficient-rebalancing`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching tax efficient rebalancing:', error);
      throw error;
    }
  }

  /**
   * Tax Bracket Analysis
   */
  async getTaxBracketAnalysis(token: string): Promise<TaxBracketAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/tax-bracket-analysis`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching tax bracket analysis:', error);
      throw error;
    }
  }

  /**
   * Two Year Gains Planner
   */
  async getTwoYearGainsPlanner(token: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/two-year-gains-planner`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching two year gains planner:', error);
      throw error;
    }
  }

  /**
   * Wash Sale Guard
   */
  async getWashSaleGuard(token: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/wash-sale-guard-v2`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching wash sale guard:', error);
      throw error;
    }
  }

  /**
   * Borrow vs Sell Advisor
   */
  async getBorrowVsSellAdvisor(token: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tax/borrow-vs-sell-advisor`, {
        method: 'GET',
        headers: this.getAuthHeaders(token),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching borrow vs sell advisor:', error);
      throw error;
    }
  }
}

export default new TaxOptimizationService();
