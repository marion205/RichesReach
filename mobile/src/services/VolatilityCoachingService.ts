/**
 * VolatilityCoachingService
 * =========================
 * Reframes market volatility in positive, actionable terms.
 * Based on the "Positive Volatility" notifications from the blueprint.
 * 
 * Instead of: "Your portfolio is up 1%"
 * We say: "Market growth today just paid for your groceries this week"
 */

import { DEMO_INVESTOR_PROFILE } from './demoMockData';

export type CoachingTone = 'the_guardian' | 'the_architect' | 'the_scout' | 'the_stabilizer';

export interface VolatilityNotification {
  id: string;
  type: 'positive' | 'negative' | 'neutral';
  headline: string;
  body: string;
  impact: {
    dollarAmount: number;
    percentChange: number;
    daysCloser?: number;
    realWorldEquivalent?: string;
  };
  tone: CoachingTone;
  timestamp: string;
  ctaText?: string;
  ctaScreen?: string;
}

// Real-world equivalents for dollar amounts
const REAL_WORLD_EQUIVALENTS = [
  { amount: 50, text: "a nice dinner out" },
  { amount: 100, text: "a week of groceries" },
  { amount: 200, text: "a month of utilities" },
  { amount: 500, text: "a weekend getaway" },
  { amount: 1000, text: "a month's rent payment" },
  { amount: 2000, text: "a new laptop" },
  { amount: 5000, text: "a dream vacation" },
  { amount: 10000, text: "a year of car payments" },
];

class VolatilityCoachingService {
  private assumedAnnualReturn = 0.07;

  /**
   * Generate a positive volatility notification for market gains.
   */
  generateGainNotification(
    dollarGain: number,
    percentGain: number,
    portfolioValue: number,
    tone: CoachingTone = 'the_architect',
  ): VolatilityNotification {
    const daysCloser = this.calculateDaysCloser(dollarGain, portfolioValue);
    const realWorldEquivalent = this.getRealWorldEquivalent(dollarGain);
    
    const { headline, body } = this.getPositiveMessage(
      dollarGain,
      percentGain,
      daysCloser,
      realWorldEquivalent,
      tone,
    );

    return {
      id: Date.now().toString(),
      type: 'positive',
      headline,
      body,
      impact: {
        dollarAmount: dollarGain,
        percentChange: percentGain,
        daysCloser,
        realWorldEquivalent,
      },
      tone,
      timestamp: new Date().toISOString(),
      ctaText: 'See Your Timeline',
      ctaScreen: 'MillionairePath',
    };
  }

  /**
   * Generate a calming notification for market dips.
   */
  generateDipNotification(
    dollarLoss: number,
    percentLoss: number,
    portfolioValue: number,
    tone: CoachingTone = 'the_architect',
  ): VolatilityNotification {
    const { headline, body } = this.getNegativeMessage(
      Math.abs(dollarLoss),
      Math.abs(percentLoss),
      tone,
    );

    return {
      id: Date.now().toString(),
      type: 'negative',
      headline,
      body,
      impact: {
        dollarAmount: dollarLoss,
        percentChange: percentLoss,
      },
      tone,
      timestamp: new Date().toISOString(),
      ctaText: 'Stay the Course',
      ctaScreen: 'WealthArrival',
    };
  }

  /**
   * Calculate how many days closer to the goal based on a gain.
   */
  private calculateDaysCloser(gain: number, portfolioValue: number): number {
    if (gain <= 0) return 0;
    
    // Approximate: each $1 of gain is about 0.01-0.05 days depending on portfolio size
    const goalAmount = 1000000;
    const remaining = goalAmount - portfolioValue;
    if (remaining <= 0) return 0;
    
    // Simple approximation
    const daysPerDollar = 365 * 15 / remaining; // Assuming 15 years to goal
    return Math.max(1, Math.round(gain * daysPerDollar * 0.5));
  }

  /**
   * Get a real-world equivalent for a dollar amount.
   */
  private getRealWorldEquivalent(amount: number): string {
    const sorted = [...REAL_WORLD_EQUIVALENTS].sort(
      (a, b) => Math.abs(amount - a.amount) - Math.abs(amount - b.amount)
    );
    return sorted[0].text;
  }

