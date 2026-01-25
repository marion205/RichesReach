/**
 * Real-time Risk Engine Service
 * Monitors DeFi positions for liquidation risk, health factors, and stop-loss
 */

import { ethers } from 'ethers';
import Web3Service from './Web3Service';
import logger from '../utils/logger';

export interface PositionRisk {
  positionId: string;
  protocol: 'AAVE' | 'Compound' | 'Lido';
  asset: string;
  healthFactor: number;
  liquidationThreshold: number;
  currentValue: number;
  collateralValue: number;
  debtValue: number;
  riskLevel: 'safe' | 'warning' | 'critical' | 'liquidated';
  estimatedLiquidationPrice?: number;
  stopLossPrice?: number;
}

export interface RiskAlert {
  type: 'liquidation_warning' | 'health_factor_low' | 'stop_loss_triggered' | 'position_closed';
  positionId: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: number;
  actionRequired: boolean;
}

class RiskEngineService {
  private monitoringInterval: NodeJS.Timeout | null = null;
  private positions: Map<string, PositionRisk> = new Map();
  private alertCallbacks: ((alert: RiskAlert) => void)[] = [];
  private healthFactorThreshold = 1.5; // Warn if below 1.5
  private criticalThreshold = 1.2; // Critical if below 1.2

  /**
   * Start monitoring positions
   */
  startMonitoring(intervalMs: number = 30000): void {
    if (this.monitoringInterval) {
      this.stopMonitoring();
    }

    this.monitoringInterval = setInterval(() => {
      this.checkAllPositions();
    }, intervalMs);

    // Initial check
    this.checkAllPositions();
  }

  /**
   * Stop monitoring
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Add position to monitor
   */
  async addPosition(
    positionId: string,
    protocol: 'AAVE' | 'Compound' | 'Lido',
    asset: string,
    stopLossPrice?: number
  ): Promise<void> {
    try {
      const risk = await this.calculatePositionRisk(positionId, protocol, asset);
      if (stopLossPrice) {
        risk.stopLossPrice = stopLossPrice;
      }
      this.positions.set(positionId, risk);
    } catch (error) {
      logger.error(`Failed to add position ${positionId}:`, error);
    }
  }

  /**
   * Remove position from monitoring
   */
  removePosition(positionId: string): void {
    this.positions.delete(positionId);
  }

  /**
   * Check all positions for risk
   */
  private async checkAllPositions(): Promise<void> {
    for (const [positionId, position] of this.positions.entries()) {
      try {
        const updatedRisk = await this.calculatePositionRisk(
          positionId,
          position.protocol,
          position.asset
        );
        
        // Update position
        updatedRisk.stopLossPrice = position.stopLossPrice;
        this.positions.set(positionId, updatedRisk);

        // Check for alerts
        this.checkPositionAlerts(positionId, updatedRisk);
      } catch (error) {
        logger.error(`Failed to check position ${positionId}:`, error);
      }
    }
  }

  /**
   * Calculate risk for a position
   */
  private async calculatePositionRisk(
    positionId: string,
    protocol: 'AAVE' | 'Compound' | 'Lido',
    asset: string
  ): Promise<PositionRisk> {
    try {
      if (protocol === 'AAVE') {
        return await this.calculateAAVERisk(positionId, asset);
      } else if (protocol === 'Compound') {
        return await this.calculateCompoundRisk(positionId, asset);
      } else {
        // Lido staking - lower risk
        return {
          positionId,
          protocol,
          asset,
          healthFactor: 999, // Staking has no liquidation risk
          liquidationThreshold: 0,
          currentValue: 0,
          collateralValue: 0,
          debtValue: 0,
          riskLevel: 'safe',
        };
      }
    } catch (error) {
      logger.error(`Failed to calculate risk for ${positionId}:`, error);
      throw error;
    }
  }

  /**
   * Calculate AAVE position risk
   */
  private async calculateAAVERisk(positionId: string, asset: string): Promise<PositionRisk> {
    try {
      const accountData = await Web3Service.getUserAccountData();
      
      const healthFactor = parseFloat(accountData.healthFactor);
      const collateralValue = parseFloat(accountData.totalCollateralETH);
      const debtValue = parseFloat(accountData.totalDebtETH);
      const liquidationThreshold = parseFloat(accountData.currentLiquidationThreshold);

      // Determine risk level
      let riskLevel: 'safe' | 'warning' | 'critical' | 'liquidated' = 'safe';
      if (healthFactor <= 1.0) {
        riskLevel = 'liquidated';
      } else if (healthFactor < this.criticalThreshold) {
        riskLevel = 'critical';
      } else if (healthFactor < this.healthFactorThreshold) {
        riskLevel = 'warning';
      }

      // Calculate estimated liquidation price (simplified)
      const estimatedLiquidationPrice = debtValue > 0 && liquidationThreshold > 0
        ? (debtValue / collateralValue) * (1 / (liquidationThreshold / 100))
        : undefined;

      return {
        positionId,
        protocol: 'AAVE',
        asset,
        healthFactor,
        liquidationThreshold,
        currentValue: collateralValue - debtValue,
        collateralValue,
        debtValue,
        riskLevel,
        estimatedLiquidationPrice,
      };
    } catch (error) {
      logger.error('Failed to calculate AAVE risk:', error);
      throw error;
    }
  }

