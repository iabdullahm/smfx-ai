import Link from 'next/link';
import { Sparkles, Brain, LineChart, ShieldCheck, Zap, BookOpen } from 'lucide-react';

const SCHOOLS = [
  'Classical TA',
  'Price Action',
  'Smart Money / ICT',
  'Wyckoff',
  'Elliott Wave',
  'Harmonic Patterns',
  'Fundamental Analysis',
  'News Analysis',
];

export default function Landing() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-500/10 via-transparent to-transparent" />
        <div className="container max-w-6xl mx-auto px-6 py-20 relative">
          <div className="inline-flex items-center gap-2 bg-bg-card border border-bg-border rounded-full px-3 py-1 text-xs text-brand-300 mb-6">
            <Sparkles className="w-3.5 h-3.5" /> SMFX-AI v1.0 · مايو 2026
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold leading-tight text-white mb-4">
            نظام تداول ذكي يدمج <span className="text-brand-400">٨ مدارس تحليلية</span><br />
            مع الذكاء الاصطناعي
          </h1>
          <p className="text-lg text-gray-300 max-w-2xl mb-8">
            إشارات دقيقة على الذهب، الفضة، النفط، والعملات الرئيسية —
            بأهداف TP1/TP2/TP3، وقف خسارة ذكي، تقييم قوة الصفقة، واحتمالية النجاح.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/dashboard" className="btn-primary">ابدأ الآن — لوحة التحكم</Link>
            <Link href="/subscriptions" className="btn-ghost">باقات الاشتراك</Link>
          </div>
        </div>
      </section>

      {/* Schools */}
      <section className="container max-w-6xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold text-white mb-6">المدارس التحليلية المدمجة</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SCHOOLS.map((name) => (
            <div key={name} className="card flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-brand-400" />
              <span className="font-semibold text-white text-sm">{name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container max-w-6xl mx-auto px-6 py-12">
        <div className="grid md:grid-cols-3 gap-4">
          <Feature icon={<Brain className="w-6 h-6" />} title="ذكاء اصطناعي يتعلم"
            text="نموذج يدمج مخرجات المدارس الـ8 بأوزان قابلة للتعديل ويُحسّن أداءه مع الوقت." />
          <Feature icon={<LineChart className="w-6 h-6" />} title="إشارات قابلة للتنفيذ"
            text="دخول، SL ذكي، TP1/TP2/TP3 محسوبة من ATR + هيكل السوق." />
          <Feature icon={<ShieldCheck className="w-6 h-6" />} title="تنبيهات الأخبار"
            text="فلترة تلقائية حول الأحداث عالية التأثير (Fed, CPI, NFP)." />
          <Feature icon={<Zap className="w-6 h-6" />} title="تقييم قوة الصفقة"
            text="مقياس من 1 إلى 10 بناءً على عدد المدارس المتوافقة وثقتها." />
          <Feature icon={<Sparkles className="w-6 h-6" />} title="احتمالية النجاح"
            text="نسبة مئوية مستندة إلى بيانات وأوزان النموذج وبيئة السوق." />
          <Feature icon={<BookOpen className="w-6 h-6" />} title="بيئة السوق"
            text="تصنيف فوري: ترندي / عرضي / انعكاسي — لتختار الاستراتيجية المناسبة." />
        </div>
      </section>

      <footer className="border-t border-bg-border mt-16 py-8 text-center text-sm text-gray-500">
        © 2026 SMFX-AI · جميع الحقوق محفوظة · سري وخاص
      </footer>
    </main>
  );
}

function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="card">
      <div className="w-10 h-10 rounded-xl bg-brand-400/15 text-brand-300 flex items-center justify-center mb-3">
        {icon}
      </div>
      <h3 className="font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{text}</p>
    </div>
  );
}
