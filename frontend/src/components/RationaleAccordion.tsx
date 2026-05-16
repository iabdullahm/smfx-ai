'use client';
import { useState } from 'react';
import { EngineDetail } from '@/lib/api';
import { ChevronDown } from 'lucide-react';
import clsx from 'clsx';

const SCHOOL_AR: Record<string, string> = {
  classical_ta:  'التحليل الفني الكلاسيكي',
  price_action:  'Price Action',
  smart_money:   'Smart Money / ICT',
  wyckoff:       'Wyckoff',
  elliott_wave:  'Elliott Wave',
  harmonic:      'الأنماط التوافقية',
  fundamental:   'التحليل الأساسي',
  news_analysis: 'الأخبار الاقتصادية',
};

export default function RationaleAccordion({ rationale }: { rationale: Record<string, EngineDetail> }) {
  const [openKey, setOpenKey] = useState<string | null>(null);

  return (
    <div className="card">
      <h3 className="font-bold text-white mb-4">تفصيل المدارس التحليلية الثمانية</h3>
      <div className="space-y-2">
        {Object.entries(rationale).map(([key, det]) => {
          const open = openKey === key;
          const dir = det.score > 0.15 ? 'صعودي' : det.score < -0.15 ? 'هبوطي' : 'محايد';
          const dirColor = det.score > 0.15 ? 'text-emerald-300' : det.score < -0.15 ? 'text-rose-300' : 'text-amber-300';
          return (
            <div key={key} className="border border-bg-border rounded-xl overflow-hidden">
              <button
                onClick={() => setOpenKey(open ? null : key)}
                className="w-full flex items-center justify-between px-4 py-3 bg-bg-panel hover:bg-bg-card transition text-right"
              >
                <div className="flex items-center gap-3">
                  <ChevronDown className={clsx('w-4 h-4 transition', open && 'rotate-180')} />
                  <span className="font-semibold text-white">{SCHOOL_AR[key] || key}</span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className={dirColor}>{dir}</span>
                  <span className="text-gray-400">ثقة: {(det.confidence * 100).toFixed(0)}%</span>
                  <span className="text-gray-500">وزن: {(det.weight * 100).toFixed(0)}%</span>
                </div>
              </button>
              {open && (
                <div className="px-4 py-3 bg-bg-base/40 text-sm">
                  {det.notes.length > 0 && (
                    <ul className="space-y-1 mb-3">
                      {det.notes.map((n, i) => (
                        <li key={i} className="text-gray-200 flex items-start gap-2">
                          <span className="text-brand-400 mt-1">◆</span>
                          <span>{n}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {det.signals.length > 0 && (
                    <details className="text-xs text-gray-400">
                      <summary className="cursor-pointer">إشارات تقنية مفصّلة</summary>
                      <pre className="mt-2 p-2 bg-bg-card rounded-lg overflow-x-auto" dir="ltr">
{JSON.stringify(det.signals, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
