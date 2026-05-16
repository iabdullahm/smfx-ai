# SMFX-AI — Smart Metals & FX Intelligence System

نظام تداول ذكي متكامل يدمج **٨ مدارس تحليلية** مع الذكاء الاصطناعي لإنتاج إشارات دقيقة في أسواق **الذهب، الفضة، النفط، والعملات الرئيسية**.

> **الإصدار:** v1.0 MVP — مايو 2026
> **المطوّر:** عبدالله الجهوري
> **النموذج:** اشتراك شهري (SaaS)

---

## نظرة عامة

SMFX-AI يجمع بين منهجيات تحليلية مختلفة في نموذج موحد:

| المدرسة | الإسهام |
|---------|---------|
| Classical TA | RSI, MACD, Bollinger, MAs |
| Price Action | الشموع، الدعم والمقاومة، هيكل السوق |
| Smart Money / ICT | Order Blocks, FVG, Liquidity Pools |
| Wyckoff | دورات السوق (Accumulation/Markup/Distribution/Markdown) |
| Elliott Wave | الموجات الدافعة والتصحيحية |
| Harmonic Patterns | Gartley, Bat, Butterfly, Crab |
| Fundamental Analysis | اقتصاد كلي، عرض/طلب، سياسات نقدية |
| News Analysis | Fed, CPI, NFP, GDP, FOMC |

---

## الهيكل التقني

```
Muasher Pro/
├── backend/                # FastAPI + Python
│   ├── app/
│   │   ├── api/routes/     # نقاط النهاية
│   │   ├── engines/        # محركات التحليل (8 مدارس)
│   │   ├── ai/             # نموذج AI لتجميع الإشارات
│   │   ├── data/           # جلب بيانات السوق
│   │   ├── models/         # نماذج DB
│   │   ├── schemas/        # Pydantic
│   │   └── core/           # config + security
│   └── requirements.txt
├── frontend/               # Next.js 14 + Tailwind (RTL)
│   └── src/
│       ├── app/            # صفحات (Dashboard, Signals, …)
│       ├── components/     # UI
│       └── lib/            # API client
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
└── tests/
```

---

## التشغيل السريع

### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
السيرفر: <http://localhost:8000>
وثائق API التفاعلية: <http://localhost:8000/docs>

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```
الواجهة: <http://localhost:3000>

---

## مخرجات النظام

كل إشارة تتضمن:
- **Entry Zone** — نطاق الدخول المثلى
- **Smart SL** — وقف خسارة ذكي مبني على هيكل السوق
- **TP1, TP2, TP3** — أهداف جني الأرباح
- **Signal Strength** — قوة الإشارة (١–١٠)
- **Win Probability** — احتمالية النجاح (%)
- **Market Regime** — ترندي / عرضي / انعكاسي
- **News Alerts** — تنبيهات الأحداث الاقتصادية

---

## نموذج الشراكة

- المطوّر: ٥٠٪ من صافي الاشتراكات الشهرية
- الشريك التسويقي: ٥٠٪ من صافي الاشتراكات الشهرية

تفاصيل العقد والإيرادات المتوقعة في `docs/PARTNERSHIP.md`.

---

## رخصة الاستخدام
سري وخاص — جميع الحقوق محفوظة © 2026
