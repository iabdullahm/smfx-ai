# البدء السريع — SMFX-AI

## المتطلبات
- **Python 3.10+**
- **Node.js 18+** (و npm أو pnpm)

## ١) تشغيل الـ Backend

```bash
cd backend
python -m venv .venv

# تفعيل البيئة
source .venv/bin/activate          # Linux / Mac
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- الخادم: <http://localhost:8000>
- وثائق API التفاعلية (Swagger): <http://localhost:8000/docs>
- وثائق ReDoc: <http://localhost:8000/redoc>

### نقاط النهاية الرئيسية
- `POST /api/auth/register` — إنشاء حساب جديد (٪١٤ يوم تجربة)
- `POST /api/auth/login` — تسجيل دخول
- `POST /api/signals/generate` — توليد إشارة جديدة `{symbol, timeframe, lookback}`
- `GET  /api/signals/latest?limit=20` — أحدث الإشارات
- `GET  /api/analysis/{symbol}?timeframe=H1` — تحليل تفصيلي
- `GET  /api/news/upcoming?hours=48&impact=high` — الأحداث القادمة
- `GET  /api/subscriptions/plans` — الباقات
- `GET  /api/signals/symbols/all` — قائمة الرموز المدعومة

### الرموز المدعومة افتراضياً
XAUUSD · XAGUSD · WTIUSD · EURUSD · GBPUSD · USDJPY · AUDUSD · USDCAD · BTCUSD

## ٢) تشغيل الـ Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

- الواجهة: <http://localhost:3000>
- المسارات: `/` (الهبوط) · `/dashboard` · `/signals` · `/news` · `/subscriptions` · `/login`

## ٣) الاختبار

```bash
cd tests
python test_engines.py
```

النتيجة المتوقعة:
```
✓ market_feed XAUUSD H1 → 150 candles
✓ news_feed → 8 events upcoming
✓ classical_ta, price_action, smart_money, wyckoff, elliott_wave, harmonic
✓ aggregator → BUY/SELL @ price
✅ كل الاختبارات نجحت
```

## ٤) ربط بيانات حقيقية لاحقاً
- استبدل `backend/app/data/market_feed.py:fetch_ohlcv` بمصدر فعلي (Twelve Data / Yahoo / CCXT).
- أضف `TWELVE_DATA_API_KEY` في `.env`.
- استبدل `news_feed.py:upcoming_events` بـ Forex Factory / Investing scraper أو API.

## ٥) الانتقال للإنتاج
- استبدل SQLite بـ PostgreSQL في `DATABASE_URL`.
- شغّل خلف Reverse Proxy (Nginx / Caddy) مع HTTPS.
- شغّل عدة workers: `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000`.
- اضبط CORS_ORIGINS على دومين الواجهة الرسمي.
