import time
import uuid
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from diabetes import db
from diabetes.config import settings


class Features(BaseModel):
    model_config = {"extra": "forbid"}

    gender: str
    age: int = Field(ge=0)
    hypertension: int
    heart_disease: int = Field(ge=0, le=300)
    smoking_history: str
    bmi: float
    HbA1c_level: float = Field(ge=0.0)
    blood_glucose_level: int


class Prediction(BaseModel):
    #model_config = {"protected_namespaces": ()}

    score: float
    diabetes: bool
    model_version: str
    request_id: str
    latency_ms: float

# загрузка модели один раз и её метаданных из артефакта (до yield запускается при старте сервиса, после yield при остановке сервиса)
@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load(settings.model_path)
    app.state.pipeline = bundle["pipeline"]
    app.state.meta = bundle["metadata"]
    app.state.version = bundle["metadata"]["model_version"]

    db.init()
    yield
    app.state.pipeline = None


app = FastAPI(title="diabetes-service", version="1.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "model_version": getattr(app.state, "version", "unknown"), 
        "config": {
            "log_level": settings.log_level,
            "model_path": settings.model_path
            }
        }

@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}

@app.post("/v1/predict")
def predict(x: Features, bg: BackgroundTasks) -> Prediction:
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())
    payload = x.model_dump()
    frame = pd.DataFrame([payload]).reindex(columns=app.state.meta["features"])

    score = float(app.state.pipeline.predict_proba(frame)[0, 1])

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    bg.add_task(db.save_prediction, request_id, payload, score, app.state.version, latency_ms)

    diabetes = (score >= app.state.meta["threshold"])

    return Prediction(
        score=score,
        diabetes=diabetes,
        model_version=app.state.version,
        request_id=request_id,
        latency_ms=latency_ms
    )