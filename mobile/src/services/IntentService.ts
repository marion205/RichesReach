/**
 * Intent-Centric Trading Service
 * Routes trades through CoW Swap, 1inch Fusion, and UniswapX for best execution
 */

import { ethers } from 'ethers';
import logger from '../utils/logger';

export interface SwapIntent {
  sellToken: string;
  buyToken: string;
  sellAmount: string;
  buyAmount?: string; // Optional: minimum buy amount
  receiver: string;
  validFor: number; // Seconds until intent expires
  source: 'cowswap' | '1inch' | 'uniswapx' | 'auto';
}

export interface IntentQuote {
  source: string;
  buyAmount: string;
  estimatedGas: string;
  priceImpact: number;
  fee: string;
  validUntil: number;
}

export interface IntentOrder {
  intentId: string;
  status: 'pending' | 'filled' | 'expired' | 'cancelled';
  txHash?: string;
  filledAmount?: string;
  fillPrice?: string;
}

class IntentService {
  // CoW Swap API (Mainnet)
  private readonly COWSWAP_API = 'https://api.cow.fi/mainnet/api/v1';
  
  // 1inch Fusion API
  private readonly ONEINCH_FUSION_API = 'https://fusion.1inch.io';
  
  // UniswapX API
  private readonly UNISWAPX_API = 'https://api.uniswap.org/v2';

  /**
   * Create a swap intent
   */
  async createSwapIntent(intent: SwapIntent): Promise<IntentOrder> {
    try {
      // Auto-select best source if not specified
      if (intent.source === 'auto') {
        const quotes = await this.getQuotes(intent);
        const bestQuote = this.selectBestQuote(quotes);
        intent.source = bestQuote.source as any;
      }

      // Route to appropriate intent protocol
      switch (intent.source) {
        case 'cowswap':
          return await this.createCoWSwapIntent(intent);
        case '1inch':
          return await this.create1inchFusionIntent(intent);
        case 'uniswapx':
          return await this.createUniswapXIntent(intent);
        default:
          throw new Error('Invalid intent source');
      }
    } catch (error) {
      logger.error('Failed to create swap intent:', error);
      throw error;
    }
  }

  /**
   * Get quotes from all intent protocols
   */
  async getQuotes(intent: SwapIntent): Promise<IntentQuote[]> {
    const quotes: IntentQuote[] = [];

    try {
      // CoW Swap quote
      const cowQuote = await this.getCoWSwapQuote(intent);
      if (cowQuote) quotes.push(cowQuote);
    } catch (error) {
      logger.warn('CoW Swap quote failed:', error);
    }

    try {
      // 1inch Fusion quote
      const oneinchQuote = await this.get1inchFusionQuote(intent);
      if (oneinchQuote) quotes.push(oneinchQuote);
    } catch (error) {
      logger.warn('1inch Fusion quote failed:', error);
    }

    try {
      // UniswapX quote
      const uniswapxQuote = await this.getUniswapXQuote(intent);
      if (uniswapxQuote) quotes.push(uniswapxQuote);
    } catch (error) {
      logger.warn('UniswapX quote failed:', error);
    }

    return quotes;
  }

  /**
   * Select best quote (best price, lowest fees, MEV protection)
   */
  private selectBestQuote(quotes: IntentQuote[]): IntentQuote {
    if (quotes.length === 0) {
      throw new Error('No quotes available');
    }

    // Score quotes: prioritize best price, then MEV protection, then lower fees
    return quotes.reduce((best, current) => {
      const bestScore = this.scoreQuote(best);
      const currentScore = this.scoreQuote(current);
      return currentScore > bestScore ? current : best;
    });
  }

  /**
   * Score a quote (higher is better)
   */
  private scoreQuote(quote: IntentQuote): number {
    // Factors:
    // - Buy amount (higher is better)
    // - MEV protection (CoW Swap = +100, 1inch Fusion = +50, UniswapX = +25)
    // - Lower fees (inverse)
    // - Lower price impact (inverse)
    
    let score = parseFloat(quote.buyAmount);
    
    // MEV protection bonus
    if (quote.source === 'cowswap') score += 100;
    else if (quote.source === '1inch') score += 50;
    else if (quote.source === 'uniswapx') score += 25;
    
    // Fee penalty
    score -= parseFloat(quote.fee) * 10;
    
    // Price impact penalty
    score -= quote.priceImpact * 100;
    
    return score;
  }

