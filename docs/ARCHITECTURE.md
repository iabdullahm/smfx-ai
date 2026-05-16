# SMFX-AI — Architecture

## نظرة عامة معمارية

```
┌───────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                     │
│  Dashboard │ Signals │ News │ Subscriptions │ Login       │
└──────────────────────────┬────────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼────────────────────────────────┐
│                  Backend API (FastAPI)                    │
│  /auth │ /signals │ /analysis │ /news │ /subscriptions    │
└─────┬─────────────────────┬───────────────────┬───────────┘
      │                     │                   │
┌─────▼────────┐    ┌───────▼──────────┐  ┌─────▼─────────┐
│ Data Layer   │    │ Analysis Engines │  │ AI Aggregator │
│ Market feed  │    │  ┌─────────────┐ │  │  scoring +    │
│ News feed    │───▶│  │ 8 schools   │ │─▶│  probability  │
│ Storage      │    │  │ pipelines   │ │  │  + regime     │
└──────────────┘    │  └─────────────┘ │  └───────────────┘
                    └──────────────────┘
```

## المكونات

### 1. Data Layer (`backend/app/data/`)
- `market_feed.py` — جلب OHLCV من مصادر بيانات (mock الآن، Yahoo/Twelve Data/CCXT لاحقاً)
- `news_feed.py` — جلب الأخبار الاقتصادية (Forex Factory / Investing calendar mock)

### 2. Analysis Engines (`backend/app/engines/`)
كل محرك يستقبل DataFrame من OHLCV ويُرجع `EngineOutput` موحد:
```python
class EngineOutput:
    score: float          # -1 (بيع قوي) → +1 (شراء قوي)
    confidence: float     # 0..1
    signals: list[dict]   # تفاصيل الإشارات الفنية
    notes: list[str]      # ملاحظات قابلة للقراءة
```

المحركات الثمانية:
1. `classical_ta.py` — مؤشرات (RSI, MACD, Bollinger, EMAs)
2. `price_action.py` — أنماط الشموع + الدعم/المقاومة + BOS/CHoCH
3. `smart_money.py` — Order Blocks, FVG, Liquidity Sweeps
4. `wyckoff.py` — كشف مراحل السوق
5. `elliott_wave.py` — تتبع الموجات (مبسّط)
6. `harmonic.py` — كشف Gartley/Bat/Butterfly/Crab
7. `fundamental.py` — تجميع بيانات اقتصاد كلي
8. `news_analysis.py` — تأثير الأخبار + تجنّب الفترات الحساسة

### 3. AI Aggregator (`backend/app/ai/`)
- `aggregator.py` — يدمج نتائج المحركات الـ8 بأوزان قابلة للتعديل
- `model.py` — منطق احتساب `Signal Strength (1–10)` و `Win Probability (%)`
- `regime.py` — تصنيف بيئة السوق (ترندي / عرضي / انعكاسي)

### 4. API Routes (`backend/app/api/routes/`)
- `POST /api/signals/generate` — يولد إشارة لرمز معين
- `GET  /api/signals/latest` — أحدث الإشارات
- `GET  /api/analysis/{symbol}` — تحليل تفصيلي بكل مدرسة
- `GET  /api/news/upcoming` — الأحداث القادمة عالية التأثير
- `POST /api/auth/login` — تسجيل دخول
- `GET  /api/subscriptions/me` — حالة اشتراك المستخدم

### 5. Models
```
User(id, email, password_hash, role, created_at)
Subscription(id, user_id, plan, status, started_at, expires_at)
Signal(id, symbol, side, entry, sl, tp1, tp2, tp3, strength, win_prob, regime, created_at)
NewsEvent(id, title, currency, impact, time, actual, forecast, previous)
```

## التدفق (Flow)
1. **Cron job** كل N دقيقة → يطلب OHLCV لكل رمز نشط.
2. كل **engine** يحلل البيانات ويُرجع score+confidence.
3. **Aggregator** يجمع النتائج بأوزان → ينتج Signal.
4. إن كانت قوة الإشارة ≥ عتبة → تُخزَّن وتُبث للمشتركين عبر WebSocket.
5. الواجهة تستقبل وتعرض البطاقة.

## الأمان
- JWT للمصادقة
- التشفير bcrypt لكلمات المرور
- مراقبة Rate-limit على نقاط النهاية الثقيلة
- تقسيم الصلاحيات: `admin / subscriber / trial`

## الأداء
- تخزين مؤقت Redis للبيانات السعرية الحية (مستقبلاً)
- WebSocket للبث الفوري
- Worker Queue (Celery / RQ) للتحليل غير المتزامن

## المراحل التالية
انظر `ROADMAP.md`.
