'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import PriceChart from '@/components/PriceChart';
import RationaleAccordion from '@/components/RationaleAccordion';
import { api, AnalysisResult } from '@/lib/api';
import { Search, RefreshCw } from 'lucide-react';

const SYMBOLS = ['XAUUSD', 'XAGUSD', 'WTIUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'];
const TFS = ['M15', 'H1', 'H4', 'D1'];

export default function SignalsPage() {
  const [symbol, setSymbol] = useState('XAUUSD');
  const [tf, setTf] = useState('H1');
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true); setError(null);
    try {
      setData(await api.analyze(symbol, tf));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { run(); /* eslint-disable-next-line */ }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">تحليل تفصيلي</h1>
          {data?.data_source && (
            <span className={`pill ${data.data_source === 'live'
              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
              : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'}`}>
              {data.data_source === 'live' ? '● بيانات حية' : '○ بيانات اصطناعية'}
            </span>
          )}
        </header>

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
          <button onClick={run} disabled={loading} className="btn-primary disabled:opacity-50">
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {loading ? 'جارٍ التحليل…' : 'تحليل'}
          </button>
        </div>

        {error && <div className="card text-rose-300">{error}</div>}

        {data && (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <PriceChart data={data.candles} entry={data.entry} sl={data.sl} tp1={data.tp1} tp2={data.tp2} tp3={data.tp3} />
              <RationaleAccordion rationale={data.rationale} />
            </div>
            <div className="space-y-4">
              <div className="card">
                <h3 className="font-bold text-white mb-3">ملخص الإشارة</h3>
                <Row label="الاتجاه" value={data.side === 'BUY' ? 'شراء' : 'بيع'} highlight={data.side === 'BUY' ? 'green' : 'red'} />
                <Row label="الدخول" value={data.entry.toFixed(4)} />
                <Row label="وقف الخسارة" value={data.sl.toFixed(4)} highlight="red" />
                <Row label="TP1" value={data.tp1.toFixed(4)} highlight="green" />
                <Row label="TP2" value={data.tp2.toFixed(4)} highlight="green" />
                <Row label="TP3" value={data.tp3.toFixed(4)} highlight="green" />
                <Row label="قوة الإشارة" value={`${data.strength.toFixed(1)} / 10`} />
                <Row label="احتمالية النجاح" value={`${data.win_probability.toFixed(1)}%`} highlight="brand" />
                <Row label="بيئة السوق" value={data.regime} />
                <Row label="مدارس متوافقة" value={`${data.aligned_schools} / 8`} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: 'red' | 'green' | 'brand' }) {
  const color = highlight === 'red' ? 'text-rose-300'
              : highlight === 'green' ? 'text-emerald-300'
              : highlight === 'brand' ? 'text-brand-300'
              : 'text-white';
  return (
    <div className="flex items-center justify-between py-2 border-b border-bg-border last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <span className={`font-mono font-semibold ${color}`}>{value}</span>
    </div>
  );
}
