"""Authentication routes."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="email already registered")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="trial",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # 14-day trial
    trial = Subscription(
        user_id=user.id,
        plan="trial",
        status="active",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=14),
    )
    db.add(trial)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, {"role": user.role}))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id, {"role": user.role}))


@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db)):
    """Stub — in real apps decode JWT from header. Kept simple for MVP."""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="no users yet")
    return user
