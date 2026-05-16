"""Classical technical analysis: RSI, MACD, Bollinger Bands, EMAs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series):
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd = ema12 - ema26
    signal = _ema(macd, 9)
    hist = macd - signal
    return macd, signal, hist


def _bollinger(close: pd.Series, period: int = 20, k: float = 2.0):
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    upper = ma + k * sd
    lower = ma - k * sd
    return ma, upper, lower


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="classical_ta")
    if len(df) < 50:
        out.notes.append("بيانات غير كافية للتحليل الفني الكلاسيكي")
        return out.clamp()

    close = df["close"]
    rsi = _rsi(close).iloc[-1]
    macd, signal, hist = _macd(close)
    macd_v, sig_v, hist_v = macd.iloc[-1], signal.iloc[-1], hist.iloc[-1]
    ma, ub, lb = _bollinger(close)
    last = close.iloc[-1]
    ma_v, ub_v, lb_v = ma.iloc[-1], ub.iloc[-1], lb.iloc[-1]

    ema50 = _ema(close, 50).iloc[-1]
    ema200 = _ema(close, 200).iloc[-1] if len(close) >= 200 else _ema(close, len(close) - 1).iloc[-1]

    score_components = []
    # RSI
    if rsi < 30:
        score_components.append(0.6)
        out.notes.append(f"RSI={rsi:.1f} منطقة تشبع بيع")
    elif rsi > 70:
        score_components.append(-0.6)
        out.notes.append(f"RSI={rsi:.1f} منطقة تشبع شراء")
    else:
        # mild bias by direction
        score_components.append((50 - rsi) / 100)
        out.notes.append(f"RSI={rsi:.1f} متعادل")

    # MACD histogram
    macd_score = np.tanh(hist_v / (abs(close.iloc[-1]) * 0.0005 + 1e-9))
    score_components.append(macd_score)
    out.notes.append(
        f"MACD hist={hist_v:.4f} ({'صعودي' if hist_v > 0 else 'هبوطي'})"
    )

    # EMA trend (50 vs 200)
    if ema50 > ema200:
        score_components.append(0.4)
        out.notes.append("EMA50 > EMA200 (اتجاه صاعد)")
    else:
        score_components.append(-0.4)
        out.notes.append("EMA50 < EMA200 (اتجاه هابط)")

    # Bollinger position
    if last < lb_v:
        score_components.append(0.5)
        out.notes.append("السعر تحت Bollinger السفلي")
    elif last > ub_v:
        score_components.append(-0.5)
        out.notes.append("السعر فوق Bollinger العلوي")

    score = float(np.mean(score_components)) if score_components else 0.0
    out.score = score
    out.confidence = min(1.0, 0.4 + abs(score) * 0.6)
    out.signals.append({
        "indicator": "RSI", "value": round(float(rsi), 2),
    })
    out.signals.append({
        "indicator": "MACD", "macd": round(float(macd_v), 5),
        "signal": round(float(sig_v), 5), "hist": round(float(hist_v), 5),
    })
    out.signals.append({
        "indicator": "Bollinger", "upper": round(float(ub_v), 4),
        "middle": round(float(ma_v), 4), "lower": round(float(lb_v), 4),
    })
    out.signals.append({
        "indicator": "EMA", "ema50": round(float(ema50), 4),
        "ema200": round(float(ema200), 4),
    })
    return out.clamp()
