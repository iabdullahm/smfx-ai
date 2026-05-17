"""NOWPayments client — fiat (Visa/Mastercard) → crypto (USDT) settlement.

Flow:
1. Backend creates an invoice via `create_invoice()` and returns `invoice_url`.
2. Frontend redirects the customer to that URL.
3. Customer pays with card (or crypto) on NOWPayments hosted page.
4. NOWPayments POSTs an IPN to our webhook with payment status.
5. We verify the HMAC-SHA512 signature and update the subscription.

Docs: https://documenter.getpostman.com/view/7907941/S1a32n38
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import httpx


NOWPAYMENTS_API = "https://api.nowpayments.io/v1"


class NOWPaymentsError(Exception):
    pass


def _headers() -> dict[str, str]:
    api_key = os.environ.get("NOWPAYMENTS_API_KEY", "")
    if not api_key:
        raise NOWPaymentsError("NOWPAYMENTS_API_KEY not configured")
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def is_configured() -> bool:
    return bool(os.environ.get("NOWPAYMENTS_API_KEY", "").strip())


def status() -> dict[str, Any]:
    """Health check against NOWPayments API."""
    try:
        r = httpx.get(f"{NOWPAYMENTS_API}/status", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"message": "unreachable", "error": str(e)}


def create_invoice(
    *,
    price_amount: float,
    order_id: str,
    order_description: str,
    success_url: str,
    cancel_url: str,
    ipn_callback_url: str,
    pay_currency: str = "usdttrc20",   # USDT on Tron — cheapest fees
    price_currency: str = "usd",
) -> dict[str, Any]:
    """Create a hosted invoice. Returns dict with `id` and `invoice_url`.

    `pay_currency` controls what you receive (USDT on TRC20 by default).
    `price_currency` is what the customer sees ($USD).
    """
    payload = {
        "price_amount": price_amount,
        "price_currency": price_currency,
        "pay_currency": pay_currency,
        "order_id": order_id,
        "order_description": order_description,
        "ipn_callback_url": ipn_callback_url,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "is_fixed_rate": True,
        "is_fee_paid_by_user": False,
    }
    r = httpx.post(f"{NOWPAYMENTS_API}/invoice", headers=_headers(), json=payload, timeout=20)
    if r.status_code >= 400:
        raise NOWPaymentsError(f"create_invoice failed {r.status_code}: {r.text}")
    return r.json()


def get_payment(payment_id: str) -> dict[str, Any]:
    r = httpx.get(f"{NOWPAYMENTS_API}/payment/{payment_id}", headers=_headers(), timeout=15)
    if r.status_code >= 400:
        raise NOWPaymentsError(f"get_payment failed {r.status_code}: {r.text}")
    return r.json()


def verify_ipn_signature(raw_body: bytes, header_signature: str) -> bool:
    """Validate IPN HMAC-SHA512 over the **sorted** JSON of the body.

    NOWPayments sorts keys alphabetically before signing.

    If NOWPAYMENTS_IPN_SECRET is not configured, signature verification is
    skipped (returns True). This is INSECURE — use only for early testing.
    Set ALLOW_UNVERIFIED_IPN=0 in production to enforce verification.
    """
    secret_raw = os.environ.get("NOWPAYMENTS_IPN_SECRET", "")
    allow_unverified = os.environ.get("ALLOW_UNVERIFIED_IPN", "0").lower() in ("1", "true", "yes")

    if not secret_raw:
        # No secret configured — fall back only if explicitly allowed.
        return allow_unverified

    if not header_signature:
        return False

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return False
    sorted_payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    digest = hmac.new(secret_raw.encode("utf-8"),
                      sorted_payload.encode("utf-8"),
                      hashlib.sha512).hexdigest()
    return hmac.compare_digest(digest, header_signature)


# Payment status flow (from NOWPayments docs):
#   waiting → confirming → confirmed → sending → partially_paid / finished / failed
SUCCESS_STATUSES = {"finished", "partially_paid"}
PENDING_STATUSES = {"waiting", "confirming", "confirmed", "sending"}
FAILED_STATUSES = {"failed", "expired", "refunded"}
