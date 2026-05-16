'use client';
import { Signal } from '@/lib/api';
import { TrendingUp, TrendingDown, ShieldAlert, Target, BarChart3 } from 'lucide-react';
import clsx from 'clsx';

function Strength({ value }: { value: number }) {
  const bars = 10;
  const filled = Math.round(value);
  return (
    <div className="flex items-end gap-0.5 h-5" aria-label={`قوة ${value}/10`}>
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          className={clsx(
            'w-1.5 rounded-sm',
            i < filled
              ? value >= 8 ? 'bg-emerald-400' : value >= 5 ? 'bg-amber-400' : 'bg-rose-400'
              : 'bg-bg-border',
            i === 0 && 'h-1.5',
            i === 1 && 'h-2',
            i === 2 && 'h-2.5',
            i === 3 && 'h-3',
            i === 4 && 'h-3.5',
            i === 5 && 'h-4',
            i === 6 && 'h-4',
            i === 7 && 'h-4.5',
            i === 8 && 'h-4.5',
            i === 9 && 'h-5',
          )}
        />
      ))}
      <span className="text-xs text-gray-300 mr-1">{value.toFixed(1)}/10</span>
    </div>
  );
}

export default function SignalCard({ s }: { s: Signal }) {
  const isBuy = s.side === 'BUY';
  return (
    <div className="card group hover:border-brand-400/40 transition">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-10 h-10 rounded-xl flex items-center justify-center',
            isBuy ? 'bg-emerald-500/15 text-emerald-300' : 'bg-rose-500/15 text-rose-300'
          )}>
            {isBuy ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
          </div>
          <div>
            <div className="font-bold text-white">{s.symbol} · {s.timeframe}</div>
            <div className="text-xs text-gray-400">
              {new Date(s.created_at).toLocaleString('ar-EG')}
            </div>
          </div>
        </div>
        <span className={isBuy ? 'pill-buy' : 'pill-sell'}>
          {isBuy ? 'شراء' : 'بيع'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <Field label="الدخول" value={s.entry.toFixed(4)} icon={<Target className="w-3 h-3" />} />
        <Field label="وقف الخسارة" value={s.sl.toFixed(4)} icon={<ShieldAlert className="w-3 h-3" />} accent="red" />
        <Field label="TP1" value={s.tp1.toFixed(4)} accent="green" />
        <Field label="TP2" value={s.tp2.toFixed(4)} accent="green" />
        <Field label="TP3" value={s.tp3.toFixed(4)} accent="green" />
        <Field label="بيئة السوق" value={regimeLabel(s.regime)} icon={<BarChart3 className="w-3 h-3" />} />
      </div>

      <div className="flex items-center justify-between border-t border-bg-border pt-3">
        <div>
          <div className="label mb-1">قوة الإشارة</div>
          <Strength value={s.strength} />
        </div>
        <div className="text-left">
          <div className="label mb-1">احتمالية النجاح</div>
          <div className="text-xl font-bold text-brand-300">{s.win_probability.toFixed(1)}%</div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, icon, accent }: { label: string; value: string; icon?: React.ReactNode; accent?: 'red' | 'green' }) {
  return (
    <div>
      <div className="label flex items-center gap-1">{icon}{label}</div>
      <div className={clsx(
        'font-mono font-semibold',
        accent === 'red' ? 'text-rose-300' : accent === 'green' ? 'text-emerald-300' : 'text-white'
      )}>
        {value}
      </div>
    </div>
  );
}

function regimeLabel(r: string) {
  return ({
    trending: 'ترندي',
    ranging: 'عرضي',
    reversal: 'انعكاسي',
    unknown: 'غير محدد',
  } as Record<string, string>)[r] || r;
}
