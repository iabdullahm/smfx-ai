import type { Metadata } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'SMFX-AI | نظام التداول الذكي',
  description: 'نظام تداول ذكي يدمج 8 مدارس تحليلية مع الذكاء الاصطناعي للمعادن النفيسة والعملات',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
