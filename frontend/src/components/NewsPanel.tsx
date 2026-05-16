'use client';
import { NewsItem } from '@/lib/api';
import { AlertTriangle, Calendar } from 'lucide-react';
import clsx from 'clsx';

const IMPACT_CLR: Record<string, string> = {
  high:   'bg-rose-500/15 text-rose-300 border-rose-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  low:    'bg-sky-500/15 text-sky-300 border-sky-500/30',
};

const IMPACT_AR: Record<string, string> = { high: 'عالي', medium: 'متوسط', low: 'منخفض' };

export default function NewsPanel({ news }: { news: NewsItem[] }) {
  if (!news.length) {
    return (
      <div className="card text-gray-400 text-sm flex items-center gap-2">
        <Calendar className="w-4 h-4" /> لا توجد أحداث قادمة
      </div>
    );
  }
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-brand-400" />
          <h3 className="font-bold text-white">الأحداث الاقتصادية القادمة</h3>
        </div>
        <span className="text-xs text-gray-400">{news.length} حدث</span>
      </div>
      <ul className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
        {news.map((n, i) => (
          <li key={i} className="flex items-start gap-3 p-3 rounded-xl bg-bg-panel border border-bg-border">
            {n.impact === 'high' && <AlertTriangle className="w-4 h-4 mt-0.5 text-rose-400" />}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={clsx('pill border', IMPACT_CLR[n.impact] || IMPACT_CLR.low)}>
                  {IMPACT_AR[n.impact] || n.impact}
                </span>
                <span className="text-xs text-gray-400 font-bold">{n.currency}</span>
              </div>
              <div className="text-sm text-white">{n.title}</div>
              <div className="text-xs text-gray-400 mt-1">
                {new Date(n.event_time).toLocaleString('ar-EG', { dateStyle: 'short', timeStyle: 'short' })}
                {n.forecast && ` · توقع: ${n.forecast}`}
                {n.previous && ` · سابق: ${n.previous}`}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
