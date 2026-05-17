'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import NewsPanel from '@/components/NewsPanel';
import { api, EconomicCalendar, SymbolNews } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus, ExternalLink, Newspaper, CalendarClock } from 'lucide-react';
import clsx from 'clsx';

const SYMBOLS = ['XAUUSD', 'XAGUSD', 'WTIUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'];

export default function NewsPage() {
  const [tab, setTab] = useState<'calendar' | 'symbol'>('calendar');
  const [cal, setCal] = useState<EconomicCalendar | null>(null);
  const [impact, setImpact] = useState('all');

  const [symbol, setSymbol] = useState('XAUUSD');
  const [news, setNews] = useState<SymbolNews | null>(null);

  useEffect(() => {
    api.upcomingNews(168, impact).then(setCal).catch(() => {});
  }, [impact]);

  useEffect(() => {
    if (tab === 'symbol') api.symbolNews(symbol, 12).then(setNews).catch(() => {});
  }, [symbol, tab]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-2">الأخبار الاقتصادية والعالمية</h1>
        <p className="text-gray-400 mb-6">روزنامة الأحداث وعناوين السوق المحدّثة مع تحليل المشاعر</p>

        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setTab('calendar')}
            className={tab === 'calendar' ? 'btn-primary' : 'btn-ghost'}>
            <CalendarClock className="w-4 h-4" /> الروزنامة الاقتصادية
          </button>
          <button
            onClick={() => setTab('symbol')}
            className={tab === 'symbol' ? 'btn-primary' : 'btn-ghost'}>
            <Newspaper className="w-4 h-4" /> أخبار الأصول
          </button>
        </div>

        {tab === 'calendar' && (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              {['all', 'high', 'medium', 'low'].map((i) => (
                <button key={i} onClick={() => setImpact(i)}
                  className={impact === i ? 'btn-primary' : 'btn-ghost'}>
                  {({ all: 'الكل', high: 'عالي', medium: 'متوسط', low: 'منخفض' } as any)[i]}
                </button>
              ))}
              {cal && (
                <span className={clsx('mr-auto pill',
                  cal.source === 'live'
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                )}>
                  {cal.source === 'live' ? '● مصدر مباشر (Forex Factory)' : '○ مصدر تجريبي'}
                </span>
              )}
            </div>
            <NewsPanel news={cal?.events ?? []} />
          </>
        )}

        {tab === 'symbol' && (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <label className="label me-2 mb-0">الرمز:</label>
              <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
                className="bg-bg-panel border border-bg-border rounded-xl px-3 py-2">
                {SYMBOLS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>

            {news?.aggregate && (
              <div className="card mb-4">
                <h3 className="font-bold text-white mb-3">ملخص المشاعر — {symbol}</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  <SentimentTile icon={<TrendingUp />} label="إيجابية" value={news.aggregate.bullish} accent="green" />
                  <SentimentTile icon={<Minus />} label="محايدة" value={news.aggregate.neutral} accent="gray" />
                  <SentimentTile icon={<TrendingDown />} label="سلبية" value={news.aggregate.bearish} accent="red" />
                  <SentimentTile
                    icon={<Newspaper />}
                    label="الانحياز"
                    value={`${news.aggregate.score > 0 ? '+' : ''}${news.aggregate.score.toFixed(2)}`}
                    accent={news.aggregate.score > 0.1 ? 'green' : news.aggregate.score < -0.1 ? 'red' : 'gray'}
                  />
                </div>
                <SentimentBar score={news.aggregate.score} />
              </div>
            )}

            <div className="card">
              <h3 className="font-bold text-white mb-3">آخر العناوين</h3>
              {news?.headlines?.length ? (
                <ul className="space-y-3">
                  {news.headlines.map((h, i) => (
                    <li key={i} className="p-3 rounded-xl bg-bg-panel border border-bg-border">
                      <div className="flex items-start justify-between gap-3 mb-1">
                        <a href={h.link} target="_blank" rel="noopener noreferrer"
                           className="font-semibold text-white hover:text-brand-300 flex items-center gap-1.5">
                          {h.title}
                          <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                        </a>
                        <span className={clsx('pill text-xs shrink-0',
                          h.sentiment > 0.15 ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : h.sentiment < -0.15 ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-gray-500/15 text-gray-300 border border-gray-500/30'
                        )}>
                          {h.sentiment > 0 ? '+' : ''}{h.sentiment.toFixed(2)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mb-1">
                        {h.publisher}
                        {h.published_at && ` · ${new Date(h.published_at).toLocaleString('ar-EG', { dateStyle: 'short', timeStyle: 'short' })}`}
                      </div>
                      {h.summary && <p className="text-sm text-gray-300 mt-1 leading-relaxed">{h.summary}</p>}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-400 text-sm">لا توجد أخبار حالياً لهذا الرمز.</p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function SentimentTile({ icon, label, value, accent }:
  { icon: React.ReactNode; label: string; value: string | number; accent: 'green' | 'red' | 'gray' }) {
  const color = accent === 'green' ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30'
              : accent === 'red'   ? 'text-rose-300 bg-rose-500/10 border-rose-500/30'
              : 'text-gray-200 bg-gray-500/10 border-gray-500/30';
  return (
    <div className={clsx('rounded-xl p-3 border flex items-center gap-3', color)}>
      <div className="opacity-80">{icon}</div>
      <div>
        <div className="text-xs opacity-80">{label}</div>
        <div className="text-xl font-bold">{value}</div>
      </div>
    </div>
  );
}

function SentimentBar({ score }: { score: number }) {
  const pct = Math.round((score + 1) * 50);   // -1..+1 → 0..100
  return (
    <div className="relative h-2 bg-bg-border rounded-full overflow-hidden">
      <div className="absolute inset-y-0 left-0 right-1/2 bg-rose-500/30" />
      <div className="absolute inset-y-0 right-0 left-1/2 bg-emerald-500/30" />
      <div className="absolute inset-y-0 w-1 bg-brand-400"
           style={{ left: `${pct}%`, transform: 'translateX(-50%)' }} />
    </div>
  );
}
