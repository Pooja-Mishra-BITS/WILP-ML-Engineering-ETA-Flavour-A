import hashlib, json, os, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

ROOT=Path(__file__).resolve().parents[1]
MODEL_PATH=Path(os.environ.get("MODEL_PATH",ROOT/"artifacts/model.joblib"))
class TripRequest(BaseModel):
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lon: float = Field(..., ge=-180, le=180)
    dropoff_lat: float = Field(..., ge=-90, le=90)
    dropoff_lon: float = Field(..., ge=-180, le=180)
    trip_distance_km: float = Field(..., gt=0, le=200)
    hour: int = Field(..., ge=0, le=23)
    weekday: int = Field(..., ge=0, le=6)
    weather: str
    traffic_level: str
    @field_validator("weather")
    @classmethod
    def valid_weather(cls,v):
        if v not in {"clear","rain","snow","cloudy"}: raise ValueError("weather must be clear, rain, snow, or cloudy")
        return v
    @field_validator("traffic_level")
    @classmethod
    def valid_traffic(cls,v):
        if v not in {"low","medium","high"}: raise ValueError("traffic_level must be low, medium, or high")
        return v
class TripResponse(BaseModel):
    predicted_eta_minutes: float
    model_version: str
    latency_ms: float
    request_id: str
bundle=joblib.load(MODEL_PATH); model=bundle["model"]; metadata=bundle["metadata"]
app=FastAPI(title="Delivery ETA Predictor",version=metadata["model_version"])
@app.exception_handler(RequestValidationError)
async def validation_handler(request:Request,exc:RequestValidationError):
    return JSONResponse(status_code=422,content={"error":"invalid_request","details":jsonable_encoder(exc.errors())})
@app.get("/health")
def health(): return {"status":"ok","model_version":metadata["model_version"]}
@app.post("/predict",response_model=TripResponse)
def predict(payload:TripRequest):
    request_id=str(uuid.uuid4()); start=time.perf_counter()
    features=pd.DataFrame([payload.model_dump()]); prediction=max(0.0,float(model.predict(features)[0])); latency=round((time.perf_counter()-start)*1000,3)
    entry={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"request_id":request_id,"input_sha256":hashlib.sha256(json.dumps(payload.model_dump(),sort_keys=True).encode()).hexdigest(),"predicted_eta_minutes":round(prediction,2),"model_version":metadata["model_version"],"latency_ms":latency}
    path=ROOT/"logs/predictions.jsonl"; path.parent.mkdir(exist_ok=True)
    with path.open("a",encoding="utf-8") as f: f.write(json.dumps(entry)+"\n")
    return TripResponse(predicted_eta_minutes=round(prediction,2),model_version=metadata["model_version"],latency_ms=latency,request_id=request_id)
if __name__=="__main__":
    import uvicorn; uvicorn.run("api.server:app",host="0.0.0.0",port=int(os.environ.get("PORT","8000")))
