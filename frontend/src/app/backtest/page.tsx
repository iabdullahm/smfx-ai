'use client';
import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { api, BacktestReport } from '@/lib/api';
import { Play, RefreshCw, TrendingUp, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import clsx from 'clsx';

const SYMBOLS = ['XAUUSD', 'XAGUSD', 'WTIUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'];
const TFS = ['M15', 'H1', 'H4', 'D1'];

export default function BacktestPage() {
  const [symbol, setSymbol] = useState('XAUUSD');
  const [tf, setTf] = useState('H1');
  const [minStrength, setMinStrength] = useState(6.0);
  const [report, setReport] = useState<BacktestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true); setError(null);
    try {
      const r = await api.backtest(symbol, tf, minStrength);
      setReport(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const equity = report?.equity_curve_r?.map((v, i) => ({ trade: i + 1, equity: v })) ?? [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-brand-400" /> اختبار تاريخي (Backtesting)
        </h1>
        <p className="text-gray-400 mb-6">
          قياس دقة النظام على بيانات تاريخية حقيقية. كل صفقة تُحتسب بـ R (multiples of risk).
        </p>

        <div className="card mb-6 flex flex-wrap gap-3 items-end">
          <div>
            <label className="label">الرمز</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
              className="bg-bg-panel border border-bg-border rounded-xl px-3 py-2">
              {SYMBOLS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="label">الفريم</label>
            <select value={tf} onChange={(e) => setTf(e.target.value)}
              className="bg-bg-panel border border-bg-border rounded-xl px-3 py-2">
              {TFS.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="label">أدنى قوة إشارة</label>
            <input type="number" step="0.5" min={1} max={10}
              value={minStrength} onChange={(e) => setMinStrength(parseFloat(e.target.value))}
              className="bg-bg-panel border border-bg-border rounded-xl px-3 py-2 w-24" />
          </div>
          <button onClick={run} disabled={loading} className="btn-primary disabled:opacity-50">
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'جارٍ الاختبار…' : 'تشغيل الاختبار'}
          </button>
        </div>

        {error && (
          <div className="card border-rose-500/30 bg-rose-500/10 text-rose-200 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" /> {error}
          </div>
        )}

        {report && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="عدد الصفقات" value={report.trades.toString()} />
              <Stat label="نسبة الربح" value={`${report.win_rate_pct}%`}
                accent={report.win_rate_pct >= 55 ? 'green' : report.win_rate_pct >= 40 ? 'amber' : 'red'} />
              <Stat label="Profit Factor" value={report.profit_factor === Infinity ? '∞' : report.profit_factor.toFixed(2)}
                accent={report.profit_factor >= 1.5 ? 'green' : report.profit_factor >= 1 ? 'amber' : 'red'} />
              <Stat label="التوقع/صفقة" value={`${report.expectancy_r >= 0 ? '+' : ''}${report.expectancy_r.toFixed(2)}R`}
                accent={report.expectancy_r > 0 ? 'green' : 'red'} />
              <Stat label="أكبر تراجع" value={`${report.max_drawdown_r.toFixed(1)}R`} accent="red" />
              <Stat label="أكبر ربح" value={`${report.largest_win_r.toFixed(1)}R`} accent="green" />
              <Stat label="أكبر خسارة" value={`${report.largest_loss_r.toFixed(1)}R`} accent="red" />
              <Stat label="عينة" value={`${report.bars} شمعة`} />
            </div>

            <div className="card">
              <h3 className="font-bold text-white mb-4">منحنى الأسهم (Equity Curve)</h3>
              <div className="h-64">
                <ResponsiveContainer>
                  <LineChart data={equity}>
                    <XAxis dataKey="trade" stroke="#6B7280" fontSize={11} />
                    <YAxis stroke="#6B7280" fontSize={11} orientation="right"
                      tickFormatter={(v) => `${v}R`} />
                    <Tooltip
                      contentStyle={{ background: '#121826', border: '1px solid #232C44', borderRadius: 8 }}
                      labelStyle={{ color: '#9CA3AF' }}
                      formatter={(v: number) => [`${v}R`, 'تراكمي']}
                      labelFormatter={(l) => `صفقة #${l}`}
                    />
                    <ReferenceLine y={0} stroke="#4B5563" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="equity" stroke="#E8A21F" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h3 className="font-bold text-white mb-4">توزيع نتائج الصفقات</h3>
              <div className="grid grid-cols-5 gap-3">
                <Bucket label="TP1" value={report.tp_distribution.tp1} accent="green" />
                <Bucket label="TP2" value={report.tp_distribution.tp2} accent="green" />
                <Bucket label="TP3" value={report.tp_distribution.tp3} accent="green" />
                <Bucket label="SL" value={report.tp_distribution.sl} accent="red" />
                <Bucket label="انتهت" value={report.tp_distribution.timeout} accent="amber" />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: 'green' | 'amber' | 'red' }) {
  const color = accent === 'green' ? 'text-emerald-300'
              : accent === 'amber' ? 'text-amber-300'
              : accent === 'red'   ? 'text-rose-300'
              : 'text-white';
  return (
    <div className="card !p-4">
      <div className="label">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function Bucket({ label, value, accent }: { label: string; value: number; accent: 'green' | 'amber' | 'red' }) {
  const color = accent === 'green' ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
              : accent === 'amber' ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
              : 'bg-rose-500/15 text-rose-300 border-rose-500/30';
  return (
    <div className={clsx('rounded-xl p-3 border text-center', color)}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs">{label}</div>
    </div>
  );
}