  /**
   * Generate positive messaging based on coaching tone.
   */
  private getPositiveMessage(
    dollarGain: number,
    percentGain: number,
    daysCloser: number,
    realWorldEquivalent: string,
    tone: CoachingTone,
  ): { headline: string; body: string } {
    switch (tone) {
      case 'the_guardian':
        return {
          headline: "Your Fortress Grew Stronger",
          body: `The market added $${dollarGain.toLocaleString()} to your defenses today. That's ${realWorldEquivalent} — paid for by simply holding your ground. Your walls are ${daysCloser} days thicker.`,
        };
      
      case 'the_architect':
        return {
          headline: "The System Delivered",
          body: `+$${dollarGain.toLocaleString()} today (+${percentGain.toFixed(2)}%). The compounding machine worked while you did other things. You're now ${daysCloser} days ahead of schedule.`,
        };
      
      case 'the_scout':
        return {
          headline: "Gains Captured",
          body: `$${dollarGain.toLocaleString()} added to your war chest today. The market paid for ${realWorldEquivalent}. ${daysCloser} days closer to the summit.`,
        };
      
      case 'the_stabilizer':
      default:
        return {
          headline: "A Good Day",
          body: `Your portfolio grew $${dollarGain.toLocaleString()} today — that's ${realWorldEquivalent}, earned while you focused on life. You're ${daysCloser} days closer to your goal.`,
        };
    }
  }

  /**
   * Generate calming messaging for dips based on coaching tone.
   */
  private getNegativeMessage(
    dollarLoss: number,
    percentLoss: number,
    tone: CoachingTone,
  ): { headline: string; body: string } {
    switch (tone) {
      case 'the_guardian':
        return {
          headline: "Your Foundation Holds",
          body: `Markets dipped ${percentLoss.toFixed(1)}% today, but your fortress stands. Your emergency fund protects you. This is temporary noise — your walls are built for storms like this.`,
        };
      
      case 'the_architect':
        return {
          headline: "Volatility Within Parameters",
          body: `A ${percentLoss.toFixed(1)}% pullback — within historical norms. The system was designed for days like this. Your automated contributions are buying at a discount.`,
        };
      
      case 'the_scout':
        return {
          headline: "Opportunity Forming",
          body: `Market down ${percentLoss.toFixed(1)}%. Scouts don't panic at discounts — they position. Your next contribution will buy more shares at lower prices.`,
        };
      
      case 'the_stabilizer':
      default:
        return {
          headline: "Stay the Course",
          body: `Down ${percentLoss.toFixed(1)}% today. I know this feels uncomfortable, but your plan was built for days like this. The long-term trend is what matters, not today's noise.`,
        };
    }
  }

  /**
   * Generate a notification based on current market conditions.
   */
  generateMarketNotification(
    dayChange: number,
    dayChangePercent: number,
    portfolioValue: number,
    tone?: CoachingTone,
  ): VolatilityNotification {
    const effectiveTone = tone || (DEMO_INVESTOR_PROFILE.coachingTone as CoachingTone) || 'the_architect';
    
    if (dayChange >= 0) {
      return this.generateGainNotification(dayChange, dayChangePercent, portfolioValue, effectiveTone);
    } else {
      return this.generateDipNotification(dayChange, dayChangePercent, portfolioValue, effectiveTone);
    }
  }

  /**
   * Generate a weekly summary notification.
   */
  generateWeeklySummary(
    weeklyChange: number,
    weeklyChangePercent: number,
    portfolioValue: number,
    tone: CoachingTone = 'the_architect',
  ): VolatilityNotification {
    const daysCloser = weeklyChange > 0 
      ? this.calculateDaysCloser(weeklyChange, portfolioValue) 
      : 0;
    
    const realWorldEquivalent = weeklyChange > 0 
      ? this.getRealWorldEquivalent(weeklyChange)
      : undefined;

    let headline: string;
    let body: string;

    if (weeklyChange >= 0) {
      headline = "Your Week in Wealth";
      body = `This week, the market paid for ${realWorldEquivalent || 'your progress'} — +$${weeklyChange.toLocaleString()} (+${weeklyChangePercent.toFixed(2)}%). Your Millionaire Date moved ${daysCloser} days closer while you lived your life.`;
    } else {
      headline = "Week in Review";
      body = `A bumpy week (-${Math.abs(weeklyChangePercent).toFixed(2)}%), but your 20-year trend remains intact. Markets always have weeks like this. Your system is designed to thrive through them.`;
    }

    return {
      id: Date.now().toString(),
      type: weeklyChange >= 0 ? 'positive' : 'negative',
      headline,
      body,
      impact: {
        dollarAmount: weeklyChange,
        percentChange: weeklyChangePercent,
        daysCloser,
        realWorldEquivalent,
      },
      tone,
      timestamp: new Date().toISOString(),
      ctaText: 'See Weekly Digest',
      ctaScreen: 'WeeklyDigest',
    };
  }
}

export default new VolatilityCoachingService();
