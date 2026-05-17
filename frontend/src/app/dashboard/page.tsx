'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import SignalCard from '@/components/SignalCard';
import NewsPanel from '@/components/NewsPanel';
import { api, Signal, NewsItem } from '@/lib/api';
import { RefreshCw, Plus, AlertCircle } from 'lucide-react';

const QUICK_SYMBOLS = ['XAUUSD', 'XAGUSD', 'WTIUSD', 'EURUSD', 'GBPUSD', 'USDJPY'];

export default function DashboardPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      const [sigs, n] = await Promise.all([api.latestSignals(12), api.upcomingNews(48)]);
      setSignals(sigs);
      setNews(n.events ?? []);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function generate(symbol: string) {
    setBusy(true);
    try {
      await api.generateSignal(symbol);
      await refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">لوحة التحكم</h1>
            <p className="text-sm text-gray-400">إشارات حية + تنبيهات الأخبار</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={refresh} className="btn-ghost"><RefreshCw className="w-4 h-4" /> تحديث</button>
          </div>
        </header>

        {error && (
          <div className="card mb-4 border-rose-500/30 bg-rose-500/10 text-rose-200 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" /> {error}
          </div>
        )}

        <section className="card mb-6">
          <h2 className="font-bold text-white mb-3">توليد إشارة جديدة</h2>
          <div className="flex flex-wrap gap-2">
            {QUICK_SYMBOLS.map((s) => (
              <button
                key={s}
                onClick={() => generate(s)}
                disabled={busy}
                className="btn-ghost text-sm disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" /> {s}
              </button>
            ))}
            {busy && <span className="text-xs text-gray-400 self-center">جارٍ التحليل…</span>}
          </div>
        </section>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-bold text-white">أحدث الإشارات</h2>
            {signals.length === 0 ? (
              <div className="card text-gray-400 text-sm">لا توجد إشارات بعد — أنشئ أول إشارة بالأعلى.</div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {signals.map((s) => <SignalCard key={s.id} s={s} />)}
              </div>
            )}
          </div>
          <div className="space-y-4">
            <NewsPanel news={news} />
          </div>
        </div>
      </main>
    </div>
  );
}
