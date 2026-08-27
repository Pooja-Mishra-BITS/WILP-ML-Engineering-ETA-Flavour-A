import csv, json, math, random
from collections import Counter
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from .generate_data import ROOT, SEED

def psi(base, current, bins=10):
    lo=min(base+current); hi=max(base+current); width=(hi-lo)/bins if hi>lo else 1
    def counts(values):
        c=[0]*bins
        for value in values: c[min(bins-1,int((value-lo)/width))]+=1
        return c
    p,q=counts(base),counts(current); pt=sum(p) or 1; qt=sum(q) or 1
    return sum((max(q[i]/qt,.0001)-max(p[i]/pt,.0001))*math.log(max(q[i]/qt,.0001)/max(p[i]/pt,.0001)) for i in range(bins))

def make_drift():
    rng=random.Random(SEED); rows=[]
    for i in range(120):
        distance=round(rng.uniform(3,45),2); hour=rng.choice([7,8,9,16,17,18,19,20]); weekday=rng.randrange(7)
        weather=rng.choice(["rain","snow","cloudy","clear"]); traffic=rng.choice(["medium","high","high"])
        base=4.5+distance*2.15+(7.5 if hour in {7,8,9,16,17,18,19} else 0)+({"medium":7,"high":16}[traffic])+({"clear":0,"cloudy":2,"rain":6,"snow":12}[weather])
        duration=round(max(4,base+10+rng.gauss(0,3.2)),2)
        rows.append({"trip_id":f"D{i+1:05d}","pickup_lat":40.6+rng.random()*.25,"pickup_lon":-74.05+rng.random()*.25,"dropoff_lat":40.6+rng.random()*.25,"dropoff_lon":-74.05+rng.random()*.25,"trip_distance_km":distance,"hour":hour,"weekday":weekday,"weather":weather,"traffic_level":traffic,"trip_duration_minutes":duration})
    path=ROOT/"data/simulated/drift_trips.csv"; path.parent.mkdir(exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return rows

def main():
    with (ROOT/"data/processed/trips_clean.csv").open(encoding="utf-8") as f: rows=list(csv.DictReader(f))
    rng=random.Random(SEED); rng.shuffle(rows); baseline=rows[:480]; drift=make_drift(); bundle=joblib.load(ROOT/"artifacts/model.joblib")
    prediction=bundle["model"].predict(pd.DataFrame(drift)); actual=[float(row["trip_duration_minutes"]) for row in drift]
    base_dist=[float(row["trip_distance_km"]) for row in baseline]; drift_dist=[float(row["trip_distance_km"]) for row in drift]; score=psi(base_dist,drift_dist)
    feedback_path=ROOT/"logs/feedback.jsonl"; feedback=[json.loads(x) for x in feedback_path.read_text(encoding="utf-8").splitlines() if x.strip()] if feedback_path.exists() else []
    report={"baseline_size":len(baseline),"drift_size":len(drift),"drift_methodology":"120 trips with longer distances, rush-hour traffic, adverse weather, and an additional delay component representing festival/seasonal congestion.","metric":"PSI on trip_distance_km plus simulated RMSE/MAE","psi":round(score,6),"drift_mae":round(float(mean_absolute_error(actual,prediction)),4),"drift_rmse":round(float(mean_squared_error(actual,prediction)**.5),4),"psi_threshold":.2,"rmse_threshold":8.0,"production_feedback_rows":len(feedback),"retraining_triggered":bool(score>=.2 or mean_squared_error(actual,prediction)**.5>8),"action":"queue retraining with latest labelled trips" if (score>=.2 or mean_squared_error(actual,prediction)**.5>8) else "continue monitoring","workflow":["monitor","detect","trigger","train","validate","promote"],"limitations":"PSI is sensitive to binning and sample size; simulated drift is not a substitute for live labelled feedback."}
    (ROOT/"reports/monitoring_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); (ROOT/"reports/monitoring_report.md").write_text("# ETA monitoring and drift report\n\n"+json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
