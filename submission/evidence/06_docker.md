# Docker evidence

Verified locally on 2026-08-27 after actual execution:

~~~text
docker build -t ml-engineering-mini-project .
docker run --rm -p 8000:8000 ml-engineering-mini-project
~~~

Capture /health and /predict responses from the running container.

Actual verification:

```text
docker build -t ml-engineering-mini-project .     # succeeded
docker run -d --rm --name ml-eta-verify -p 18000:8000 ml-engineering-mini-project
GET /health -> {"status":"ok","model_version":"eta-gradient_boosting-v1"}
POST /predict -> {"predicted_eta_minutes":46.63,"model_version":"eta-gradient_boosting-v1","latency_ms":6.48,"request_id":"e4332faa-fc25-4c5b-a9c2-0f08c261020f"}
docker stop ml-eta-verify
```
