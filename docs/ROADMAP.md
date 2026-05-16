# SMFX-AI — Roadmap

## الإطار الزمني (مطابق لمقترح الشراكة)

| المرحلة | الأسبوع | الهدف | الحالة |
|---------|---------|-------|--------|
| ١ — النموذج الأولي | ١–٢ | قاعدة النظام + Classical TA + Price Action + Smart Money + لوحة تحكم | ✅ MVP |
| ٢ — المدارس المتقدمة | ٣–٤ | Elliott Wave + Harmonic + Wyckoff + News integration + Backtest | 🔄 |
| ٣ — اختبار الشريك | ٥–٦ | نسخة تجريبية للشريك، جمع ملاحظات، ضبط دقة | ⏳ |
| ٤ — الإطلاق التجاري | ٧+ | اشتراك شهري، قنوات تسويق، توزيع عوائد | ⏳ |

## Backlog مفصّل

### Backend
- [x] هيكل FastAPI + Routes أساسية
- [x] 8 محركات تحليل (نسخة أولية)
- [x] AI Aggregator
- [ ] Live market data (Yahoo Finance / Twelve Data)
- [ ] WebSocket bus للإشارات الحية
- [ ] قاعدة بيانات Postgres + Alembic migrations
- [ ] Celery worker للتحليل الدوري
- [ ] Backtesting framework
- [ ] Stripe integration للاشتراكات

### Frontend
- [x] صفحة هبوط
- [x] Dashboard (إشارات + بيئة السوق + أخبار)
- [x] صفحة Signals تفصيلية
- [x] صفحة Subscriptions (Plans)
- [ ] تكامل TradingView Charting Library
- [ ] إشعارات Push
- [ ] صفحة Admin
- [ ] تخصيص قائمة الرموز

### AI / Quant
- [ ] جمع بيانات تاريخية للذهب والفضة والنفط و EURUSD/GBPUSD/USDJPY
- [ ] تدريب نموذج XGBoost على Features من المحركات الـ8
- [ ] احتساب احتمالية النجاح بناءً على نتائج تاريخية
- [ ] Self-learning loop (feedback من نتائج الصفقات)
