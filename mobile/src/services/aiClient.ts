// Lightweight API client for Tutor, Assistant, Coach endpoints
// Uses fetch; expects EXPO_PUBLIC_API_BASE_URL or falls back to localhost

const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 10_000; // Reduced from 25s to 10s for faster failure handling
const ASSISTANT_TIMEOUT_MS = 5_000; // Reduced from 8s to 5s for assistant queries (faster UX)

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  requestId?: string;
  constructor(message: string, status: number, detail?: unknown, requestId?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.requestId = requestId;
  }
}

// ---------- Shared types ----------
export type AskResponse = { response: string; model?: string; confidence_score?: number };
export type ExplainResponse = {
  concept: string;
  explanation: string;
  examples?: string[];
  analogies?: string[];
  visual_aids?: string[];
  generated_at: string;
};
export type QuizQuestion = {
  id: string;
  question: string;
  question_type: string;
  options?: string[];
  correct_answer?: string;
  explanation?: string;
  hints?: string[];
};
export type QuizResponse = {
  topic: string;
  difficulty: string;
  questions: QuizQuestion[];
  generated_at: string;
  regime_context?: {
    current_regime: string;
    regime_confidence: number;
    regime_description: string;
    relevant_strategies: string[];
    common_mistakes: string[];
  };
};
export type DynamicContentResponse = Record<string, any>;
export type AdviceResponse = {
  overview: string;
  risk_considerations: string[];
  controls: string[];
  next_steps: string[];
  disclaimer: string;
  generated_at: string;
  model?: string;
  confidence_score?: number;
};
export type StrategyResponse = {
  strategies: {
    name: string;
    when_to_use: string;
    pros: string[];
    cons: string[];
    risk_controls: string[];
    metrics: string[];
  }[];
  disclaimer: string;
  generated_at: string;
  model?: string;
  confidence_score?: number;
};

function withTimeout<T>(p: Promise<T>, ms: number, abort: AbortController) {
  return new Promise<T>((resolve, reject) => {
    const id = setTimeout(() => {
      abort.abort();
      reject(new ApiError('Request timeout', 408));
    }, ms);
    p.then(
      (v) => {
        clearTimeout(id);
        resolve(v);
      },
      (e) => {
        clearTimeout(id);
        reject(e);
      }
    );
  });
}

async function postJSON<T>(
  path: string,
  body: unknown,
  opts?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const controller = new AbortController();
  const url = `${BASE_URL}${path}`;
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const resPromise = fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
      ...(opts?.headers || {}),
    },
    body: JSON.stringify(body ?? {}),
    signal: controller.signal,
    ...opts,
  });

  const res = await withTimeout(resPromise, opts?.timeoutMs ?? DEFAULT_TIMEOUT_MS, controller);
  const text = await res.text();
  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError(`Invalid JSON from ${path}`, res.status || 500, text, res.headers.get('X-Request-ID') || requestId);
    }
  }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText || 'Request failed';
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status, data, res.headers.get('X-Request-ID') || requestId);
  }
  return data as T;
}

async function getJSON<T>(
  path: string,
  opts?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const controller = new AbortController();
  const url = `${BASE_URL}${path}`;
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const resPromise = fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
      ...(opts?.headers || {}),
    },
    signal: controller.signal,
    ...opts,
  });

  const res = await withTimeout(resPromise, opts?.timeoutMs ?? DEFAULT_TIMEOUT_MS, controller);
  const text = await res.text();
  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError(`Invalid JSON from ${path}`, res.status || 500, text, res.headers.get('X-Request-ID') || requestId);
    }
  }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText || 'Request failed';
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status, data, res.headers.get('X-Request-ID') || requestId);
  }
  return data as T;
}

// ---------- Tutor ----------
export function tutorAsk(req: { user_id: string; question: string; context?: any }) {
  return postJSON<AskResponse>('/tutor/ask', req);
}
export function tutorExplain(req: { user_id: string; concept: string; extra_context?: any }) {
  return postJSON<ExplainResponse>('/tutor/explain', req);
}
export function tutorQuiz(req: { user_id: string; topic: string; difficulty?: string; num_questions?: number }) {
  return postJSON<QuizResponse>('/tutor/quiz', req, { timeoutMs: 30000 }); // 30s timeout for quiz generation
}

