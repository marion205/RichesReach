/**
 * FeatureUnlockService
 * ====================
 * Manages feature gating based on user maturity stage.
 * Implements the WealthTech product logic from the blueprint.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export type MaturityStage = 'starter' | 'builder' | 'optimizer' | 'advanced';

export interface FeatureConfig {
  id: string;
  name: string;
  description: string;
  minStage: MaturityStage;
  icon: string;
  screen: string;
  category: 'foundation' | 'growth' | 'optimization' | 'advanced';
}

export interface UnlockProgress {
  currentStage: MaturityStage;
  totalAssets: number;
  unlockedFeatures: string[];
  lockedFeatures: string[];
  nextStageRequirements: {
    stage: MaturityStage;
    requirements: string[];
    progress: number; // 0-100
  } | null;
}

// All features with their unlock requirements
const ALL_FEATURES: FeatureConfig[] = [
  // Foundation (Starter)
  { id: 'leak_detector', name: 'Leak Detector', description: 'Find and stop money drains', minStage: 'starter', icon: 'search', screen: 'LeakDetector', category: 'foundation' },
  { id: 'emergency_fund', name: 'Emergency Fund', description: 'Build your financial fortress', minStage: 'starter', icon: 'shield', screen: 'FinancialHealth', category: 'foundation' },
  { id: 'credit_health', name: 'Credit Health', description: 'Track and improve your score', minStage: 'starter', icon: 'credit-card', screen: 'credit', category: 'foundation' },
  { id: 'budget_tools', name: 'Budget Tools', description: 'Track spending and cash flow', minStage: 'starter', icon: 'pie-chart', screen: 'budgeting', category: 'foundation' },
  { id: 'net_worth', name: 'Net Worth', description: 'Track your total wealth', minStage: 'starter', icon: 'trending-up', screen: 'NetWorth', category: 'foundation' },

  // Growth (Builder)
  { id: 'portfolio_builder', name: 'AI Portfolio Builder', description: 'Personalized investment plan', minStage: 'builder', icon: 'cpu', screen: 'AIPortfolioBuilder', category: 'growth' },
  { id: 'wealth_arrival', name: 'Wealth Arrival', description: 'Your millionaire timeline', minStage: 'builder', icon: 'flag', screen: 'WealthArrival', category: 'growth' },
  { id: 'auto_invest', name: 'Auto-Invest', description: 'Automated contributions', minStage: 'builder', icon: 'repeat', screen: 'Reallocate', category: 'growth' },
  { id: 'investor_profile', name: 'Investor Identity', description: 'Your behavioral profile', minStage: 'builder', icon: 'user', screen: 'InvestorProfile', category: 'growth' },
  { id: 'weekly_digest', name: 'Weekly Digest', description: 'Personalized wealth report', minStage: 'builder', icon: 'bar-chart-2', screen: 'WeeklyDigest', category: 'growth' },

  // Optimization (Optimizer)
  { id: 'tax_optimizer', name: 'Tax Optimizer', description: 'Tax-loss harvesting', minStage: 'optimizer', icon: 'sliders', screen: 'portfolio', category: 'optimization' },
  { id: 'bias_detection', name: 'Bias Detection', description: 'Real-time portfolio analysis', minStage: 'optimizer', icon: 'alert-triangle', screen: 'InvestorProfile', category: 'optimization' },
  { id: 'scenario_modeling', name: 'Life Decisions', description: 'What-if analysis', minStage: 'optimizer', icon: 'git-branch', screen: 'LifeDecision', category: 'optimization' },
  { id: 'income_intelligence', name: 'Income Intelligence', description: 'Optimize your cash flow', minStage: 'optimizer', icon: 'dollar-sign', screen: 'IncomeIntelligence', category: 'optimization' },
  { id: 'reallocation', name: 'Smart Reallocation', description: 'AI-powered rebalancing', minStage: 'optimizer', icon: 'refresh-cw', screen: 'Reallocate', category: 'optimization' },

  // Advanced
  { id: 'options_lab', name: 'Options Lab', description: 'Covered calls, spreads, hedging', minStage: 'advanced', icon: 'layers', screen: 'options', category: 'advanced' },
  { id: 'private_markets', name: 'Private Markets', description: 'PE and venture access', minStage: 'advanced', icon: 'briefcase', screen: 'private-markets', category: 'advanced' },
  { id: 'defi_integration', name: 'DeFi Integration', description: 'Yield farming, staking', minStage: 'advanced', icon: 'link', screen: 'defi', category: 'advanced' },
  { id: 'custom_strategies', name: 'Custom Strategies', description: 'Build your own models', minStage: 'advanced', icon: 'code', screen: 'AIPortfolioBuilder', category: 'advanced' },
];

// Stage requirements
const STAGE_REQUIREMENTS: Record<MaturityStage, { minAssets: number; requirements: string[] }> = {
  starter: {
    minAssets: 0,
    requirements: ['Complete onboarding', 'Connect an account'],
  },
  builder: {
    minAssets: 5000,
    requirements: ['$5,000+ total assets', 'Steady income', 'Emergency fund started'],
  },
  optimizer: {
    minAssets: 100000,
    requirements: ['$100,000+ total assets', 'Diversified portfolio', 'Tax-advantaged accounts'],
  },
  advanced: {
    minAssets: 500000,
    requirements: ['$500,000+ total assets', 'Options experience', 'Alternative investments interest'],
  },
};

const STAGE_ORDER: MaturityStage[] = ['starter', 'builder', 'optimizer', 'advanced'];

class FeatureUnlockService {
  private currentStage: MaturityStage = 'starter';
  private storageKey = '@rr_maturity_stage';

  async initialize(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(this.storageKey);
      if (stored && STAGE_ORDER.includes(stored as MaturityStage)) {
        this.currentStage = stored as MaturityStage;
      }
    } catch (error) {
      console.warn('Failed to load maturity stage:', error);
    }
  }

  async setStage(stage: MaturityStage): Promise<void> {
    this.currentStage = stage;
    try {
      await AsyncStorage.setItem(this.storageKey, stage);
    } catch (error) {
      console.warn('Failed to save maturity stage:', error);
    }
  }

  getStage(): MaturityStage {
    return this.currentStage;
  }

  /**
   * Determine stage based on total assets and other factors.
   */
  determineStage(totalAssets: number, hasOptionsActivity: boolean = false): MaturityStage {
    if (totalAssets >= 500000 || (totalAssets >= 250000 && hasOptionsActivity)) {
      return 'advanced';
    }
    if (totalAssets >= 100000) {
      return 'optimizer';
    }
    if (totalAssets >= 5000) {
      return 'builder';
    }
    return 'starter';
  }

  /**
   * Check if a feature is unlocked for the current stage.
   */
  isFeatureUnlocked(featureId: string): boolean {
    const feature = ALL_FEATURES.find(f => f.id === featureId);
    if (!feature) return false;

    const currentIndex = STAGE_ORDER.indexOf(this.currentStage);
    const requiredIndex = STAGE_ORDER.indexOf(feature.minStage);

    return currentIndex >= requiredIndex;
  }

  /**
   * Get all features with their unlock status.
   */
  getAllFeatures(): Array<FeatureConfig & { isUnlocked: boolean }> {
    const currentIndex = STAGE_ORDER.indexOf(this.currentStage);

    return ALL_FEATURES.map(feature => ({
      ...feature,
      isUnlocked: currentIndex >= STAGE_ORDER.indexOf(feature.minStage),
    }));
  }

  /**
   * Get features for a specific category.
   */
  getFeaturesByCategory(category: FeatureConfig['category']): Array<FeatureConfig & { isUnlocked: boolean }> {
    return this.getAllFeatures().filter(f => f.category === category);
  }

  /**
   * Get unlocked features only.
   */
  getUnlockedFeatures(): FeatureConfig[] {
    return this.getAllFeatures().filter(f => f.isUnlocked);
  }

  /**
   * Get locked features (for "coming soon" display).
   */
  getLockedFeatures(): Array<FeatureConfig & { unlockStage: MaturityStage }> {
    return this.getAllFeatures()
      .filter(f => !f.isUnlocked)
      .map(f => ({ ...f, unlockStage: f.minStage }));
  }

  /**
   * Get progress towards the next stage.
   */
  getUnlockProgress(totalAssets: number): UnlockProgress {
    const currentIndex = STAGE_ORDER.indexOf(this.currentStage);
    const nextStage = currentIndex < STAGE_ORDER.length - 1 ? STAGE_ORDER[currentIndex + 1] : null;

    let nextStageRequirements = null;
    if (nextStage) {
      const req = STAGE_REQUIREMENTS[nextStage];
      const progress = Math.min(100, Math.round((totalAssets / req.minAssets) * 100));
      nextStageRequirements = {
        stage: nextStage,
        requirements: req.requirements,
        progress,
      };
    }

    const allFeatures = this.getAllFeatures();

    return {
      currentStage: this.currentStage,
      totalAssets,
      unlockedFeatures: allFeatures.filter(f => f.isUnlocked).map(f => f.id),
      lockedFeatures: allFeatures.filter(f => !f.isUnlocked).map(f => f.id),
      nextStageRequirements,
    };
  }

  /**
   * Get stage display info.
   */
  getStageInfo(stage: MaturityStage): {
    title: string;
    emoji: string;
    color: string;
    description: string;
  } {
    const info: Record<MaturityStage, ReturnType<typeof this.getStageInfo>> = {
      starter: {
        title: 'Starter',
        emoji: '🌱',
        color: '#10B981',
        description: 'Building your foundation',
      },
      builder: {
        title: 'Builder',
        emoji: '🏗️',
        color: '#6366F1',
        description: 'Growing your wealth',
      },
      optimizer: {
        title: 'Optimizer',
        emoji: '⚡',
        color: '#F59E0B',
        description: 'Maximizing efficiency',
      },
      advanced: {
        title: 'Advanced',
        emoji: '🎯',
        color: '#8B5CF6',
        description: 'Sophisticated strategies',
      },
    };
    return info[stage];
  }
}

export default new FeatureUnlockService();
