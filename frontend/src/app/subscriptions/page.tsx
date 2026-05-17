'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { api, Plan } from '@/lib/api';
import { Check, Crown, CreditCard, AlertCircle, X } from 'lucide-react';
import clsx from 'clsx';

export default function SubscriptionsPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [showCheckout, setShowCheckout] = useState<Plan | null>(null);
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.plans().then(setPlans).catch(() => {}); }, []);

  async function checkout(plan: Plan) {
    if (!email || !email.includes('@')) {
      setError('يرجى إدخال بريد إلكتروني صحيح');
      return;
    }
    setBusy(true); setError(null);
    try {
      const res = await api.checkout(plan.id, email);
      // Redirect to NOWPayments hosted invoice
      window.location.href = res.invoice_url;
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-2">باقات الاشتراك</h1>
        <p className="text-gray-400 mb-2">اختر الباقة المناسبة لاحتياجاتك التداولية</p>
        <p className="text-xs text-brand-300 mb-8 flex items-center gap-2">
          <CreditCard className="w-3.5 h-3.5" />
          ندعم الدفع بـ Visa / Mastercard / Apple Pay — تتحول تلقائياً إلى USDT
        </p>

        <div className="grid md:grid-cols-3 gap-4">
          {plans.map((p) => {
            const featured = p.id === 'monthly';
            return (
              <div key={p.id} className={clsx(
                'card relative',
                featured && 'border-brand-400/50 shadow-[0_0_40px_-10px_rgba(232,162,31,0.4)]'
              )}>
                {featured && (
                  <div className="absolute -top-3 right-4 bg-brand-400 text-bg-base text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                    <Crown className="w-3 h-3" /> الأكثر شعبية
                  </div>
                )}
                <div className="text-sm text-gray-400 mb-1">{p.name_en}</div>
                <h3 className="text-2xl font-bold text-white mb-3">{p.name}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-extrabold text-brand-300">${p.price_usd}</span>
                  <span className="text-gray-400"> / {p.duration_days} يوم</span>
                </div>
                <ul className="space-y-2 mb-6">
                  {p.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                {p.price_usd === 0 ? (
                  <button className="btn-ghost w-full">ابدأ مجاناً</button>
                ) : (
                  <button
                    onClick={() => setShowCheckout(p)}
                    className={featured ? 'btn-primary w-full' : 'btn-ghost w-full'}
                  >
                    اشترك الآن
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div className="card mt-8">
          <h3 className="font-bold text-white mb-2">ضمان الاشتراك</h3>
          <p className="text-sm text-gray-400">
            يمكنك إلغاء اشتراكك في أي وقت. النظام أداة مساعدة للتحليل وليس ضماناً لتحقيق أرباح،
            وقرار التداول النهائي يبقى بيد المتداول.
          </p>
        </div>

        {/* Checkout Modal */}
        {showCheckout && (
          <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
            <div className="card w-full max-w-md relative">
              <button
                onClick={() => { setShowCheckout(null); setError(null); }}
                className="absolute top-3 left-3 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-xl font-bold text-white mb-1">إتمام الاشتراك</h3>
              <p className="text-sm text-gray-400 mb-5">
                {showCheckout.name} — <span className="text-brand-300 font-bold">${showCheckout.price_usd}</span>
              </p>

              <label className="label">البريد الإلكتروني</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-bg-panel border border-bg-border rounded-xl px-3 py-2 mb-4"
              />

              {error && (
                <div className="border border-rose-500/30 bg-rose-500/10 text-rose-200 text-sm p-3 rounded-xl mb-4 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" /> {error}
                </div>
              )}

              <button
                onClick={() => checkout(showCheckout)}
                disabled={busy}
                className="btn-primary w-full disabled:opacity-50"
              >
                <CreditCard className="w-4 h-4" />
                {busy ? 'جارٍ التحويل…' : `ادفع $${showCheckout.price_usd} بـ Visa / Crypto`}
              </button>

              <p className="text-xs text-gray-500 mt-3 text-center">
                ستُحوّل لصفحة دفع آمنة من NOWPayments
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
