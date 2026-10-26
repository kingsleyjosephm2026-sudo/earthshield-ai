"""Screening score 0-100 (NOT a probability of crop failure)."""
import math
WEIGHTS = {"ndvi": 0.4, "rain": 0.3, "flood": 0.3}
def _c(x): return float(min(1.0, max(0.0, x)))
def normalize(name, v):
    """ndvi: z-score vs baseline (z=-3 -> 1). rain: shortfall % vs baseline (50% -> 1; surplus -> 0). flood: % area flooded (30% -> 1)."""
    if v is None or not math.isfinite(v): return None
    return {"ndvi": lambda: _c(-v/3.0), "rain": lambda: _c(v/50.0), "flood": lambda: _c(v/30.0)}[name]()
def screening_score(factors, weights=WEIGHTS):
    sub = {k: normalize(k, factors.get(k)) for k in weights}
    avail = {k: s for k, s in sub.items() if s is not None}
    if not avail: return None, sub, 0.0
    ws = sum(weights[k] for k in avail)
    return 100*sum(weights[k]*s for k, s in avail.items())/ws, sub, ws/sum(weights.values())
def band(score):
    return "no data" if score is None else "low" if score < 25 else "moderate" if score < 50 else "high" if score < 75 else "critical"
def evidence(coverage, baseline_years, completeness):
    if coverage < 0.7 or baseline_years < 3 or completeness < 0.9: return "low"
    return "moderate"  # never 'high': demo data is synthetic and unvalidated