  /**
   * Create CoW Swap intent (MEV-protected, no gas needed)
   */
  private async createCoWSwapIntent(intent: SwapIntent): Promise<IntentOrder> {
    try {
      const response = await fetch(`${this.COWSWAP_API}/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sellToken: intent.sellToken,
          buyToken: intent.buyToken,
          sellAmount: intent.sellAmount,
          buyAmount: intent.buyAmount,
          validFor: intent.validFor,
          partiallyFillable: false,
          from: intent.receiver,
        }),
      });

      const result = await response.json();
      
      return {
        intentId: result.uid,
        status: 'pending',
      };
    } catch (error) {
      logger.error('CoW Swap intent creation failed:', error);
      throw error;
    }
  }

  /**
   * Get CoW Swap quote
   */
  private async getCoWSwapQuote(intent: SwapIntent): Promise<IntentQuote | null> {
    try {
      const response = await fetch(
        `${this.COWSWAP_API}/quote?sellToken=${intent.sellToken}&buyToken=${intent.buyToken}&sellAmount=${intent.sellAmount}`
      );
      
      const result = await response.json();
      
      return {
        source: 'cowswap',
        buyAmount: result.buyAmount,
        estimatedGas: '0', // CoW Swap is gasless for users
        priceImpact: parseFloat(result.priceImpact || '0'),
        fee: result.feeAmount || '0',
        validUntil: Date.now() + (intent.validFor * 1000),
      };
    } catch (error) {
      logger.error('CoW Swap quote failed:', error);
      return null;
    }
  }

  /**
   * Create 1inch Fusion intent
   */
  private async create1inchFusionIntent(intent: SwapIntent): Promise<IntentOrder> {
    try {
      const response = await fetch(`${this.ONEINCH_FUSION_API}/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source: intent.sellToken,
          destination: intent.buyToken,
          amount: intent.sellAmount,
          walletAddress: intent.receiver,
          orderType: 'fill-or-kill',
        }),
      });

      const result = await response.json();
      
      return {
        intentId: result.orderHash,
        status: 'pending',
      };
    } catch (error) {
      logger.error('1inch Fusion intent creation failed:', error);
      throw error;
    }
  }

  /**
   * Get 1inch Fusion quote
   */
  private async get1inchFusionQuote(intent: SwapIntent): Promise<IntentQuote | null> {
    try {
      // 1inch Fusion uses standard 1inch API for quotes
      const response = await fetch(
        `https://api.1inch.io/v5.0/1/quote?fromTokenAddress=${intent.sellToken}&toTokenAddress=${intent.buyToken}&amount=${intent.sellAmount}`
      );
      
      const result = await response.json();
      
      return {
        source: '1inch',
        buyAmount: result.toTokenAmount,
        estimatedGas: result.estimatedGas || '0',
        priceImpact: parseFloat(result.priceImpact || '0'),
        fee: result.protocolFee || '0',
        validUntil: Date.now() + (intent.validFor * 1000),
      };
    } catch (error) {
      logger.error('1inch Fusion quote failed:', error);
      return null;
    }
  }

  /**
   * Create UniswapX intent
   */
  private async createUniswapXIntent(intent: SwapIntent): Promise<IntentOrder> {
    try {
      const response = await fetch(`${this.UNISWAPX_API}/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tokenIn: intent.sellToken,
          tokenOut: intent.buyToken,
          amount: intent.sellAmount,
          recipient: intent.receiver,
          deadline: Math.floor(Date.now() / 1000) + intent.validFor,
        }),
      });

      const result = await response.json();
      
      return {
        intentId: result.orderHash,
        status: 'pending',
      };
    } catch (error) {
      logger.error('UniswapX intent creation failed:', error);
      throw error;
    }
  }

  /**
   * Get UniswapX quote
   */
  private async getUniswapXQuote(intent: SwapIntent): Promise<IntentQuote | null> {
    try {
      const response = await fetch(`${this.UNISWAPX_API}/quote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tokenIn: intent.sellToken,
          tokenOut: intent.buyToken,
          amount: intent.sellAmount,
        }),
      });
      
      const result = await response.json();
      
      return {
        source: 'uniswapx',
        buyAmount: result.quote.amountOut,
        estimatedGas: '0', // UniswapX is gasless
        priceImpact: parseFloat(result.quote.priceImpact || '0'),
        fee: result.quote.fee || '0',
        validUntil: Date.now() + (intent.validFor * 1000),
      };
    } catch (error) {
      logger.error('UniswapX quote failed:', error);
      return null;
    }
  }

  /**
   * Check intent status
   */
  async getIntentStatus(intentId: string, source: string): Promise<IntentOrder> {
    try {
      let response;
      
      if (source === 'cowswap') {
        response = await fetch(`${this.COWSWAP_API}/orders/${intentId}`);
      } else if (source === '1inch') {
        response = await fetch(`${this.ONEINCH_FUSION_API}/orders/${intentId}`);
      } else if (source === 'uniswapx') {
        response = await fetch(`${this.UNISWAPX_API}/orders/${intentId}`);
      } else {
        throw new Error('Invalid source');
      }

      const result = await response.json();
      
      return {
        intentId,
        status: this.mapStatus(result.status),
        txHash: result.txHash,
        filledAmount: result.filledAmount,
        fillPrice: result.fillPrice,
      };
    } catch (error) {
      logger.error('Failed to get intent status:', error);
      throw error;
    }
  }

  /**
   * Map protocol status to our status enum
   */
  private mapStatus(status: string): 'pending' | 'filled' | 'expired' | 'cancelled' {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('filled') || statusLower.includes('executed')) {
      return 'filled';
    }
    if (statusLower.includes('expired')) {
      return 'expired';
    }
    if (statusLower.includes('cancelled') || statusLower.includes('rejected')) {
      return 'cancelled';
    }
    return 'pending';
  }

  /**
   * Cancel an intent
   */
  async cancelIntent(intentId: string, source: string): Promise<void> {
    try {
      let response;
      
      if (source === 'cowswap') {
        response = await fetch(`${this.COWSWAP_API}/orders/${intentId}`, {
          method: 'DELETE',
        });
      } else if (source === '1inch') {
        response = await fetch(`${this.ONEINCH_FUSION_API}/orders/${intentId}`, {
          method: 'DELETE',
        });
      } else if (source === 'uniswapx') {
        response = await fetch(`${this.UNISWAPX_API}/orders/${intentId}`, {
          method: 'DELETE',
        });
      } else {
        throw new Error('Invalid source');
      }

      if (!response.ok) {
        throw new Error('Failed to cancel intent');
      }
    } catch (error) {
      logger.error('Failed to cancel intent:', error);
      throw error;
    }
  }
}

export default new IntentService();

