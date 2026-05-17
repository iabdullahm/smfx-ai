# دليل إعداد المدفوعات — NOWPayments

كيفية تفعيل قبول مدفوعات Visa/Mastercard والحصول على USDT في محفظتك على Binance.

---

## ١) إنشاء حساب NOWPayments

1. اذهب لـ <https://nowpayments.io>
2. اضغط **Get Started** → سجّل بريداً إلكترونياً وكلمة مرور
3. أكّد البريد الإلكتروني
4. سجّل دخول للوحة التحكم

## ٢) ضبط محفظة الاستلام (USDT على Binance)

1. اذهب لـ Binance → **محفظة → سحب → USDT**
2. اختر شبكة **TRC20** (الأرخص في الرسوم — أقل من $1 لكل تحويل)
3. انسخ عنوان محفظتك (Address)
4. عُد لـ NOWPayments → **Payments Settings** → **Outcome Wallet**
5. الصق العنوان واختر العملة `USDTTRC20`
6. احفظ

> 💡 يمكنك إضافة عناوين متعددة (BEP20, ERC20) للحصول على مرونة، لكن TRC20 أرخص.

## ٣) تفعيل الدفع بالفيزا

1. لوحة NOWPayments → **Settings** → **Fiat Currencies**
2. فعّل **"Accept Fiat Payments"**
3. اختر العملات المقبولة (USD, EUR على الأقل)
4. وافق على شروط مزوّدي البطاقات (Simplex / MoonPay)

> ⚠️ قد يطلب منك NOWPayments **KYC للأعمال** (هوية + إثبات عنوان شركة) قبل تفعيل
> الدفع بالفيزا. هذا متطلب قانوني عالمي، عادةً يستغرق ١-٣ أيام عمل.

## ٤) الحصول على API Key + IPN Secret

### API Key
1. **Profile → Store Settings → API Keys**
2. اضغط **+ Add New Key**
3. الاسم: `SMFX-AI Production`
4. الصلاحيات: `Payments: Read+Write`, `Invoices: Read+Write`
5. انسخ المفتاح فوراً — لن يظهر مرة أخرى

### IPN Secret
1. نفس الصفحة → **IPN Settings**
2. **IPN Callback URL** = `https://smfx-ai-production.up.railway.app/api/payments/webhook`
3. اضغط **Generate IPN Secret** → انسخه

## ٥) إضافة المتغيرات في Railway

1. <https://railway.app/dashboard> → مشروع smfx-ai → خدمة smfx-ai → **Variables**
2. أضف:

| Name | Value |
|------|-------|
| `NOWPAYMENTS_API_KEY` | (المفتاح من خطوة ٤) |
| `NOWPAYMENTS_IPN_SECRET` | (IPN Secret من خطوة ٤) |

Railway سيعيد النشر تلقائياً.

## ٦) الاختبار

### في وضع Sandbox أولاً (موصى به)
NOWPayments يوفر بيئة اختبار:
1. <https://account-sandbox.nowpayments.io>
2. أنشئ مفتاح Sandbox
3. غيّر `NOWPAYMENTS_API_KEY` مؤقتاً للمفتاح التجريبي
4. الكود سيستخدم نفس endpoints (نضيف متغير `NOWPAYMENTS_SANDBOX=1` للتبديل)

### تدفّق الاختبار
1. افتح <https://smfx-ai.vercel.app/subscriptions>
2. اضغط **اشترك الآن** على الباقة الشهرية
3. أدخل بريداً إلكترونياً
4. اضغط **ادفع $49 بـ Visa / Crypto**
5. ستُحوّل لصفحة NOWPayments
6. اختر **Pay with Card** أو **Pay with Crypto**
7. أكمل الدفع
8. ستعود إلى `https://smfx-ai.vercel.app/payment/success`
9. الصفحة ستنتظر تأكيد IPN وتُفعّل الاشتراك

### التحقق من وصول USDT
- Binance → **سجل المعاملات** → **إيداع**
- يجب أن ترى الإيداع بـ USDT خلال ١٠-٣٠ دقيقة بعد تأكيد الدفع

---

## ٧) الرسوم والأرباح

### مثال على باقة $49

```
السعر للمشترك:            $49.00
رسوم NOWPayments (0.5%):  -$0.25
رسوم مزوّد الفيزا (~3%):    -$1.47
─────────────────────────────────
تستلمه USDT:               ~$47.28
```

### مقارنة بـ Stripe

```
Stripe:        $49 × (1 - 0.029) - $0.30 = $47.27 + 2-3 أيام انتظار
NOWPayments:   $47.28 → USDT مباشرة على Binance خلال ١٠ دقائق
```

---

## ٨) الأمان

- **لا تشارك** `NOWPAYMENTS_API_KEY` أو `NOWPAYMENTS_IPN_SECRET` مع أحد
- **لا تكتبهما في الكود** — فقط في متغيرات Railway
- الـ webhook يتحقق من التوقيع HMAC-SHA512 — لا يمكن لأحد تزييف الدفعات
- اختر **2FA** على حساب NOWPayments

## ٩) الإلغاء والاسترجاع

- المدفوعات بالكريبتو **غير قابلة للاسترجاع** بطبيعتها
- إذا قرّرت رد المال يدوياً، أرسل USDT للعميل من Binance
- لا توجد آلية تلقائية للاسترجاع (هذا اختلاف رئيسي عن Stripe)

## ١٠) الدعم
- وثائق NOWPayments: <https://documenter.getpostman.com/view/7907941/S1a32n38>
- دعم: support@nowpayments.io (وقت الرد ~٢٤ ساعة)
