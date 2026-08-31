import csv, hashlib, json, shutil
from pathlib import Path
import joblib, mlflow, yaml
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .features import NUMERIC_FEATURES, CATEGORICAL_FEATURES
from .generate_data import DATASET_VERSION, ROOT
from .validate import validate

PARAMS = yaml.safe_load((ROOT/"params.yaml").read_text(encoding="utf-8"))
def load_rows():
    with (ROOT/"data/processed/trips_clean.csv").open(encoding="utf-8") as f: return list(csv.DictReader(f))
def frame(rows):
    return pd.DataFrame([{key: (float(row[key]) if key in NUMERIC_FEATURES else row[key]) for key in NUMERIC_FEATURES+CATEGORICAL_FEATURES} for row in rows])
def make_preprocessor():
    return ColumnTransformer([("numeric",StandardScaler(),NUMERIC_FEATURES),("categorical",OneHotEncoder(handle_unknown="ignore"),CATEGORICAL_FEATURES)])
def main():
    validation=validate(); rows=load_rows()
    train_rows,test_rows=train_test_split(rows,test_size=PARAMS["test_size"],random_state=PARAMS["seed"])
    x_train,x_test=frame(train_rows),frame(test_rows); y_train=[float(r["trip_duration_minutes"]) for r in train_rows]; y_test=[float(r["trip_duration_minutes"]) for r in test_rows]
    train_signatures={tuple(row[key] for key in NUMERIC_FEATURES+CATEGORICAL_FEATURES) for row in train_rows}
    test_signatures={tuple(row[key] for key in NUMERIC_FEATURES+CATEGORICAL_FEATURES) for row in test_rows}
    duplicate_trip_feature_overlap_count=len(train_signatures & test_signatures)
    mlruns=ROOT/"mlruns"; mlflow.set_tracking_uri(mlruns.resolve().as_uri()); mlflow.set_experiment("delivery-eta")
    specs=[("linear_regression",LinearRegression(),{"fit_intercept":True}),("gradient_boosting",GradientBoostingRegressor(random_state=PARAMS["seed"],n_estimators=100,max_depth=3,learning_rate=.05),{"n_estimators":100,"max_depth":3,"learning_rate":.05})]
    results=[]; fitted={}
    for name,reg,hp in specs:
        pipe=Pipeline([("preprocess",make_preprocessor()),("regressor",reg)]); pipe.fit(x_train,y_train); pred=pipe.predict(x_test)
        result={"model":name,"mae":float(mean_absolute_error(y_test,pred)),"rmse":float(mean_squared_error(y_test,pred)**.5),"r2":float(r2_score(y_test,pred)),"train_size":len(train_rows),"test_size":len(test_rows),"seed":PARAMS["seed"],"hyperparameters":hp,"features":NUMERIC_FEATURES+CATEGORICAL_FEATURES,"dataset_version":DATASET_VERSION}
        with mlflow.start_run(run_name=name) as run:
            mlflow.log_params({"model":name,"seed":PARAMS["seed"],"train_size":len(train_rows),"test_size":len(test_rows),**hp})
            mlflow.log_metrics({"mae":result["mae"],"rmse":result["rmse"],"r2":result["r2"]}); mlflow.set_tags({"dataset_version":DATASET_VERSION,"feature_representation":"scaled numeric + one-hot categorical"})
            run_dir=ROOT/"experiments/artifacts"/run.info.run_id; run_dir.mkdir(parents=True,exist_ok=True); (run_dir/"metrics.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); mlflow.log_artifact(str(run_dir/"metrics.json")); result["mlflow_run_id"]=run.info.run_id
        results.append(result); fitted[name]=pipe
    selected=min(results,key=lambda x:(x["rmse"],-x["r2"])); selected_name=selected["model"]
    artifact={"model":fitted[selected_name],"metadata":{"model_version":"eta-"+selected_name+"-v1","model_name":selected_name,"dataset_version":DATASET_VERSION,"seed":PARAMS["seed"],"features":NUMERIC_FEATURES+CATEGORICAL_FEATURES}}
    (ROOT/"artifacts").mkdir(exist_ok=True); (ROOT/"experiments").mkdir(exist_ok=True); joblib.dump(artifact,ROOT/"artifacts/model.joblib"); shutil.copy2(ROOT/"artifacts/model.joblib",ROOT/"experiments/selected_model.joblib")
    (ROOT/"experiments/runs.jsonl").write_text("\n".join(json.dumps(x) for x in results)+"\n",encoding="utf-8")
    manifest=json.loads((ROOT/"data/manifest.json").read_text(encoding="utf-8")); manifest.update({"processed_sha256":hashlib.sha256((ROOT/"data/processed/trips_clean.csv").read_bytes()).hexdigest(),"train_rows":len(train_rows),"test_rows":len(test_rows)}); (ROOT/"data/manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    report={"validation":validation,"dataset_version":DATASET_VERSION,"train_size":len(train_rows),"test_size":len(test_rows),"duplicate_trip_feature_overlap_count":duplicate_trip_feature_overlap_count,"runs":results,"selected_model":selected_name,"artifact":"artifacts/model.joblib","mlflow_tracking_uri":"mlruns/"}
    (ROOT/"reports").mkdir(exist_ok=True); (ROOT/"reports/training_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    lines=["# ETA model comparison","","| Model | MAE | RMSE | R2 | Features | Decision |","|---|---:|---:|---:|---|---|"]
    for r in results: lines.append(f"| {r['model']} | {r['mae']:.4f} | {r['rmse']:.4f} | {r['r2']:.4f} | numeric + one-hot categorical | {'Selected' if r['model']==selected_name else 'Not selected'} |")
    lines += ["","## Selection","","The model with the lowest held-out RMSE was selected. The preprocessor is fit only on training rows and persisted inside artifacts/model.joblib.","","## Limitations","","The dataset is deterministic synthetic trip data. It demonstrates the engineering lifecycle but is not a substitute for a real fleet telemetry dataset."]
    (ROOT/"reports/model_comparison.md").write_text("\n".join(lines)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
