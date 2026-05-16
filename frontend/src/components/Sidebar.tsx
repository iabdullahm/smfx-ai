'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Activity, CalendarClock, CreditCard, LogIn, Sparkles } from 'lucide-react';
import clsx from 'clsx';

const items = [
  { href: '/dashboard', label: 'لوحة التحكم', icon: LayoutDashboard },
  { href: '/signals', label: 'الإشارات', icon: Activity },
  { href: '/news', label: 'الأخبار الاقتصادية', icon: CalendarClock },
  { href: '/subscriptions', label: 'الاشتراكات', icon: CreditCard },
  { href: '/login', label: 'تسجيل الدخول', icon: LogIn },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-64 bg-bg-panel border-l border-bg-border min-h-screen px-4 py-6 hidden md:flex flex-col">
      <Link href="/" className="flex items-center gap-2 mb-8 px-2">
        <Sparkles className="w-6 h-6 text-brand-400" />
        <div>
          <div className="font-bold text-white text-lg leading-tight">SMFX-AI</div>
          <div className="text-xs text-gray-400">نظام التداول الذكي</div>
        </div>
      </Link>
      <nav className="space-y-1 flex-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname?.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition',
                active
                  ? 'bg-brand-400/15 text-brand-300 border border-brand-400/30'
                  : 'text-gray-300 hover:bg-bg-card'
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="text-xs text-gray-500 mt-4 px-2">v1.0.0 · MVP</div>
    </aside>
  );
}
