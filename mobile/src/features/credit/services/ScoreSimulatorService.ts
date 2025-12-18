/**
 * Score Simulator Service
 * Calculates projected credit scores based on user inputs
 */

import { ScoreSimulatorInputs, ScoreSimulation } from '../types/CreditTypes';

class ScoreSimulatorService {
  /**
   * Simulate credit score based on inputs
   * Uses simplified FICO-like calculation
   */
  simulateScore(
    currentScore: number,
    inputs: ScoreSimulatorInputs
  ): ScoreSimulation {
    // Base factors (simplified FICO model)
    const utilizationWeight = 0.3; // 30% of score
    const paymentHistoryWeight = 0.35; // 35% of score
    const inquiriesWeight = 0.1; // 10% of score
    const otherFactorsWeight = 0.25; // 25% (age, mix, etc.)

    // Calculate utilization impact
    const utilizationImpact = this.calculateUtilizationImpact(
      inputs.utilizationPercent,
      currentScore
    );

    // Calculate payment history impact
    const paymentHistoryImpact = this.calculatePaymentHistoryImpact(
      inputs.onTimeStreak,
      currentScore
    );

    // Calculate inquiries impact
    const inquiriesImpact = this.calculateInquiriesImpact(
      inputs.recentInquiries,
      currentScore
    );

    // Calculate projected score
    const baseScore = currentScore * otherFactorsWeight;
    const utilizationScore = (850 * utilizationWeight) * (1 - utilizationImpact / 100);
    const paymentScore = (850 * paymentHistoryWeight) * (1 - paymentHistoryImpact / 100);
    const inquiriesScore = (850 * inquiriesWeight) * (1 - inquiriesImpact / 100);

    const projectedScore = Math.round(
      baseScore + utilizationScore + paymentScore + inquiriesScore
    );

    // Clamp to valid range
    const minScore = Math.max(300, projectedScore - 30);
    const likelyScore = Math.min(850, Math.max(300, projectedScore));
    const maxScore = Math.min(850, projectedScore + 30);

    // Determine time to impact
    const timeToImpact = this.getTimeToImpact(
      utilizationImpact,
      paymentHistoryImpact,
      inquiriesImpact
    );

    return {
      minScore,
      likelyScore,
      maxScore,
      timeToImpact,
      factors: {
        utilization: {
          impact: Math.round(utilizationImpact),
          note: this.getUtilizationNote(inputs.utilizationPercent),
        },
        paymentHistory: {
          impact: Math.round(paymentHistoryImpact),
          note: this.getPaymentHistoryNote(inputs.onTimeStreak),
        },
        inquiries: {
          impact: Math.round(inquiriesImpact),
          note: this.getInquiriesNote(inputs.recentInquiries),
        },
      },
    };
  }

  private calculateUtilizationImpact(utilization: number, currentScore: number): number {
    // Optimal utilization is 1-9%
    if (utilization <= 9) {
      return -5; // Small positive impact
    } else if (utilization <= 30) {
      return 0; // Neutral
    } else if (utilization <= 50) {
      return 10; // Moderate negative
    } else if (utilization <= 75) {
      return 25; // Significant negative
    } else {
      return 40; // Major negative
    }
  }

  private calculatePaymentHistoryImpact(streak: number, currentScore: number): number {
    // Perfect payment history (24+ months) = no negative impact
    if (streak >= 24) {
      return -10; // Positive impact
    } else if (streak >= 12) {
      return 0; // Neutral
    } else if (streak >= 6) {
      return 15; // Moderate negative
    } else if (streak >= 3) {
      return 30; // Significant negative
    } else {
      return 50; // Major negative (recent late payments)
    }
  }

  private calculateInquiriesImpact(inquiries: number, currentScore: number): number {
    // 0-1 inquiries = minimal impact
    if (inquiries <= 1) {
      return 0;
    } else if (inquiries <= 3) {
      return 5; // Small negative
    } else if (inquiries <= 5) {
      return 15; // Moderate negative
    } else {
      return 25; // Significant negative
    }
  }

  private getTimeToImpact(
    utilImpact: number,
    paymentImpact: number,
    inquiriesImpact: number
  ): string {
    const maxImpact = Math.max(Math.abs(utilImpact), Math.abs(paymentImpact), Math.abs(inquiriesImpact));
    
    if (maxImpact <= 5) {
      return '1-2 cycles';
    } else if (maxImpact <= 15) {
      return '2-3 cycles';
    } else if (maxImpact <= 30) {
      return '3-6 months';
    } else {
      return '6-12 months';
    }
  }

  private getUtilizationNote(utilization: number): string {
    if (utilization <= 9) {
      return 'Excellent! Keep utilization under 10% for optimal scoring.';
    } else if (utilization <= 30) {
      return 'Good utilization. Aim for under 10% to maximize score.';
    } else if (utilization <= 50) {
      return 'Moderate utilization. Pay down to under 30% for better scoring.';
    } else {
      return 'High utilization is hurting your score. Prioritize paying down debt.';
    }
  }

  private getPaymentHistoryNote(streak: number): string {
    if (streak >= 24) {
      return 'Perfect payment history! This is your strongest factor.';
    } else if (streak >= 12) {
      return 'Good payment history. Keep it up to build a stronger track record.';
    } else if (streak >= 6) {
      return 'Building payment history. Stay consistent for 12+ months.';
    } else {
      return 'Recent payment history. Focus on never missing a payment.';
    }
  }

  private getInquiriesNote(inquiries: number): string {
    if (inquiries === 0) {
      return 'No recent inquiries. Great for your score.';
    } else if (inquiries <= 2) {
      return 'Minimal inquiries. Avoid new applications for 6 months.';
    } else if (inquiries <= 5) {
      return 'Multiple inquiries detected. Wait 12 months before applying again.';
    } else {
      return 'Too many inquiries. This significantly impacts your score.';
    }
  }
}

export const scoreSimulatorService = new ScoreSimulatorService();

