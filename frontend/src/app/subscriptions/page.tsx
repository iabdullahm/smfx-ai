'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { api, Plan } from '@/lib/api';
import { Check, Crown } from 'lucide-react';
import clsx from 'clsx';

export default function SubscriptionsPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  useEffect(() => { api.plans().then(setPlans).catch(() => {}); }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-2">باقات الاشتراك</h1>
        <p className="text-gray-400 mb-8">اختر الباقة المناسبة لاحتياجاتك التداولية</p>

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
                <button className={featured ? 'btn-primary w-full' : 'btn-ghost w-full'}>
                  {p.price_usd === 0 ? 'ابدأ مجاناً' : 'اشترك الآن'}
                </button>
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
      </main>
    </div>
  );
}
