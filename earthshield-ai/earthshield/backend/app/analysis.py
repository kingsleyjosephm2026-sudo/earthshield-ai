import json
import numpy as np, pandas as pd
from . import geo, finance, risk, alerts as al
def load(d):
    reg = json.load(open(f"{d}/regions.geojson"))["features"]; fl = json.load(open(f"{d}/floods.geojson"))["features"]
    return reg, pd.read_csv(f"{d}/observations.csv", parse_dates=["date"]), fl, pd.read_csv(f"{d}/crops.csv").set_index("crop")
def assess(d, year=2025, months=(6,7,8,9), as_of="2025-10-31"):
    """Per-region screening assessment. Baseline = same months in 2019..year-1 (needs >=3 baseline years)."""
    reg, obs, fl, crops = load(d); out = []; asof = pd.Timestamp(as_of); n = len(months)
    for f in reg:
        p = f["properties"]; o = obs[obs.region_id == p["region_id"]]
        cur = o[(o.date.dt.year == year) & o.date.dt.month.isin(months)]
        have = set(cur.date.dt.month)   # compare like-with-like months only (avoids seasonal bias when months are missing)
        sel = lambda y: o[(o.date.dt.year == y) & o.date.dt.month.isin(have)]
        cur = sel(year); base = [sel(y) for y in range(2019, year)]; base = [b for b in base if b.ndvi.count() >= max(1, len(have))/2]
        bn = np.array([b.ndvi.mean() for b in base]); br = np.array([b.rainfall_mm.mean() for b in base])
        z = float((cur.ndvi.mean() - bn.mean())/bn.std(ddof=1)) if len(bn) >= 3 and bn.std(ddof=1) > 0 and len(cur) else None
        dpct = float((br.mean() - cur.rainfall_mm.mean())/br.mean()*100) if len(br) >= 3 and len(cur) and br.mean() > 0 else None
        ring = f["geometry"]["coordinates"][0]
        aff, tot = geo.flood_overlap(ring, [x["geometry"]["coordinates"][0] for x in fl]); fpct = aff/tot*100
        aff_ha = fpct/100*p["cultivated_ha"]   # ASSUMPTION: cultivated land uniformly distributed within polygon
        c = crops.loc[p["crop"]]; sc = finance.scenarios(aff_ha, c.yield_t_per_ha, c.price_inr_per_t)
        score, sub, cov = risk.screening_score({"ndvi": z, "rain": dpct, "flood": fpct})
        comp = len(cur.ndvi.dropna())/n; stale = int((asof - o.date.max()).days) if len(o) else None
        out.append({"region_id": p["region_id"], "name": p["name"], "crop": p["crop"], "cultivated_ha": p["cultivated_ha"],
            "period": f"{year}-{months[0]:02d}..{months[-1]:02d}", "as_of": as_of, "ndvi_z": z, "rain_deficit_pct": dpct, "flood_pct": fpct,
            "flood_affected_ha": aff_ha, "flood_source": "SIMULATED scenario 2025-09-12", "gross_value_exposed_inr": sc["central"]["gross_crop_value_inr"],
            "low_loss_inr": sc["low"]["estimated_loss_inr"], "central_loss_inr": sc["central"]["estimated_loss_inr"], "high_loss_inr": sc["high"]["estimated_loss_inr"],
            "score": score, "band": risk.band(score), "factor_scores": sub, "completeness": comp, "days_stale": stale, "baseline_years": len(bn),
            "evidence_strength": risk.evidence(cov, len(bn), comp), "source": "SIMULATED", "label": "screening score, not a probability"})
    out.sort(key=lambda r: -(r["score"] if r["score"] is not None else -1))
    return out, [a for r in out for a in al.generate(r)]
if __name__ == "__main__":
    r, a = assess("data")
    for x in r: print(x["region_id"], x["band"], round(x["score"] or 0,1), "z", x["ndvi_z"] and round(x["ndvi_z"],2), "rain%", x["rain_deficit_pct"] and round(x["rain_deficit_pct"],1), "flood%", round(x["flood_pct"],1), "stale", x["days_stale"])
    print(len(a), "alerts")
