"""Simulates ground-truth trip outcomes and submits them to /feedback so
predicted-vs-actual accuracy drift can be measured (see pipeline/accuracy_report.py).

Real "actual" durations aren't available in this demo, so this recomputes the
same physics-based duration formula used in pipeline/generate_data.py against
each logged request's features, plus noise. Pass --surge to inject an extra
delay (simulating a festival/rush-hour surge) so accuracy drift can be
demonstrated on demand.
"""
import argparse, json, random
from pathlib import Path

import httpx

from .live_client import JSONL_LOG, ROOT

FEEDBACK_SENT_LOG = ROOT / "logs/feedback_sent.json"
RUSH_HOURS = {7, 8, 9, 16, 17, 18, 19}
TRAFFIC_FACTOR = {"low": 0.0, "medium": 7.0, "high": 16.0}
WEATHER_FACTOR = {"clear": 0.0, "cloudy": 2.0, "rain": 6.0, "snow": 12.0}


def true_duration(payload, rng, surge):
    rush = 1.0 if payload["hour"] in RUSH_HOURS else 0.0
    surge_bonus = rng.uniform(10, 25) if surge else 0.0
    duration = (4.5 + payload["trip_distance_km"] * 2.15 + rush * 7.5
                + TRAFFIC_FACTOR[payload["traffic_level"]] + WEATHER_FACTOR[payload["weather"]]
                + (payload["weekday"] == 5) * 2.0 + surge_bonus + rng.gauss(0, 3.2))
    return round(max(4.0, duration), 2)


def load_already_sent():
    if not FEEDBACK_SENT_LOG.exists():
        return set()
    return set(json.loads(FEEDBACK_SENT_LOG.read_text(encoding="utf-8")))


def main():
    parser = argparse.ArgumentParser(description="Simulate ground-truth outcomes and submit them as /feedback")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--limit", type=int, default=0, help="0 = submit feedback for all unlabelled requests")
    parser.add_argument("--surge", action="store_true", help="simulate a festival/rush-hour surge to demonstrate accuracy drift")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    if not JSONL_LOG.exists():
        print("No client requests logged yet; run `python -m client.live_client` first")
        return

    already_sent = load_already_sent()
    entries = [json.loads(line) for line in JSONL_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidates = [e for e in entries if e.get("outcome") == "ok" and e["response"]["request_id"] not in already_sent]
    if args.limit:
        candidates = candidates[:args.limit]

    sent = 0
    with httpx.Client() as client:
        for entry in candidates:
            request_id = entry["response"]["request_id"]
            actual = true_duration(entry["request"], rng, args.surge)
            resp = client.post(f"{args.base_url}/feedback", json={"request_id": request_id, "actual_eta_minutes": actual}, timeout=5.0)
            if resp.status_code == 200:
                already_sent.add(request_id)
                sent += 1
                print(f"feedback request_id={request_id} predicted={entry['response']['predicted_eta_minutes']} actual={actual} status={resp.status_code}")
            else:
                print(f"feedback FAILED request_id={request_id} status={resp.status_code} body={resp.text}")

    FEEDBACK_SENT_LOG.write_text(json.dumps(sorted(already_sent)), encoding="utf-8")
    print(f"Submitted {sent} feedback record(s){' with surge simulation' if args.surge else ''}. "
          f"{len(candidates) - sent} failed, {len(entries) - len(candidates) - (len(candidates) - sent)} already labelled.")


if __name__ == "__main__":
    main()
