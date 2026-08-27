# Experiment tracking evidence

Capture the local MLflow UI showing two completed runs, or the output of:

~~~text
mlflow ui --backend-store-uri ./mlruns --host 127.0.0.1 --port 5000
~~~

Also capture `experiments/runs.jsonl` and the two MLflow run IDs from `reports/training_report.json`. The experiments are linear regression and gradient boosting regression.