export function tutorRegimeAdaptiveQuiz(req: { 
  user_id: string; 
  market_data?: any; 
  difficulty?: string; 
  num_questions?: number 
}) {
  return postJSON<QuizResponse>('/tutor/quiz/regime-adaptive', req, { timeoutMs: 30000 }); // 30s timeout for quiz generation
}

// ---------- Daily Voice Digest ----------
export type VoiceDigestResponse = {
  digest_id: string;
  user_id: string;
  regime_context: {
    current_regime: string;
    regime_confidence: number;
    regime_description: string;
    relevant_strategies: string[];
    common_mistakes: string[];
  };
  voice_script: string;
  key_insights: string[];
  actionable_tips: string[];
  pro_teaser?: string;
  generated_at: string;
  scheduled_for: string;
};

export type RegimeAlertResponse = {
  notification_id: string;
  user_id: string;
  title: string;
  body: string;
  data: {
    type: string;
    old_regime: string;
    new_regime: string;
    confidence: number;
    urgency: string;
  };
  scheduled_for: string;
  type: string;
};

export function generateDailyDigest(req: { 
  user_id: string; 
  market_data?: any; 
  preferred_time?: string 
}) {
  // Use shorter timeout for digest generation (8 seconds)
  return postJSON<VoiceDigestResponse>('/digest/daily', req, { timeoutMs: 8000 });
}

export function createRegimeAlert(req: { 
  user_id: string; 
  regime_change: any; 
  urgency?: string 
}) {
  return postJSON<RegimeAlertResponse>('/digest/regime-alert', req);
}

// ---------- Momentum Missions ----------
export type MomentumMission = {
  mission_id: string;
  user_id: string;
  day_number: number;
  mission_type: string;
  title: string;
  description: string;
  difficulty: string;
  estimated_duration: number;
  content: {
    challenge: string;
    instructions: string;
    learning_objectives: string[];
    regime_context: string;
    success_criteria: string;
  };
  rewards: {
    points: number;
    badges: string[];
    streak_bonus: number;
    experience: number;
  };
  streak_multiplier: number;
  created_at: string;
  due_at: string;
};

export type RecoveryRitual = {
  ritual_id: string;
  user_id: string;
  missed_day: number;
  ritual_type: string;
  title: string;
  description: string;
  content: {
    challenge: string;
    encouragement: string;
    next_steps: string;
  };
  streak_recovery: boolean;
  created_at: string;
};

export type UserProgress = {
  user_id: string;
  current_streak: number;
  longest_streak: number;
  total_missions_completed: number;
  current_mission?: MomentumMission;
  available_recovery?: RecoveryRitual;
  achievements: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    unlocked_at: string;
  }>;
  streak_multiplier: number;
  last_activity: string;
};

export function getUserProgress(req: { 
  user_id: string; 
  include_current_mission?: boolean 
}) {
  return getJSON<UserProgress>(`/missions/progress/${req.user_id}?include_current_mission=${req.include_current_mission ?? true}`);
}

export function generateDailyMission(req: { 
  user_id: string; 
  day_number: number; 
  market_data?: any 
}) {
  return postJSON<MomentumMission>('/missions/daily', req);
}

export function generateRecoveryRitual(req: { 
  user_id: string; 
  missed_day: number 
}) {
  return postJSON<RecoveryRitual>('/missions/recovery', req);
}
export function tutorModule(req: { user_id: string; topic: string; difficulty?: string; content_types?: string[]; learning_objectives?: string[]; user_profile?: any }) {
  return postJSON<DynamicContentResponse>('/tutor/module', req);
}
export function tutorMarketCommentary(req: { user_id?: string; horizon?: string; tone?: string; market_context?: any }) {
  return postJSON<DynamicContentResponse>('/tutor/market-commentary', req, { timeoutMs: 30000 }); // 30s timeout for commentary generation
}

// ---------- Assistant ----------
export function assistantQuery(req: { user_id?: string; prompt: string; context?: any; market_context?: any }) {
  // Use shorter timeout for assistant queries for better UX
  return postJSON<any>('/assistant/query', req, { timeoutMs: ASSISTANT_TIMEOUT_MS });
}

// ---------- Coach ----------
export function coachAdvise(req: { user_id: string; goal: string; risk_tolerance: 'low'|'medium'|'high'; horizon: 'short'|'medium'|'long'; context?: any }) {
  return postJSON<AdviceResponse>('/coach/advise', req);
}
export function coachStrategy(req: { user_id: string; objective: string; market_view: string; constraints?: any }) {
  return postJSON<StrategyResponse>('/coach/strategy', req);
}
