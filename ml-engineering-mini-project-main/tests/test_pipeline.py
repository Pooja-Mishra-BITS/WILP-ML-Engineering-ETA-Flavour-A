import json, subprocess, sys, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api.server import app, bundle
from pipeline.monitor import psi
ROOT=Path(__file__).resolve().parents[1]
VALID={"pickup_lat":40.7,"pickup_lon":-73.9,"dropoff_lat":40.75,"dropoff_lon":-73.8,"trip_distance_km":8.5,"hour":17,"weekday":2,"weather":"rain","traffic_level":"high"}
class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,"-m","pipeline.train"],cwd=ROOT,check=True,capture_output=True)
    def test_validation(self):
        r=json.loads((ROOT/"reports/training_report.json").read_text()); self.assertEqual(r["validation"]["accepted"],600); self.assertEqual(r["validation"]["rejected"],3)
    def test_artifact(self): self.assertIn("model",bundle); self.assertIn("metadata",bundle)
    def test_prediction(self):
        r=TestClient(app).post("/predict",json=VALID); self.assertEqual(r.status_code,200); self.assertIn("predicted_eta_minutes",r.json())
    def test_health(self): self.assertEqual(TestClient(app).get("/health").status_code,200)
    def test_empty_and_malformed(self):
        c=TestClient(app); self.assertEqual(c.post("/predict",json={}).status_code,422); self.assertEqual(c.post("/predict",content=b"{bad",headers={"Content-Type":"application/json"}).status_code,422)
    def test_validation_bounds(self):
        bad=dict(VALID); bad["trip_distance_km"]=-1; self.assertEqual(TestClient(app).post("/predict",json=bad).status_code,422)
    def test_monitoring_metric(self): self.assertGreater(psi([1,2,3],[10,11,12]),.2)
    def test_train_test_separation(self):
        r=json.loads((ROOT/"reports/training_report.json").read_text()); self.assertEqual(r["duplicate_trip_feature_overlap_count"],0)
if __name__=="__main__": unittest.main()
