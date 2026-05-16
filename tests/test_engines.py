"""Smoke test for analysis engines + aggregator.

Run from the project root:
    cd backend && python -m pytest ../tests -v
Or quickly:
    python tests/test_engines.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone


def build_df(n=200, anchor=2380.0, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0002, 0.005, n)
    prices = anchor * np.exp(np.cumsum(returns))
    opens = prices.copy()
    closes = np.roll(prices, -1); closes[-1] = prices[-1] * 1.0003
    highs = np.maximum(opens, closes) + np.abs(rng.normal(0, anchor * 0.0015, n))
    lows = np.minimum(opens, closes) - np.abs(rng.normal(0, anchor * 0.0015, n))
    times = [datetime.now(timezone.utc) - timedelta(hours=n - i) for i in range(n)]
    return pd.DataFrame({
        "time": times, "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": rng.integers(1000, 5000, n).astype(float),
    })


def test_all_engines():
    from app.engines import classical_ta, price_action, smart_money, wyckoff, elliott_wave, harmonic
    df = build_df()
    for mod, name in [
        (classical_ta, "classical_ta"),
        (price_action, "price_action"),
        (smart_money, "smart_money"),
        (wyckoff, "wyckoff"),
        (elliott_wave, "elliott_wave"),
        (harmonic, "harmonic"),
    ]:
        out = mod.analyze(df)
        assert -1.0 <= out.score <= 1.0, f"{name} score out of range"
        assert 0.0 <= out.confidence <= 1.0, f"{name} confidence out of range"
        print(f"  ✓ {name:14s} score={out.score:+.3f}  conf={out.confidence:.3f}")


def test_aggregator():
    from app.ai.aggregator import aggregate
    df = build_df()
    result = aggregate(df, symbol="XAUUSD")
    assert result["side"] in ("BUY", "SELL")
    assert 1.0 <= result["strength"] <= 10.0
    assert 30.0 <= result["win_probability"] <= 92.0
    assert result["regime"] in ("trending", "ranging", "reversal", "unknown")
    assert len(result["rationale"]) == 8
    print(f"  ✓ aggregator → {result['side']} @ {result['entry']}")
    print(f"               strength={result['strength']}  win_prob={result['win_probability']}%")
    print(f"               regime={result['regime']}  aligned_schools={result['aligned_schools']}/8")


def test_market_feed():
    from app.data.market_feed import fetch_ohlcv, SUPPORTED_SYMBOLS
    assert "XAUUSD" in SUPPORTED_SYMBOLS
    df = fetch_ohlcv("XAUUSD", "H1", 150)
    assert len(df) == 150
    assert set(df.columns) >= {"time", "open", "high", "low", "close", "volume"}
    print(f"  ✓ market_feed XAUUSD H1 → {len(df)} candles, last close={df['close'].iloc[-1]:.2f}")


def test_news_feed():
    from app.data.news_feed import upcoming_events
    items = upcoming_events(hours_ahead=48)
    assert len(items) >= 1
    print(f"  ✓ news_feed → {len(items)} events upcoming")


if __name__ == "__main__":
    print("== Market feed ==");      test_market_feed()
    print("== News feed ==");        test_news_feed()
    print("== Engines ==");          test_all_engines()
    print("== Aggregator ==");       test_aggregator()
    print("\n✅ كل الاختبارات نجحت")
