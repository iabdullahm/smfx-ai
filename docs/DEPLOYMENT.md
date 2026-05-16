# دليل النشر — SMFX-AI

نشر النظام على رابط عام مجاناً تقريباً:
- **Backend (FastAPI)** → Railway
- **Frontend (Next.js)** → Vercel
- **Source control** → GitHub

---

## ١) رفع المشروع على GitHub

افتح PowerShell في مجلد المشروع:

```powershell
cd "C:\Muasher Pro"
git init
git add .
git commit -m "Initial commit: SMFX-AI v1.0 MVP"
```

أنشئ مستودع جديد على <https://github.com/new>:
- Name: `smfx-ai`
- Visibility: **Private** (موصى به — كود مالي)
- لا تختر README/gitignore (موجودان)

ثم اربط واُدفع:

```powershell
git remote add origin https://github.com/<your-username>/smfx-ai.git
git branch -M main
git push -u origin main
```

> إذا طلب منك تسجيل دخول، استخدم **Personal Access Token** من
> <https://github.com/settings/tokens> (Tokens > classic > Generate new token > scope: `repo`)

---

## ٢) نشر Backend على Railway

### أ) إنشاء المشروع
1. اذهب لـ <https://railway.app> وسجّل دخول بـ GitHub
2. **New Project** → **Deploy from GitHub repo** → اختر `smfx-ai`
3. Railway تكتشف Python تلقائياً

### ب) ضبط Root Directory
في تبويب **Settings** للخدمة:
- **Root Directory** = `backend`
- **Watch Paths** = `backend/**` (يعيد النشر فقط عند تغيير backend)

### ج) إضافة PostgreSQL
1. داخل المشروع: **+ New** → **Database** → **PostgreSQL**
2. Railway تنشئها وتربطها تلقائياً عبر متغير `DATABASE_URL`

### د) متغيرات البيئة
في تبويب **Variables** للخدمة، أضف:

| المتغير | القيمة |
|---------|--------|
| `APP_ENV` | `production` |
| `JWT_SECRET` | مفتاح عشوائي ٦٤ حرف ([مولّد](https://generate-secret.vercel.app/64)) |
| `CORS_ORIGINS` | `https://smfx-ai.vercel.app` (نحدّثه بعد Vercel) |
| `SIGNAL_STRENGTH_THRESHOLD` | `6.0` |

> `DATABASE_URL` و `PORT` تُضافان تلقائياً، لا تلمسهما.

### هـ) الحصول على رابط الخدمة
**Settings** → **Networking** → **Generate Domain**
ستحصل على: `https://smfx-api-production.up.railway.app`

اختبر: `https://<your-url>/health` → `{"status":"ok"}`
وSwagger: `https://<your-url>/docs`

---

## ٣) نشر Frontend على Vercel

### أ) إنشاء المشروع
1. اذهب لـ <https://vercel.com> وسجّل دخول بـ GitHub
2. **Add New** → **Project** → اختر `smfx-ai`
3. **Root Directory** = `frontend`
4. Framework يُكتشف تلقائياً (Next.js)

### ب) متغير البيئة
أضف في **Environment Variables**:

| المتغير | القيمة |
|---------|--------|
| `NEXT_PUBLIC_API_BASE` | `https://smfx-api-production.up.railway.app` |

### ج) Deploy
اضغط **Deploy** — ينتهي خلال دقيقتين.
ستحصل على: **<https://smfx-ai.vercel.app>**

### د) تحديث CORS في Railway
عُد لـ Railway → Variables، وحدّث:
- `CORS_ORIGINS` = `https://smfx-ai.vercel.app`

ثم **Deployments** → **Redeploy**.

---

## ٤) تحقق نهائي

| الرابط | النتيجة المتوقعة |
|--------|------------------|
| `https://smfx-api-production.up.railway.app/health` | `{"status":"ok"}` |
| `https://smfx-api-production.up.railway.app/docs` | Swagger UI |
| `https://smfx-ai.vercel.app` | صفحة الهبوط |
| `https://smfx-ai.vercel.app/dashboard` | لوحة التحكم + توليد إشارات |

---

## ٥) النشر التلقائي

كل `git push origin main` يُطلق:
- إعادة نشر Backend على Railway
- إعادة نشر Frontend على Vercel

Preview deployments من branches أخرى تنشأ تلقائياً على Vercel.

---

## ٦) التكاليف

| الخدمة | التكلفة |
|--------|---------|
| GitHub Private | مجاناً |
| Vercel Hobby | مجاناً |
| Railway | $5 رصيد مجاني + ~$5/شهر لاحقاً |
| **المجموع** | **~$5/شهر** |

---

## ٧) استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| CORS error | حدّث `CORS_ORIGINS` بدومين Vercel الفعلي |
| Railway build فشل (Nixpacks) | استخدم Dockerfile (موجود في `backend/Dockerfile`) |
| Vercel build فشل | تحقق Root Directory = `frontend` |
| 502 على Railway | راجع Logs، عادةً JWT_SECRET أو Database connection |
| Database connection refused | تأكد أن PostgreSQL service مرتبطة بالـ web service |

---

## ٨) خطوات الأمان قبل الإطلاق العام

- [ ] `JWT_SECRET` قوي وعشوائي (٦٤+ حرف)
- [ ] HTTPS فقط (افتراضي على Vercel/Railway)
- [ ] Rate limiting على `/api/auth/*` و `/api/signals/generate`
- [ ] Sentry لمراقبة الأخطاء
- [ ] استبدال البيانات الاصطناعية ببيانات سوق حقيقية
- [ ] تكامل Stripe للمدفوعات
