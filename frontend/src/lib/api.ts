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
  actual?: string;
};

export type EconomicCalendar = {
  source: 'live' | 'synthetic';
  count: number;
  events: NewsItem[];
};

export type SymbolHeadline = {
  title: string;
  summary: string;
  publisher: string;
  link: string;
  published_at: string;
  sentiment: number;
};

export type SymbolNews = {
  symbol: string;
  count: number;
  headlines: SymbolHeadline[];
  aggregate: {
    score: number;
    n_articles: number;
    bullish: number;
    bearish: number;
    neutral: number;
    samples: Array<{ title: string; sentiment: number; publisher: string; link: string }>;
  } | null;
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
  total_schools?: number;
  data_source?: 'live' | 'synthetic';
  mtf?: {
    confluence: number;
    total_timeframes: number;
    confluence_pct: number;
    majority_side: 'BUY' | 'SELL';
    weighted_score: number;
    weighted_confidence: number;
    per_timeframe: Record<string, {
      side: 'BUY' | 'SELL';
      strength: number;
      win_probability: number;
      composite_score: number;
    }>;
  };
};

export type BacktestReport = {
  symbol: string;
  timeframe: string;
  bars: number;
  trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  profit_factor: number;
  avg_r: number;
  expectancy_r: number;
  max_drawdown_r: number;
  largest_win_r: number;
  largest_loss_r: number;
  tp_distribution: { tp1: number; tp2: number; tp3: number; sl: number; timeout: number };
  equity_curve_r: number[];
};

export type CheckoutResponse = {
  subscription_id: number;
  invoice_id: string;
  invoice_url: string;
  amount: number;
  currency: string;
  expires_at: string;
};

export type SubscriptionStatus = {
  id: number;
  plan: string;
  status: 'pending' | 'active' | 'cancelled' | 'expired' | 'failed';
  amount_usd: number;
  payment_provider: string;
  payment_status: string;
  started_at: string | null;
  expires_at: string | null;
};

export const api = {
  generateSignal: (symbol = 'XAUUSD', timeframe = 'H1') =>
    http<Signal>('/api/signals/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframe, lookback: 200 }),
    }),
  latestSignals: (limit = 20) => http<Signal[]>(`/api/signals/latest?limit=${limit}`),
  analyze: (symbol: string, timeframe = 'H1', mtf = false) =>
    http<AnalysisResult>(`/api/analysis/${symbol}?timeframe=${timeframe}&mtf=${mtf}`),
  backtest: (symbol: string, timeframe = 'H1', minStrength = 6.0) =>
    http<BacktestReport>(`/api/backtest/${symbol}?timeframe=${timeframe}&min_strength=${minStrength}&lookback=800`),
  upcomingNews: (hours = 48, impact = 'all') =>
    http<EconomicCalendar>(`/api/news/upcoming?hours=${hours}&impact=${impact}`),
  symbolNews: (symbol: string, limit = 8) =>
    http<SymbolNews>(`/api/news/symbol/${symbol}?limit=${limit}`),
  plans: () => http<Plan[]>('/api/subscriptions/plans'),
  symbols: () => http<{ symbols: string[]; threshold: number }>('/api/signals/symbols/all'),
  health: () => http<{ status: string }>('/health'),
  checkout: (plan: string, email: string) =>
    http<CheckoutResponse>('/api/payments/checkout', {
      method: 'POST',
      // Let the backend build success_url / cancel_url using the request
      // Origin header — that way the actual subscription id ends up in them.
      body: JSON.stringify({ plan, email }),
    }),
  getSubscription: (id: number) => http<SubscriptionStatus>(`/api/payments/subscription/${id}`),
  paymentStatus: () => http<{ provider: string; configured: boolean }>('/api/payments/status'),
};
