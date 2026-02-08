// src/shared/learningPaths.ts - Learning paths for RichesReach AI-driven education
// Structured as Record<string, Path> for type safety and easy export

export interface LearningStep {
  id: string;
  title: string;
  duration: number; // in minutes
  type: 'video' | 'article' | 'quiz' | 'interactive';
  content?: string; // URL or ID for media
  prerequisites?: string[]; // Step IDs
  nextStep?: string; // ID for branching
}

export interface LearningPath {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  steps: LearningStep[];
  // Backward compatibility properties
  modules?: LearningModule[];
  totalModules?: number;
  estimatedTime?: string;
  icon?: string;
  color?: string;
}

export type PathId = string;

export const LEARNING_PATHS: Record<string, LearningPath> = {
  creditBasics: {
    id: 'creditBasics',
    title: 'Credit Basics',
    description: 'Build a strong foundation for your credit score.',
    difficulty: 'beginner',
    icon: 'credit-card',
    color: '#007AFF',
    estimatedTime: '16 minutes',
    steps: [
      {
        id: 'what-is-credit',
        title: 'What is Credit?',
        duration: 3,
        type: 'video',
        content: 'videos/credit-intro.mp4',
      },
      {
        id: 'score-components',
        title: 'Understanding Score Components',
        duration: 5,
        type: 'article',
      },
      {
        id: 'payment-history',
        title: 'The Power of Payment History',
        duration: 4,
        type: 'interactive',
        prerequisites: ['what-is-credit'],
      },
      {
        id: 'credit-utilization',
        title: 'Managing Credit Utilization',
        duration: 4,
        type: 'quiz',
        nextStep: 'advanced-credit',
      },
    ],
  },
  advancedCredit: {
    id: 'advancedCredit',
    title: 'Advanced Credit Strategies',
    description: 'Optimize for loans and long-term growth.',
    difficulty: 'intermediate',
    icon: 'trending-up',
    color: '#34C759',
    estimatedTime: '18 minutes',
    steps: [
      {
        id: 'debt-snowball',
        title: 'Debt Snowball Method',
        duration: 6,
        type: 'video',
        content: 'videos/debt-snowball.mp4',
      },
      {
        id: 'credit-mix',
        title: 'Building a Diverse Credit Mix',
        duration: 5,
        type: 'article',
      },
      {
        id: 'dispute-errors',
        title: 'Disputing Errors on Your Report',
        duration: 7,
        type: 'interactive',
        prerequisites: ['score-components'],
      },
    ],
  },
  defiBasics: {
    id: 'defiBasics',
    title: 'DeFi Fortress 101',
    description: 'Build your first yield-earning position, step by step.',
    difficulty: 'beginner',
    icon: 'shield',
    color: '#10B981',
    estimatedTime: '20 minutes',
    steps: [
      {
        id: 'what-is-defi',
        title: 'What is DeFi?',
        duration: 4,
        type: 'article',
      },
      {
        id: 'wallets-explained',
        title: 'Your Wallet, Your Keys',
        duration: 5,
        type: 'interactive',
        prerequisites: ['what-is-defi'],
      },
      {
        id: 'yield-farming-basics',
        title: 'How Yield Farming Works',
        duration: 4,
        type: 'video',
        content: 'videos/yield-farming-basics.mp4',
      },
      {
        id: 'risk-management-defi',
        title: 'Protecting Your Position',
        duration: 4,
        type: 'article',
        prerequisites: ['yield-farming-basics'],
      },
      {
        id: 'first-fortress-deposit',
        title: 'Your First Fortress Deposit',
        duration: 3,
        type: 'quiz',
        prerequisites: ['risk-management-defi'],
      },
    ],
  },
  defiAdvanced: {
    id: 'defiAdvanced',
    title: 'DeFi Mastery',
    description: 'Advanced strategies: impermanent loss, leverage, DAO governance, and auto-compounding.',
    difficulty: 'advanced',
    icon: 'zap',
    color: '#8B5CF6',
    estimatedTime: '30 minutes',
    steps: [
      {
        id: 'impermanent-loss-deep-dive',
        title: 'Impermanent Loss Mastery',
        duration: 6,
        type: 'interactive',
      },
      {
        id: 'leverage-strategies',
        title: 'Leverage & Looping Strategies',
        duration: 5,
        type: 'article',
        prerequisites: ['impermanent-loss-deep-dive'],
      },
      {
        id: 'vault-auto-compound',
        title: 'ERC-4626 Vaults & Auto-Compounding',
        duration: 5,
        type: 'video',
        content: 'videos/vault-auto-compound.mp4',
        prerequisites: ['leverage-strategies'],
      },
      {
        id: 'dao-governance',
        title: 'DAO Governance & Voting Power',
        duration: 6,
        type: 'article',
      },
      {
        id: 'multi-chain-strategies',
        title: 'Multi-Chain Portfolio Strategies',
        duration: 5,
        type: 'interactive',
        prerequisites: ['vault-auto-compound'],
      },
      {
        id: 'defi-mastery-quiz',
        title: 'DeFi Mastery Final Assessment',
        duration: 3,
        type: 'quiz',
        prerequisites: ['multi-chain-strategies', 'dao-governance'],
      },
    ],
  },
  portfolioBasics: {
    id: 'portfolioBasics',
    title: 'Portfolio Basics',
    description: 'Learn the fundamentals of building and managing your investment portfolio.',
    difficulty: 'beginner',
    icon: 'pie-chart',
    color: '#007AFF',
    estimatedTime: '15 minutes',
    steps: [
      {
        id: 'what-is-investing',
        title: 'What is Investing?',
        duration: 5,
        type: 'article',
      },
      {
        id: 'asset-allocation',
        title: 'Asset Allocation Basics',
        duration: 6,
        type: 'interactive',
      },
      {
        id: 'diversification',
        title: 'The Power of Diversification',
        duration: 4,
        type: 'video',
        content: 'videos/diversification.mp4',
      },
    ],
  },
};

// Helper functions - no syntax risks here
export function getLearningPath(pathId: PathId): LearningPath | null {
  return LEARNING_PATHS[pathId] || null;
}

export function getStep(pathId: PathId, stepId: string): LearningStep | null {
  const path = getLearningPath(pathId);
  return path?.steps.find((step) => step.id === stepId) || null;
}

export function getPathProgress(pathId: PathId, completedSteps: string[]): number {
  const path = getLearningPath(pathId);
  if (!path) return 0;
  const completed = completedSteps.filter((id) => path.steps.some((step) => step.id === id));
  return Math.round((completed.length / path.steps.length) * 100);
}

// Populate backward compatibility properties
Object.values(LEARNING_PATHS).forEach((path) => {
  path.totalModules = path.steps.length;
  path.modules = getLegacyModules(path.id as PathId);
});

// Dev-time validation
if (__DEV__) {
  // Development logging removed - use logger if needed
  Object.values(LEARNING_PATHS).forEach((path) => {
    if (path.steps.length === 0) {
      // Empty path validation removed
    }
  });
}

// Backward compatibility exports
export const CREDIT_BUILDING_PATH = LEARNING_PATHS.creditBasics;

// Legacy interface for backward compatibility
export interface LearningModule {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  duration: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  completed: boolean;
  locked: boolean;
  content: {
    sections: Array<{
      id: string;
      title: string;
      type: 'text' | 'interactive' | 'quiz' | 'video' | 'example';
      content: string;
    }>;
  };
}

// Convert new structure to legacy format for compatibility
export function getLegacyModules(pathId: PathId): LearningModule[] {
  const path = getLearningPath(pathId);
  if (!path) return [];
  
  return path.steps.map((step, index) => ({
    id: step.id,
    title: step.title,
    description: step.title, // Use title as description fallback
    icon: 'book',
    color: path.difficulty === 'beginner' ? '#34C759' : path.difficulty === 'intermediate' ? '#007AFF' : '#FF9500',
    duration: `${step.duration} min`,
    difficulty: path.difficulty === 'beginner' ? 'Beginner' as const : path.difficulty === 'intermediate' ? 'Intermediate' as const : 'Advanced' as const,
    completed: false,
    locked: index > 0, // Lock all except first
    content: {
      sections: [
        {
          id: step.id,
          title: step.title,
          type: step.type === 'video' ? 'video' as const : step.type === 'quiz' ? 'quiz' as const : step.type === 'interactive' ? 'interactive' as const : 'text' as const,
          content: step.content || step.title,
        },
      ],
    },
  }));
}
