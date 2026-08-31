"""Simulated real-time traffic client for the ETA prediction API.

Sends /predict requests with randomly generated (but realistic) trip data and
logs every request/response pair with a timestamp and the serving model
version. Successful HTTP errors and connection failures ("crashes") are all
captured so the monitoring dashboard can plot system health over time.
"""
import argparse, json, random, time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
TXT_LOG = ROOT / "logs/client_requests.txt"
JSONL_LOG = ROOT / "logs/client_requests.jsonl"
WEATHER = ["clear", "rain", "snow", "cloudy"]
TRAFFIC = ["low", "medium", "high"]
RUSH_HOURS = {7, 8, 9, 16, 17, 18, 19}


def make_payload(rng):
    hour = rng.randrange(24)
    rush = hour in RUSH_HOURS
    traffic = rng.choices(TRAFFIC, weights=[2, 3, 5] if rush else [5, 3, 2])[0]
    weather = rng.choices(WEATHER, weights=[6, 2, 1, 3])[0]
    return {
        "pickup_lat": round(40.60 + rng.random() * .25, 6),
        "pickup_lon": round(-74.05 + rng.random() * .25, 6),
        "dropoff_lat": round(40.60 + rng.random() * .25, 6),
        "dropoff_lon": round(-74.05 + rng.random() * .25, 6),
        "trip_distance_km": round(rng.uniform(1.0, 30.0), 2),
        "hour": hour,
        "weekday": rng.randrange(7),
        "weather": weather,
        "traffic_level": traffic,
    }


def send(client, base_url, payload):
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {"timestamp_utc": timestamp, "request": payload}
    start = time.perf_counter()
    try:
        resp = client.post(f"{base_url}/predict", json=payload, timeout=5.0)
        entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
        entry["status_code"] = resp.status_code
        if resp.status_code == 200:
            body = resp.json()
            entry.update({"response": body, "model_version": body.get("model_version"), "outcome": "ok"})
        else:
            entry.update({"response": resp.text, "model_version": None, "outcome": "http_error"})
    except httpx.RequestError as exc:
        entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
        entry.update({"status_code": None, "response": None, "model_version": None, "outcome": "crash", "error": str(exc)})
    return entry


def log_entry(entry):
    JSONL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    line = (f"[{entry['timestamp_utc']}] status={entry['status_code']} outcome={entry['outcome']} "
            f"model_version={entry['model_version']} latency_ms={entry['latency_ms']} "
            f"request={json.dumps(entry['request'])} response={json.dumps(entry['response'])}\n")
    with TXT_LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def main():
    parser = argparse.ArgumentParser(description="Simulated real-time traffic client for the ETA prediction API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--interval", type=float, default=0.2, help="seconds between requests")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    with httpx.Client() as client:
        for i in range(args.count):
            entry = send(client, args.base_url, make_payload(rng))
            log_entry(entry)
            print(f"{i + 1}/{args.count} outcome={entry['outcome']} status={entry['status_code']} latency_ms={entry['latency_ms']}")
            if i < args.count - 1:
                time.sleep(args.interval)


if __name__ == "__main__":
    main()
