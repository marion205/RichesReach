/**
 * Futures Service - Simple API client
 */

import { FuturesRecommendation, FuturesOrderRequest } from '../types/FuturesTypes';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

class FuturesService {
  async getRecommendations(): Promise<{ recommendations: FuturesRecommendation[] }> {
    const response = await fetch(`${API_BASE}/api/futures/recommendations`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch recommendations');
    }

    return response.json();
  }

  async placeOrder(order: FuturesOrderRequest): Promise<{ order_id: string; status: string }> {
    const response = await fetch(`${API_BASE}/api/futures/order`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(order),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to place order');
    }

    return response.json();
  }

  async getPositions(): Promise<{ positions: any[] }> {
    const response = await fetch(`${API_BASE}/api/futures/positions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch positions');
    }

    return response.json();
  }
}

export default new FuturesService();

