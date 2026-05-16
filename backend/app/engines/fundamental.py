"""Fundamental bias — macro signal per symbol (heuristic mock for MVP)."""
from __future__ import annotations

from random import Random

import pandas as pd

from app.engines.base import EngineOutput


# Static "macro view" per instrument — represents current bias from a fundamental
# desk. In production these are computed from rate-differentials, COT data,
# inflation prints, etc.
_MACRO_BIAS = {
    "XAUUSD": ("الذهب مدعوم بضعف الدولار والتوقعات بخفض الفائدة", +0.5),
    "XAGUSD": ("الفضة مدفوعة بطلب صناعي + تدفقات الذهب الآمنة", +0.4),
    "WTIUSD": ("النفط ضمن نطاق — تأثيرات OPEC+ والمخزونات الأسبوعية", 0.0),
    "EURUSD": ("اليورو ضعيف نسبياً مقابل صلابة الاقتصاد الأمريكي", -0.3),
    "GBPUSD": ("الإسترليني مدعوم بتأخر BoE في خفض الفائدة", +0.2),
    "USDJPY": ("الين تحت ضغط رغم تدخلات BoJ", +0.3),
    "AUDUSD": ("الدولار الأسترالي مرتبط بأسعار السلع", 0.0),
    "USDCAD": ("الدولار الكندي مرتبط بالنفط وسياسة BoC", 0.0),
}


def analyze(df: pd.DataFrame, symbol: str = "") -> EngineOutput:
    out = EngineOutput(name="fundamental")
    sym = symbol.upper() or "XAUUSD"
    note, bias = _MACRO_BIAS.get(sym, (f"لا توجد رؤية أساسية محددة لـ {sym}", 0.0))
    out.notes.append(note)
    out.score = float(bias)
    out.confidence = 0.55 if bias != 0.0 else 0.25
    out.signals.append({"macro_bias": bias, "symbol": sym})
    return out.clamp()
