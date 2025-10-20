// Lightweight API client for Tutor, Assistant, Coach endpoints
// Uses fetch; expects EXPO_PUBLIC_API_BASE_URL or falls back to localhost

const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8124';
const DEFAULT_TIMEOUT_MS = 25_000;

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

// ---------- Tutor ----------
export function tutorAsk(req: { user_id: string; question: string; context?: any }) {
  return postJSON<AskResponse>('/tutor/ask', req);
}
export function tutorExplain(req: { user_id: string; concept: string; extra_context?: any }) {
  return postJSON<ExplainResponse>('/tutor/explain', req);
}
export function tutorQuiz(req: { user_id: string; topic: string; difficulty?: string; num_questions?: number }) {
  return postJSON<QuizResponse>('/tutor/quiz', req);
}
export function tutorModule(req: { user_id: string; topic: string; difficulty?: string; content_types?: string[]; learning_objectives?: string[]; user_profile?: any }) {
  return postJSON<DynamicContentResponse>('/tutor/module', req);
}
export function tutorMarketCommentary(req: { user_id?: string; horizon?: string; tone?: string; market_context?: any }) {
  return postJSON<DynamicContentResponse>('/tutor/market-commentary', req);
}

// ---------- Assistant ----------
export function assistantQuery(req: { user_id?: string; prompt: string; context?: any; market_context?: any }) {
  return postJSON<any>('/assistant/query', req);
}

// ---------- Coach ----------
export function coachAdvise(req: { user_id: string; goal: string; risk_tolerance: 'low'|'medium'|'high'; horizon: 'short'|'medium'|'long'; context?: any }) {
  return postJSON<AdviceResponse>('/coach/advise', req);
}
export function coachStrategy(req: { user_id: string; objective: string; market_view: string; constraints?: any }) {
  return postJSON<StrategyResponse>('/coach/strategy', req);
}
