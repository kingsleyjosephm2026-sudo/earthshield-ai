import json, os, datetime as dt
STATUSES = ("Open", "Under review", "Resolved", "Dismissed")
def generate(a):
    """Deterministic rules over one assessment dict `a`. Returns list of alert dicts."""
    out = []
    def add(t, sev, ev, act): out.append({"id": f"{a['region_id']}:{t}:{a['period']}", "region_id": a["region_id"], "timestamp": a["as_of"],
        "type": t, "severity": sev, "evidence": ev, "source": a["source"], "data_quality": a["evidence_strength"],
        "suggested_investigation": act, "status": "Open", "notes": ""})
    z = a.get("ndvi_z")
    if z is not None and z <= -2: add("ndvi_decline", "high" if z <= -3 else "moderate", f"NDVI z-score {z:.2f} vs baseline", "Check crop stage/harvest/cloud effects, then field-verify")
    d = a.get("rain_deficit_pct")
    if d is not None and d >= 30: add("rainfall_deficit", "high" if d >= 50 else "moderate", f"Rainfall {d:.0f}% below baseline", "Compare with gauge data and irrigation coverage")
    if (a.get("flood_pct") or 0) > 0: add("flood_overlap", "high" if a["flood_pct"] >= 15 else "moderate", f"{a['flood_pct']:.1f}% of area intersects flood extent ({a['flood_source']})", "Verify flood extent with imagery/field reports")
    if (a.get("central_loss_inr") or 0) >= 5_000_000: add("large_modeled_exposure", "high", f"Central modeled loss INR {a['central_loss_inr']:,.0f}", "Review yield/price assumptions")
    if a["completeness"] < 0.9 or (a.get("days_stale") or 0) > 45: add("data_quality", "moderate", f"completeness {a['completeness']:.0%}, last obs {a.get('days_stale')} days old", "Obtain missing observations before relying on score")
    return out
class AlertStore:
    """JSON-file persistence for status changes and notes (demo substitute for the database)."""
    def __init__(self, path): self.path = path
    def load(self):
        return json.load(open(self.path)) if os.path.exists(self.path) else {}
    def sync(self, alerts):
        cur = self.load()
        for a in alerts: cur.setdefault(a["id"], a)
        json.dump(cur, open(self.path, "w"), indent=1); return list(cur.values())
    def update(self, alert_id, status, notes=""):
        if status not in STATUSES: raise ValueError(f"status must be one of {STATUSES}")
        cur = self.load()
        if alert_id not in cur: raise KeyError(alert_id)
        cur[alert_id].update(status=status, notes=notes, updated=dt.datetime.now(dt.timezone.utc).isoformat())
        json.dump(cur, open(self.path, "w"), indent=1); return cur[alert_id]
