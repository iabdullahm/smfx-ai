// Lightweight typed API client for SMFX-AI backend.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    cache: 'no-store',
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type Signal = {
  id: number;
  symbol: string;
  timeframe: string;
  side: 'BUY' | 'SELL';
  entry: number;
  sl: number;
  tp1: number;
  tp2: number;
  tp3: number;
  strength: number;
  win_probability: number;
  regime: string;
  rationale: Record<string, EngineDetail>;
  created_at: string;
};

export type EngineDetail = {
  score: number;
  confidence: number;
  notes: string[];
  signals: any[];
  weight: number;
};

export type NewsItem = {
  title: string;
  currency: string;
  impact: string;
  event_time: string;
  forecast: string;
  previous: string;
};

export type Plan = {
  id: string;
  name: string;
  name_en: string;
  price_usd: number;
  duration_days: number;
  features: string[];
};

export type AnalysisResult = Signal & {
  candles: Array<{ time: string; open: number; high: number; low: number; close: number; volume: number }>;
  symbol: string;
  composite_score: number;
  composite_confidence: number;
  aligned_schools: number;
  data_source?: 'live' | 'synthetic';
};

export const api = {
  generateSignal: (symbol = 'XAUUSD', timeframe = 'H1') =>
    http<Signal>('/api/signals/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframe, lookback: 200 }),
    }),
  latestSignals: (limit = 20) => http<Signal[]>(`/api/signals/latest?limit=${limit}`),
  analyze: (symbol: string, timeframe = 'H1') =>
    http<AnalysisResult>(`/api/analysis/${symbol}?timeframe=${timeframe}`),
  upcomingNews: (hours = 48, impact = 'all') =>
    http<NewsItem[]>(`/api/news/upcoming?hours=${hours}&impact=${impact}`),
  plans: () => http<Plan[]>('/api/subscriptions/plans'),
  symbols: () => http<{ symbols: string[]; threshold: number }>('/api/signals/symbols/all'),
  health: () => http<{ status: string }>('/health'),
};
