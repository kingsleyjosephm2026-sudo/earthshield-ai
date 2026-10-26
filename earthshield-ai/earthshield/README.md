# EarthShield AI — prototype (vertical slice)

Decision-support prototype for agricultural crop-stress, rainfall-deficit and flood-exposure screening.
**All bundled data is SIMULATED (seed 42). Demo polygons are not official boundaries. Scores are screening indicators, not probabilities. Modeled loss is not verified loss or an insurance payout.**

## Run
```
cd backend
python -m app.generate data                    # regenerate demo data (deterministic)
python -m unittest discover -s tests -t . -v   # 15 tests, stdlib only
python -m app.analysis                         # print risk table
pip install -r requirements.txt && uvicorn app.main:app --reload   # API, docs at /docs
cd ../frontend && npm install && npm run dev   # UI at :5173
```
Or `docker compose up`.

## Implemented and tested (backend/app)
- `ndvi.py` NDVI=(NIR-Red)/(NIR+Red); nodata/NaN/zero-denominator -> NaN; reflectance scale factor.
- `geo.py` ring validation (closure, range, self-intersection, zero area); local-projection area in m²; flood∩region via convex clipping with overlaps counted once (inclusion–exclusion).
- `finance.py` gross = area×yield×price; loss = gross×damage fraction; low/central/high = 10/25/50% (ASSUMED). Returns None on missing inputs.
- `risk.py` weighted screening score (NDVI z 0.4, rain shortfall 0.3, flood 0.3), each normalised to 0–1 (z=-3, 50%, 30% → 1); missing factors are dropped and weights renormalised; evidence label never above "moderate".
- `alerts.py` deterministic rules + JSON-persisted status/notes (Open/Under review/Resolved/Dismissed).
- `analysis.py` baseline = same calendar months in 2019..year-1 (≥3 years required), like-with-like months when the current period has gaps.
## Written but NOT executed here (dependencies unavailable offline)
FastAPI service (`main.py`, syntax-checked only) and React/Leaflet/Recharts UI (not built).
## Not implemented
PostgreSQL/PostGIS, SQLAlchemy/Alembic, GeoPandas/Rasterio ingestion (CSV/GeoJSON/GeoTIFF/Shapefile), raster NDVI maps, SPI, ML model, PDF/GeoJSON reports, live Sentinel-2/NASA adapters, most of the 12 navigation pages, the full 12-document doc set.
## Method notes & limitations
- Area uses an equirectangular local projection (fine for <1° polygons); replace with PyProj equal-area for production.
- Flood polygons must be convex (else rejected). Affected cultivated hectares assume uniform cultivation within the polygon.
- Low NDVI ≠ drought (growth stage, harvest, clouds, soil confound it). Rainfall deficit is a simple % anomaly, not SPI.
- 6 regions × 7 years monthly; baseline of 6 years gives noisy z-scores.
