import csv, json
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["trip_id","pickup_lat","pickup_lon","dropoff_lat","dropoff_lon","trip_distance_km","hour","weekday","weather","traffic_level","trip_duration_minutes","created_at"]
WEATHER = {"clear","rain","snow","cloudy"}; TRAFFIC = {"low","medium","high"}
NUMERIC = ["pickup_lat","pickup_lon","dropoff_lat","dropoff_lon","trip_distance_km","hour","weekday","trip_duration_minutes"]
def validate():
    accepted=[]; rejected=[]; raw=ROOT/"data/raw/trips.csv"; clean=ROOT/"data/processed/trips_clean.csv"; bad=ROOT/"data/processed/rejected_rows.jsonl"; clean.parent.mkdir(parents=True,exist_ok=True)
    with raw.open(encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames != FIELDS: raise ValueError("schema mismatch")
        for row in reader:
            errors=[]
            parsed={}
            for field in NUMERIC:
                try: parsed[field]=float(row[field])
                except (TypeError, ValueError): errors.append("invalid_"+field)
            if not row["trip_id"].strip(): errors.append("missing_trip_id")
            if not row["weather"] in WEATHER: errors.append("invalid_weather")
            if not row["traffic_level"] in TRAFFIC: errors.append("invalid_traffic_level")
            try: datetime.fromisoformat(row["created_at"].replace("Z","+00:00"))
            except ValueError: errors.append("invalid_timestamp")
            if all(field in parsed for field in ["pickup_lat","pickup_lon","dropoff_lat","dropoff_lon"]):
                if not (-90 <= parsed["pickup_lat"] <= 90 and -180 <= parsed["pickup_lon"] <= 180 and -90 <= parsed["dropoff_lat"] <= 90 and -180 <= parsed["dropoff_lon"] <= 180): errors.append("invalid_coordinates")
            if "trip_distance_km" in parsed and not (0 < parsed["trip_distance_km"] <= 200): errors.append("invalid_distance")
            if all(field in parsed for field in ["hour","weekday"]):
                if not (0 <= int(parsed["hour"]) <= 23 and 0 <= int(parsed["weekday"]) <= 6): errors.append("invalid_time")
            if "trip_duration_minutes" in parsed and parsed["trip_duration_minutes"] <= 0: errors.append("invalid_duration")
            if errors: rejected.append({"row":row,"errors":errors})
            else: accepted.append(row)
    with clean.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(accepted)
    with bad.open("w",encoding="utf-8") as f:
        for row in rejected: f.write(json.dumps(row)+"\n")
    return {"accepted":len(accepted),"rejected":len(rejected),"reject_reasons":[r["errors"] for r in rejected]}
if __name__=="__main__": print(json.dumps(validate(),indent=2))
