'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { api } from '@/lib/api';
import { CheckCircle, ArrowRight, Loader2 } from 'lucide-react';

export default function PaymentSuccessPage() {
  const [sub, setSub] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const url = new URL(window.location.href);
    const subId = url.searchParams.get('sub');
    if (!subId) { setLoading(false); return; }

    // Poll subscription status for up to 60s (webhook usually arrives in seconds)
    let attempts = 0;
    const poll = async () => {
      try {
        const data = await api.getSubscription(parseInt(subId));
        setSub(data);
        if (data.status === 'active' || attempts > 30) {
          setLoading(false);
          return;
        }
      } catch {/* ignore */}
      attempts++;
      setTimeout(poll, 2000);
    };
    poll();
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="card max-w-md w-full text-center">
          {loading ? (
            <>
              <Loader2 className="w-12 h-12 text-brand-400 animate-spin mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-white mb-2">جارٍ تأكيد الدفع…</h1>
              <p className="text-gray-400">قد يستغرق هذا دقيقة. لا تُغلق هذه الصفحة.</p>
            </>
          ) : (
            <>
              <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-white mb-2">
                {sub?.status === 'active' ? 'تم تفعيل اشتراكك بنجاح!' : 'تم استلام الدفع'}
              </h1>
              {sub && (
                <div className="bg-bg-panel border border-bg-border rounded-xl p-4 my-4 text-right">
                  <Row label="الباقة" value={sub.plan} />
                  <Row label="المبلغ" value={`$${sub.amount_usd}`} />
                  <Row label="الحالة" value={statusLabel(sub.status)} />
                  {sub.expires_at && (
                    <Row label="تنتهي في" value={new Date(sub.expires_at).toLocaleDateString('ar-EG')} />
                  )}
                </div>
              )}
              <Link href="/dashboard" className="btn-primary w-full">
                ابدأ التداول الآن <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1.5 text-sm border-b border-bg-border last:border-0">
      <span className="text-gray-400">{label}</span>
      <span className="text-white font-semibold">{value}</span>
    </div>
  );
}

function statusLabel(s: string) {
  return ({
    active: 'نشط ✓',
    pending: 'قيد التأكيد',
    cancelled: 'ملغي',
    expired: 'منتهي',
  } as Record<string, string>)[s] || s;
}
