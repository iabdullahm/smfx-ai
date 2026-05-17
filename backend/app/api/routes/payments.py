"""Payments routes — NOWPayments checkout and webhook."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.payments import nowpayments

router = APIRouter(prefix="/api/payments", tags=["payments"])


PLAN_PRICES_USD = {
    "monthly": 49.0,
    "annual": 490.0,
}
PLAN_DURATION_DAYS = {
    "monthly": 30,
    "annual": 365,
}


class CheckoutRequest(BaseModel):
    plan: str = "monthly"          # monthly / annual
    email: str
    success_url: str | None = None
    cancel_url: str | None = None


@router.get("/status")
def payment_status():
    """Health check for NOWPayments configuration + reachability."""
    return {
        "provider": "nowpayments",
        "configured": nowpayments.is_configured(),
        "api_status": nowpayments.status() if nowpayments.is_configured() else None,
    }


@router.get("/diagnose")
def payment_diagnose():
    """Attempts a minimal invoice creation and returns the raw error if any.

    Use this from a browser to see exactly why checkout is failing.
    """
    if not nowpayments.is_configured():
        return {"ok": False, "stage": "configuration", "error": "NOWPAYMENTS_API_KEY missing"}
    try:
        invoice = nowpayments.create_invoice(
            price_amount=49.0,
            order_id="diagnose-test",
            order_description="Diagnose-only test invoice",
            success_url="https://smfx-ai.vercel.app/payment/success",
            cancel_url="https://smfx-ai.vercel.app/payment/cancel",
            ipn_callback_url="https://smfx-ai-production.up.railway.app/api/payments/webhook",
        )
        return {"ok": True, "invoice_id": invoice.get("id"), "invoice_url": invoice.get("invoice_url")}
    except Exception as e:
        return {"ok": False, "stage": "create_invoice", "error": str(e)}


@router.post("/checkout")
def create_checkout(payload: CheckoutRequest, request: Request, db: Session = Depends(get_db)):
    if payload.plan not in PLAN_PRICES_USD:
        raise HTTPException(status_code=400, detail=f"unknown plan: {payload.plan}")
    if not nowpayments.is_configured():
        raise HTTPException(status_code=503, detail="payment provider not configured")

    # Find or create user (lightweight — full auth comes later)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(email=payload.email, password_hash="", full_name="", role="subscriber")
        db.add(user)
        db.commit()
        db.refresh(user)

    amount = PLAN_PRICES_USD[payload.plan]
    duration = PLAN_DURATION_DAYS[payload.plan]

    # Pending subscription record
    sub = Subscription(
        user_id=user.id,
        plan=payload.plan,
        status="pending",
        amount_usd=amount,
        payment_provider="nowpayments",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=duration),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Build callback URLs based on incoming request
    base = str(request.base_url).rstrip("/")
    frontend = (request.headers.get("origin") or "").rstrip("/")
    success_url = payload.success_url or f"{frontend}/payment/success?sub={sub.id}"
    cancel_url = payload.cancel_url or f"{frontend}/payment/cancel?sub={sub.id}"
    ipn_callback_url = f"{base}/api/payments/webhook"

    try:
        invoice = nowpayments.create_invoice(
            price_amount=amount,
            order_id=f"sub-{sub.id}",
            order_description=f"SMFX-AI {payload.plan} subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            ipn_callback_url=ipn_callback_url,
        )
    except nowpayments.NOWPaymentsError as e:
        sub.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(e))

    # Persist invoice id (NOWPayments calls it `id`)
    sub.payment_id = str(invoice.get("id") or "")
    sub.payment_status = "invoice_created"
    db.commit()

    return {
        "subscription_id": sub.id,
        "invoice_id": invoice.get("id"),
        "invoice_url": invoice.get("invoice_url"),
        "amount": amount,
        "currency": "USD",
        "expires_at": sub.expires_at.isoformat(),
    }


@router.post("/webhook")
async def nowpayments_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives IPN from NOWPayments after a payment status changes."""
    raw_body = await request.body()
    signature = request.headers.get("x-nowpayments-sig", "")

    if not nowpayments.verify_ipn_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    import json
    data = json.loads(raw_body.decode("utf-8"))

    payment_id = str(data.get("payment_id") or data.get("id") or "")
    payment_status = data.get("payment_status", "")
    order_id = data.get("order_id", "")

    # Match by order_id (preferred — it's our sub id) or by payment_id
    sub = None
    if order_id.startswith("sub-"):
        try:
            sub_id = int(order_id.split("-", 1)[1])
            sub = db.get(Subscription, sub_id)
        except ValueError:
            pass
    if not sub and payment_id:
        sub = db.query(Subscription).filter(Subscription.payment_id == payment_id).first()
    if not sub:
        # Acknowledge to prevent retries even when we can't link it
        return {"ok": True, "matched": False}

    sub.payment_status = payment_status
    if payment_status in nowpayments.SUCCESS_STATUSES:
        sub.status = "active"
    elif payment_status in nowpayments.FAILED_STATUSES:
        sub.status = "cancelled"
    elif payment_status in nowpayments.PENDING_STATUSES:
        sub.status = "pending"

    db.commit()
    return {"ok": True, "subscription_id": sub.id, "status": sub.status}


@router.get("/subscription/{sub_id}")
def get_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.get(Subscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="subscription not found")
    return {
        "id": sub.id,
        "plan": sub.plan,
        "status": sub.status,
        "amount_usd": sub.amount_usd,
        "payment_provider": sub.payment_provider,
        "payment_status": sub.payment_status,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }
