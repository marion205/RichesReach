/**
 * Centralized Test IDs for Detox E2E Testing
 * Use these constants to ensure consistency across the app
 */

export const TID = {
  tabs: {
    voiceAI: 'voice-ai-tab',
    memeQuest: 'memequest-tab',
    coach: 'coach-tab',
    learning: 'learning-tab',
    community: 'community-tab',
  },
  voice: {
    orb: 'voice-orb',
    selector: 'voice-selector',
    nova: 'voice-selector-nova',
    executeTrade: 'execute-trade-button',
    viewPortfolio: 'view-portfolio-button',
  },
  memeQuest: {
    frogTemplate: 'frog-template',
    voiceLaunch: 'voice-launch',
    animate: 'animate-button',
    sendTip: 'send-tip-button',
  },
  coach: {
    bullishSpread: 'bullish-spread-strategy',
    executeTrade: 'coach-execute-trade',
  },
  learning: {
    startQuiz: 'start-options-quiz-button',
    callOption: 'call-option-answer',
    putOption: 'put-option-answer',
    next: 'next-button',
    showResults: 'show-results-button',
  },
  community: {
    bipocLeague: 'bipoc-wealth-builders-league',
    joinDiscussion: 'join-discussion-button',
    messageInput: 'message-input',
    sendMessage: 'send-message-button',
  },
  screens: {
    home: 'home-screen',
    voiceAI: 'voice-ai-screen',
    memeQuest: 'memequest-screen',
    coach: 'coach-screen',
    learning: 'learning-screen',
    community: 'community-screen',
  },
} as const;