  /**
   * Calculate Compound position risk
   */
  private async calculateCompoundRisk(positionId: string, asset: string): Promise<PositionRisk> {
    // Similar to AAVE but using Compound's comptroller
    // Simplified for now
    return {
      positionId,
      protocol: 'Compound',
      asset,
      healthFactor: 2.0,
      liquidationThreshold: 80,
      currentValue: 0,
      collateralValue: 0,
      debtValue: 0,
      riskLevel: 'safe',
    };
  }

  /**
   * Check position for alerts
   */
  private checkPositionAlerts(positionId: string, risk: PositionRisk): void {
    const alerts: RiskAlert[] = [];

    // Health factor alerts
    if (risk.healthFactor < this.criticalThreshold && risk.healthFactor > 1.0) {
      alerts.push({
        type: 'liquidation_warning',
        positionId,
        severity: 'critical',
        message: `Critical: Health factor is ${risk.healthFactor.toFixed(2)}. Position at risk of liquidation!`,
        timestamp: Date.now(),
        actionRequired: true,
      });
    } else if (risk.healthFactor < this.healthFactorThreshold) {
      alerts.push({
        type: 'health_factor_low',
        positionId,
        severity: 'high',
        message: `Warning: Health factor is ${risk.healthFactor.toFixed(2)}. Consider adding collateral.`,
        timestamp: Date.now(),
        actionRequired: true,
      });
    }

    // Stop-loss check
    if (risk.stopLossPrice && risk.currentValue <= risk.stopLossPrice) {
      alerts.push({
        type: 'stop_loss_triggered',
        positionId,
        severity: 'high',
        message: `Stop-loss triggered at $${risk.stopLossPrice}. Position should be closed.`,
        timestamp: Date.now(),
        actionRequired: true,
      });
    }

    // Liquidated check
    if (risk.riskLevel === 'liquidated') {
      alerts.push({
        type: 'position_closed',
        positionId,
        severity: 'critical',
        message: 'Position has been liquidated.',
        timestamp: Date.now(),
        actionRequired: false,
      });
    }

    // Emit alerts
    alerts.forEach(alert => {
      this.emitAlert(alert);
    });
  }

  /**
   * Register alert callback
   */
  onAlert(callback: (alert: RiskAlert) => void): void {
    this.alertCallbacks.push(callback);
  }

  /**
   * Remove alert callback
   */
  offAlert(callback: (alert: RiskAlert) => void): void {
    this.alertCallbacks = this.alertCallbacks.filter(cb => cb !== callback);
  }

  /**
   * Emit alert to all callbacks
   */
  private emitAlert(alert: RiskAlert): void {
    this.alertCallbacks.forEach(callback => {
      try {
        callback(alert);
      } catch (error) {
        logger.error('Error in alert callback:', error);
      }
    });
  }

  /**
   * Get all monitored positions
   */
  getPositions(): PositionRisk[] {
    return Array.from(this.positions.values());
  }

  /**
   * Get position by ID
   */
  getPosition(positionId: string): PositionRisk | undefined {
    return this.positions.get(positionId);
  }

  /**
   * Set stop-loss for position
   */
  setStopLoss(positionId: string, price: number): void {
    const position = this.positions.get(positionId);
    if (position) {
      position.stopLossPrice = price;
      this.positions.set(positionId, position);
    }
  }

  /**
   * Get risk summary
   */
  getRiskSummary(): {
    totalPositions: number;
    safe: number;
    warning: number;
    critical: number;
    liquidated: number;
    totalValue: number;
  } {
    const positions = Array.from(this.positions.values());
    
    return {
      totalPositions: positions.length,
      safe: positions.filter(p => p.riskLevel === 'safe').length,
      warning: positions.filter(p => p.riskLevel === 'warning').length,
      critical: positions.filter(p => p.riskLevel === 'critical').length,
      liquidated: positions.filter(p => p.riskLevel === 'liquidated').length,
      totalValue: positions.reduce((sum, p) => sum + p.currentValue, 0),
    };
  }
}

export default new RiskEngineService();

