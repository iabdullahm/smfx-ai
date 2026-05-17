"""Walk-forward backtesting engine.

For each historical bar in a rolling window we:
1. Build a sub-frame of N candles ending at that bar.
2. Ask `aggregate()` for a signal.
3. Track whether the trade hits SL or any of the TPs within `forward_window` bars.
4. Aggregate stats: win rate, profit factor, average R:R, max drawdown.

Signals are only opened when strength ≥ min_strength to model the realistic UX.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from app.ai.aggregator import aggregate
from app.data.market_feed import fetch_ohlcv


@dataclass
class TradeResult:
    side: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    open_idx: int
    close_idx: int
    outcome: str           # tp1 / tp2 / tp3 / sl / timeout
    pnl_r: float           # P/L in multiples of risk
    strength: float
    win_probability: float


@dataclass
class BacktestReport:
    symbol: str
    timeframe: str
    bars: int
    trades: int
    wins: int
    losses: int
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_r: float = 0.0
    expectancy_r: float = 0.0
    max_dd_r: float = 0.0
    largest_win_r: float = 0.0
    largest_loss_r: float = 0.0
    best_streak: int = 0
    worst_streak: int = 0
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    sl_hits: int = 0
    timeouts: int = 0
    trade_log: list[dict[str, Any]] = field(default_factory=list)
    equity_curve_r: list[float] = field(default_factory=list)


def _trade_outcome(df: pd.DataFrame, side: str, entry: float, sl: float,
                   tp1: float, tp2: float, tp3: float,
                   start_idx: int, max_bars: int) -> tuple[str, int, float]:
    """Walk forward bar-by-bar and return (outcome, close_idx, pnl_in_R)."""
    if side == "BUY":
        risk = entry - sl
    else:
        risk = sl - entry
    if risk <= 0:
        return "invalid", start_idx, 0.0

    end = min(start_idx + max_bars, len(df))
    for i in range(start_idx + 1, end):
        bar = df.iloc[i]
        hi, lo = bar["high"], bar["low"]
        if side == "BUY":
            if lo <= sl:
                return "sl", i, -1.0
            if hi >= tp3:
                return "tp3", i, 3.0
            if hi >= tp2:
                return "tp2", i, 2.0
            if hi >= tp1:
                return "tp1", i, 1.0
        else:  # SELL
            if hi >= sl:
                return "sl", i, -1.0
            if lo <= tp3:
                return "tp3", i, 3.0
            if lo <= tp2:
                return "tp2", i, 2.0
            if lo <= tp1:
                return "tp1", i, 1.0
    # No level hit — close at last bar, mark to market
    last = float(df["close"].iloc[end - 1])
    if side == "BUY":
        pnl_r = (last - entry) / max(entry - sl, 1e-9)
    else:
        pnl_r = (entry - last) / max(sl - entry, 1e-9)
    return "timeout", end - 1, float(pnl_r)


def run_backtest(
    symbol: str = "XAUUSD",
    timeframe: str = "H1",
    lookback: int = 1000,
    warmup: int = 200,
    forward_window: int = 30,
    min_strength: float = 6.0,
    step: int = 3,
) -> BacktestReport:
    """Run a walk-forward backtest.

    Parameters
    ----------
    lookback : total candles to evaluate over
    warmup   : candles used as history before the first signal
    forward_window : how many bars after entry to track for TP/SL
    min_strength : only open trades with strength ≥ this value
    step : evaluate every Nth bar (avoids signal redundancy)
    """
    df = fetch_ohlcv(symbol, timeframe, lookback=lookback)
    if len(df) < warmup + 50:
        return BacktestReport(symbol=symbol, timeframe=timeframe,
                              bars=len(df), trades=0, wins=0, losses=0)

    trades: list[TradeResult] = []
    streak = 0; best_streak = 0; worst_streak = 0; last_was_win: bool | None = None
    last_close_idx = -1

    for i in range(warmup, len(df) - forward_window, step):
        if i <= last_close_idx:
            continue   # don't open another trade while one is still open
        window = df.iloc[:i + 1].reset_index(drop=True)
        result = aggregate(window, symbol=symbol)
        if result["strength"] < min_strength:
            continue
        side = result["side"]
        entry = result["entry"]
        sl = result["sl"]
        tp1, tp2, tp3 = result["tp1"], result["tp2"], result["tp3"]

        outcome, close_idx, pnl_r = _trade_outcome(
            df, side, entry, sl, tp1, tp2, tp3,
            start_idx=i, max_bars=forward_window,
        )
        if outcome == "invalid":
            continue
        last_close_idx = close_idx
        trades.append(TradeResult(
            side=side, entry=entry, sl=sl, tp1=tp1, tp2=tp2, tp3=tp3,
            open_idx=i, close_idx=close_idx, outcome=outcome, pnl_r=pnl_r,
            strength=result["strength"], win_probability=result["win_probability"],
        ))

        # Streak tracking
        is_win = pnl_r > 0
        if last_was_win is None:
            streak = 1
        elif is_win == last_was_win:
            streak += 1
        else:
            streak = 1
        last_was_win = is_win
        if is_win:
            best_streak = max(best_streak, streak)
        else:
            worst_streak = max(worst_streak, streak)

    rep = _summarize(trades, symbol, timeframe, len(df))
    return rep


def _summarize(trades: list[TradeResult], symbol: str, tf: str, bars: int) -> BacktestReport:
    rep = BacktestReport(symbol=symbol, timeframe=tf, bars=bars,
                         trades=len(trades), wins=0, losses=0)
    if not trades:
        return rep

    gross_win = 0.0
    gross_loss = 0.0
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        equity += t.pnl_r
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        rep.equity_curve_r.append(round(equity, 3))
        rep.trade_log.append({
            "side": t.side, "entry": t.entry, "sl": t.sl,
            "tp1": t.tp1, "tp2": t.tp2, "tp3": t.tp3,
            "outcome": t.outcome, "pnl_r": round(t.pnl_r, 3),
            "strength": t.strength, "win_probability": t.win_probability,
            "open_idx": t.open_idx, "close_idx": t.close_idx,
        })
        if t.pnl_r > 0:
            rep.wins += 1
            gross_win += t.pnl_r
            rep.largest_win_r = max(rep.largest_win_r, t.pnl_r)
        else:
            rep.losses += 1
            gross_loss += abs(t.pnl_r)
            rep.largest_loss_r = max(rep.largest_loss_r, abs(t.pnl_r))
        if t.outcome == "tp1": rep.tp1_hits += 1
        elif t.outcome == "tp2": rep.tp2_hits += 1
        elif t.outcome == "tp3": rep.tp3_hits += 1
        elif t.outcome == "sl":  rep.sl_hits += 1
        else:                    rep.timeouts += 1

    rep.win_rate = round(rep.wins / max(rep.trades, 1) * 100, 1)
    rep.profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf")
    rep.avg_r = round((gross_win - gross_loss) / max(rep.trades, 1), 3)
    rep.expectancy_r = round((rep.wins / rep.trades) * (gross_win / max(rep.wins, 1)) -
                              (rep.losses / rep.trades) * (gross_loss / max(rep.losses, 1)), 3)
    rep.max_dd_r = round(max_dd, 3)
    return rep


def report_to_dict(rep: BacktestReport, include_log: bool = False) -> dict[str, Any]:
    d = {
        "symbol": rep.symbol, "timeframe": rep.timeframe, "bars": rep.bars,
        "trades": rep.trades, "wins": rep.wins, "losses": rep.losses,
        "win_rate_pct": rep.win_rate, "profit_factor": rep.profit_factor,
        "avg_r": rep.avg_r, "expectancy_r": rep.expectancy_r,
        "max_drawdown_r": rep.max_dd_r,
        "largest_win_r": round(rep.largest_win_r, 3),
        "largest_loss_r": round(rep.largest_loss_r, 3),
        "tp_distribution": {
            "tp1": rep.tp1_hits, "tp2": rep.tp2_hits, "tp3": rep.tp3_hits,
            "sl": rep.sl_hits, "timeout": rep.timeouts,
        },
        "equity_curve_r": rep.equity_curve_r,
    }
    if include_log:
        d["trade_log"] = rep.trade_log
    return d
