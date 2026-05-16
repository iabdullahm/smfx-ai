"""Subscriptions — read plans + current user subscription."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.subscription import Subscription

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


PLANS = [
    {
        "id": "trial",
        "name": "تجريبي",
        "name_en": "Trial",
        "price_usd": 0,
        "duration_days": 14,
        "features": [
            "إشارات يومية محدودة (3 رموز)",
            "تنبيهات الأخبار",
            "وصول لوحة التحكم الأساسية",
        ],
    },
    {
        "id": "monthly",
        "name": "الاشتراك الشهري",
        "name_en": "Monthly",
        "price_usd": 49,
        "duration_days": 30,
        "features": [
            "إشارات غير محدودة لجميع الرموز",
            "تحليل تفصيلي بكل المدارس الـ8",
            "تنبيهات فورية + WebSocket",
            "أهداف TP1/TP2/TP3",
            "نسبة احتمالية النجاح",
        ],
    },
    {
        "id": "annual",
        "name": "الاشتراك السنوي",
        "name_en": "Annual",
        "price_usd": 490,
        "duration_days": 365,
        "features": [
            "كل ميزات الشهري",
            "شهران مجاناً (خصم ٢ شهر)",
            "أولوية الدعم الفني",
            "تقارير أداء أسبوعية",
        ],
    },
]


@router.get("/plans")
def plans():
    return PLANS


@router.get("/me")
def my_subscription(db: Session = Depends(get_db)):
    sub = db.query(Subscription).order_by(Subscription.id.desc()).first()
    if not sub:
        return {"status": "none", "plan": None}
    expired = sub.expires_at and sub.expires_at < datetime.now(timezone.utc)
    return {
        "plan": sub.plan,
        "status": "expired" if expired else sub.status,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }
