'use client';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import NewsPanel from '@/components/NewsPanel';
import { api, NewsItem } from '@/lib/api';

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [impact, setImpact] = useState('all');
  useEffect(() => { api.upcomingNews(168, impact).then(setNews).catch(() => {}); }, [impact]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-2">الأخبار الاقتصادية</h1>
        <p className="text-gray-400 mb-6">الأحداث القادمة خلال الأسبوع</p>
        <div className="flex gap-2 mb-4">
          {['all', 'high', 'medium', 'low'].map((i) => (
            <button key={i} onClick={() => setImpact(i)}
              className={impact === i ? 'btn-primary' : 'btn-ghost'}>
              {({ all: 'الكل', high: 'عالي', medium: 'متوسط', low: 'منخفض' } as any)[i]}
            </button>
          ))}
        </div>
        <NewsPanel news={news} />
      </main>
    </div>
  );
}
