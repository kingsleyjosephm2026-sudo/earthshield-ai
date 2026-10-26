import unittest, tempfile, os
import numpy as np
from app import geo, ndvi as nd, finance, risk, alerts, generate, analysis
SQ = generate.box
class T(unittest.TestCase):
    def test_ndvi(self): self.assertAlmostEqual(float(nd.ndvi(0.5, 0.1)), 0.6667, 3)
    def test_ndvi_zero_den(self): self.assertTrue(np.isnan(nd.ndvi(0.0, 0.0)))
    def test_ndvi_nodata(self):
        r = nd.ndvi(np.array([-9999, 5000]), np.array([100, 1000]), nodata=-9999, scale=10000)
        self.assertTrue(np.isnan(r[0])); self.assertAlmostEqual(r[1], 0.6667, 3)
    def test_ndvi_nan(self): self.assertTrue(np.isnan(nd.ndvi(np.nan, 0.2)))
    def test_area_known(self): self.assertAlmostEqual(geo.area_m2(SQ(80, 0, .1, .1))/1e6, 123.64, delta=0.5)
    def test_area_shrinks_with_latitude(self): self.assertLess(geo.area_m2(SQ(80, 60, .1, .1)), 0.55*geo.area_m2(SQ(80, 0, .1, .1)))
    def test_invalid_polygons(self):
        self.assertTrue(geo.validate_ring([[0,0],[1,0],[0,0]]))
        self.assertTrue(geo.validate_ring([[0,0],[1,1],[1,0],[0,1],[0,0]]))
        self.assertTrue(geo.validate_ring([[0,0],[200,0],[200,5],[0,5],[0,0]]))
        self.assertEqual(geo.validate_ring(SQ(80,16,.3,.25)), [])
    def test_flood_partial(self):
        a, t = geo.flood_overlap(SQ(80,16,.2,.2), [SQ(80.1,15.9,.3,.3)]); self.assertAlmostEqual(a/t, .5, 2)
    def test_flood_overlap_not_double_counted(self):
        a, t = geo.flood_overlap(SQ(80,16,.2,.2), [SQ(80.0,16,.1,.2), SQ(80.05,16,.1,.2)]); self.assertAlmostEqual(a/t, .75, 2)  # union 0.15/0.2, overlap counted once
    def test_flood_none_and_nonconvex(self):
        self.assertEqual(geo.flood_overlap(SQ(80,16,.2,.2), [SQ(85,10,.1,.1)])[0], 0)
        self.assertEqual(geo.flood_overlap(SQ(80,16,.2,.2), [])[0], 0)
        with self.assertRaises(ValueError): geo.flood_overlap(SQ(80,16,.2,.2), [[[80,16],[80.1,16.1],[80.2,16],[80.2,16.2],[80,16.2],[80,16]]])
    def test_finance(self):
        self.assertEqual(finance.exposure(10, 3, 100, .5), {"gross_crop_value_inr": 3000, "estimated_loss_inr": 1500})
        self.assertIsNone(finance.exposure(10, None, 100, .5)); self.assertIsNone(finance.exposure(10, 3, float("nan"), .5))
        self.assertIsNone(finance.exposure(10, 3, 100, 1.5)); self.assertEqual(finance.exposure(0, 3, 100, .5)["estimated_loss_inr"], 0)
    def test_risk_norm(self):
        self.assertEqual(risk.normalize("ndvi", -6), 1.0); self.assertEqual(risk.normalize("rain", -20), 0.0); self.assertIsNone(risk.normalize("flood", float("nan")))
    def test_risk_missing_reweights(self):
        s, _, cov = risk.screening_score({"ndvi": -3, "rain": None, "flood": None}); self.assertEqual(s, 100); self.assertAlmostEqual(cov, .4)
        self.assertIsNone(risk.screening_score({})[0]); self.assertEqual(risk.band(None), "no data")
    def test_alert_store(self):
        with tempfile.TemporaryDirectory() as d:
            s = alerts.AlertStore(d+"/a.json"); s.sync([{"id": "x"}]); self.assertEqual(s.update("x", "Resolved", "ok")["status"], "Resolved")
            self.assertEqual(s.load()["x"]["notes"], "ok")
            with self.assertRaises(ValueError): s.update("x", "bogus")
            with self.assertRaises(KeyError): s.update("nope", "Open")
    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e:
            generate.main(d); generate.main(e)
            self.assertTrue(all(open(f"{d}/{f}").read() == open(f"{e}/{f}").read() for f in os.listdir(d)))
            r, a = analysis.assess(d); by = {x["region_id"]: x for x in r}
            self.assertEqual(r[0]["region_id"], "Z03")
            self.assertLess(by["Z03"]["ndvi_z"], -2); self.assertGreater(by["Z03"]["rain_deficit_pct"], 30)
            self.assertGreater(by["Z02"]["flood_pct"], 0); self.assertEqual(by["Z01"]["flood_pct"], 0)
            self.assertEqual(by["Z06"]["evidence_strength"], "low"); self.assertGreater(by["Z05"]["ndvi_z"], -2)  # missing month must not fake an NDVI anomaly
            types = {(x["region_id"], x["type"]) for x in a}
            self.assertIn(("Z03","ndvi_decline"), types); self.assertIn(("Z02","flood_overlap"), types); self.assertIn(("Z06","data_quality"), types)
            self.assertNotIn(("Z01","ndvi_decline"), types)
if __name__ == "__main__": unittest.main()
