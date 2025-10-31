/**
 * Options Copilot Service (Hedge-Fund Edition)
 * Advanced, production-grade AI-powered options strategy engine
 */

import { API_BASE } from '../../../config/api';
import type {
  OptionsCopilotRequest, OptionsCopilotResponse, OptionsStrategy, RiskAssessment
} from '../types/OptionsCopilotTypes';

class OptionsCopilotService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE;
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
    };
  }

  async getRecommendations(request: OptionsCopilotRequest): Promise<OptionsCopilotResponse> {
    const res = await fetch(`${this.baseUrl}/api/options/copilot/recommendations`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(error.detail || `Failed to get recommendations (${res.status})`);
    }
    return res.json();
  }

  async getOptionsChain(symbol: string, expirationDate?: string): Promise<any> {
    const qs = new URLSearchParams({ symbol });
    if (expirationDate) qs.set('expiration', expirationDate);
    const res = await fetch(`${this.baseUrl}/api/options/copilot/chain?${qs.toString()}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(error.detail || `Failed to get options chain (${res.status})`);
    }
    return res.json();
  }

  async calculateStrategyPnL(strategy: OptionsStrategy, priceScenarios: number[]): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/options/copilot/calculate-pnl`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ strategy, priceScenarios }),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(error.detail || `Failed to calculate P&L (${res.status})`);
    }
    return res.json();
  }

  async getRiskAnalysis(strategy: OptionsStrategy): Promise<RiskAssessment> {
    const res = await fetch(`${this.baseUrl}/api/options/copilot/risk-analysis`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ strategy }),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(error.detail || `Failed to get risk analysis (${res.status})`);
    }
    return res.json();
  }
}

export default new OptionsCopilotService();