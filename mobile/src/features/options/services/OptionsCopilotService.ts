/**
 * Options Copilot Service (Hedge-Fund Edition)
 * Advanced, production-grade AI-powered options strategy engine
 */

import { httpFetch, TokenProvider } from '../../aiScans/services/http';
import type {
  OptionsCopilotRequest, OptionsCopilotResponse, OptionsStrategy, RiskAssessment
} from '../types/OptionsCopilotTypes';

class OptionsCopilotService {
  private baseUrl: string;
  private tokenProvider: TokenProvider;

  constructor(tokenProvider?: TokenProvider) {
    this.baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    this.tokenProvider = tokenProvider ?? (async () => 'your-auth-token');
  }

  private async authHeaders() {
    const tok = await this.tokenProvider();
    return {
      'Content-Type': 'application/json',
      ...(tok ? { 'Authorization': `Bearer ${tok}` } : {}),
    };
  }

  async getRecommendations(request: OptionsCopilotRequest): Promise<OptionsCopilotResponse> {
    const res = await httpFetch(`${this.baseUrl}/api/options/copilot/recommendations`, {
      method: 'POST',
      headers: await this.authHeaders(),
      timeoutMs: 15_000,
      idempotencyKey: `opts-reco-${request.symbol}-${Date.now()}`,
      body: JSON.stringify(request),
    }, 1);
    if (!res.ok) throw new Error(`Failed to get recommendations (${res.status})`);
    return res.json();
  }

  async getOptionsChain(symbol: string, expirationDate?: string): Promise<any> {
    const qs = new URLSearchParams({ symbol });
    if (expirationDate) qs.set('expiration', expirationDate);
    const res = await httpFetch(`${this.baseUrl}/api/options/chain?${qs.toString()}`, {
      method: 'GET',
      headers: await this.authHeaders(),
      timeoutMs: 10_000,
    });
    if (!res.ok) throw new Error(`Failed to get options chain (${res.status})`);
    return res.json();
  }

  async calculateStrategyPnL(strategy: OptionsStrategy, priceScenarios: number[]): Promise<any> {
    const res = await httpFetch(`${this.baseUrl}/api/options/copilot/calculate-pnl`, {
      method: 'POST',
      headers: await this.authHeaders(),
      timeoutMs: 12_000,
      idempotencyKey: `opts-pnl-${strategy.id}-${Date.now()}`,
      body: JSON.stringify({ strategy, priceScenarios }),
    });
    if (!res.ok) throw new Error(`Failed to calculate P&L (${res.status})`);
    return res.json();
  }

  async getRiskAnalysis(strategy: OptionsStrategy): Promise<RiskAssessment> {
    const res = await httpFetch(`${this.baseUrl}/api/options/copilot/risk-analysis`, {
      method: 'POST',
      headers: await this.authHeaders(),
      timeoutMs: 12_000,
      idempotencyKey: `opts-risk-${strategy.id}-${Date.now()}`,
      body: JSON.stringify({ strategy }),
    });
    if (!res.ok) throw new Error(`Failed to get risk analysis (${res.status})`);
    return res.json();
  }
}

export default new OptionsCopilotService();