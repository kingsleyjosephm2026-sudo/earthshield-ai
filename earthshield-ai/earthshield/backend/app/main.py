"""FastAPI service. UNVERIFIED in the build sandbox (fastapi could not be installed offline)."""
import io, json, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import pandas as pd
from . import analysis
from .alerts import AlertStore
D = os.environ.get("DATA_DIR", "data")
store = AlertStore(os.path.join(D, "alerts.json"))
app = FastAPI(title="EarthShield AI (prototype, SIMULATED data)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
class StatusUpdate(BaseModel):
    status: str
    notes: str = ""
@app.get("/health")
def health(): return {"status": "ok"}
@app.get("/regions")
def regions(): return json.load(open(f"{D}/regions.geojson"))
@app.get("/floods")
def floods(): return json.load(open(f"{D}/floods.geojson"))
@app.get("/risk")
def risk(year: int = 2025, start_month: int = 6, end_month: int = 9):
    if not (1 <= start_month <= end_month <= 12): raise HTTPException(422, "invalid month range")
    return analysis.assess(D, year, tuple(range(start_month, end_month+1)))[0]
@app.get("/alerts")
def alerts(): return store.sync(analysis.assess(D)[1])
@app.patch("/alerts/{alert_id}")
def update(alert_id: str, body: StatusUpdate):
    store.sync(analysis.assess(D)[1])
    try: return store.update(alert_id, body.status, body.notes)
    except KeyError: raise HTTPException(404, "alert not found")
    except ValueError as e: raise HTTPException(422, str(e))
@app.get("/export/risk.csv")
def export():
    df = pd.DataFrame(analysis.assess(D)[0]).drop(columns=["factor_scores"]); b = io.StringIO(); df.to_csv(b, index=False); b.seek(0)
    return StreamingResponse(b, media_type="text/csv")
