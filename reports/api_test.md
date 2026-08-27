# Flavor A API test report

Executed with the project-local environment and FastAPI TestClient against `artifacts/model.joblib`.

## GET /health — 200

```json
{"model_version":"eta-gradient_boosting-v1","status":"ok"}
```

## POST /predict valid request — 200

Request:

```json
{"pickup_lat":40.7,"pickup_lon":-73.9,"dropoff_lat":40.75,"dropoff_lon":-73.8,"trip_distance_km":8.5,"hour":17,"weekday":2,"weather":"rain","traffic_level":"high"}
```

Response (request ID and latency are runtime-generated):

```json
{"latency_ms":2.077,"model_version":"eta-gradient_boosting-v1","predicted_eta_minutes":46.63,"request_id":"cded427b-3e3b-4e6f-ad07-07b0634dd073"}
```

## POST /predict empty payload — 422

`{}` returns `{"error":"invalid_request","details":[...]}` with required-field validation details.

## POST /predict malformed JSON — 422

Body `{bad` returns `{"error":"invalid_request","details":[...]}` with a JSON decode error.

## Final live Uvicorn verification

The API was also started with `python -m uvicorn api.server:app --host 127.0.0.1 --port 18001` and tested with curl. Actual statuses were: health **200**, valid prediction **200**, missing field **422**, invalid type **422**, impossible distance **422**, and malformed JSON **422**. The valid live response returned `predicted_eta_minutes: 46.63`, model version `eta-gradient_boosting-v1`, and latency `9.654` ms.
