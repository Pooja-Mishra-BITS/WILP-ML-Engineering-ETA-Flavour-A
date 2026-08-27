import csv, hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "trips.csv"
SEED = 412
DATASET_VERSION = "dataset-a-v1.0.0"
WEATHER = ["clear", "rain", "snow", "cloudy"]
TRAFFIC = ["low", "medium", "high"]

def main():
    rng = random.Random(SEED)
    rows = []
    for i in range(600):
        hour = rng.randrange(24)
        weekday = rng.randrange(7)
        distance = round(rng.uniform(1.0, 28.0), 2)
        weather = rng.choice(WEATHER)
        traffic = rng.choice(TRAFFIC)
        pickup_lat = round(40.60 + rng.random() * .25, 6)
        pickup_lon = round(-74.05 + rng.random() * .25, 6)
        dropoff_lat = round(40.60 + rng.random() * .25, 6)
        dropoff_lon = round(-74.05 + rng.random() * .25, 6)
        rush = 1.0 if hour in {7,8,9,16,17,18,19} else 0.0
        traffic_factor = {"low": 0.0, "medium": 7.0, "high": 16.0}[traffic]
        weather_factor = {"clear": 0.0, "cloudy": 2.0, "rain": 6.0, "snow": 12.0}[weather]
        duration = max(4.0, 4.5 + distance * 2.15 + rush * 7.5 + traffic_factor + weather_factor + (weekday == 5) * 2.0 + rng.gauss(0, 3.2))
        rows.append({
            "trip_id": f"TRIP{i+1:05d}", "pickup_lat": pickup_lat, "pickup_lon": pickup_lon,
            "dropoff_lat": dropoff_lat, "dropoff_lon": dropoff_lon, "trip_distance_km": distance,
            "hour": hour, "weekday": weekday, "weather": weather, "traffic_level": traffic,
            "trip_duration_minutes": round(duration, 2), "created_at": f"2026-08-{i%28+1:02d}T{hour:02d}:15:00Z",
        })
    rows += [
        {"trip_id":"BAD001","pickup_lat":"","pickup_lon":-73.9,"dropoff_lat":40.7,"dropoff_lon":-73.8,"trip_distance_km":5,"hour":8,"weekday":1,"weather":"clear","traffic_level":"low","trip_duration_minutes":20,"created_at":"2026-08-01T08:00:00Z"},
        {"trip_id":"BAD002","pickup_lat":40.7,"pickup_lon":-73.9,"dropoff_lat":40.7,"dropoff_lon":-73.8,"trip_distance_km":-2,"hour":8,"weekday":1,"weather":"clear","traffic_level":"low","trip_duration_minutes":20,"created_at":"2026-08-01T08:00:00Z"},
        {"trip_id":"BAD003","pickup_lat":40.7,"pickup_lon":-73.9,"dropoff_lat":40.7,"dropoff_lon":-73.8,"trip_distance_km":5,"hour":8,"weekday":1,"weather":"clear","traffic_level":"low","trip_duration_minutes":20,"created_at":"bad-date"},
    ]
    rng.shuffle(rows); RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = ["trip_id","pickup_lat","pickup_lon","dropoff_lat","dropoff_lon","trip_distance_km","hour","weekday","weather","traffic_level","trip_duration_minutes","created_at"]
    with RAW_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    manifest = {"dataset_version": DATASET_VERSION, "seed": SEED, "raw_rows": len(rows), "valid_rows": 600, "class_balance": "not applicable for regression", "sha256": hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()}
    (ROOT/"data"/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    (ROOT/"data"/"VERSION").write_text(DATASET_VERSION+"\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
if __name__ == "__main__": main()
