# FastAPI app, /predict, /health, /metrics

import lightgbm
import time

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel

from src.explainability import explain_transaction
from src.score_pipeline import _get_model, _prepare_features, risk_score, score

app = FastAPI()

REQUEST_COUNT = Counter("predict_requests_total", "total /predict requests", ["status"])
REQUEST_LATENCY = Histogram("predict_latency_seconds", "latency of /predict requests")


class Transaction(BaseModel):
    # raw transaction schema: live payment fields
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(transaction: Transaction):
    # calls the score pipeline and SHAP explanation
    start = time.time()
    try:
        payload = transaction.model_dump()
        fraud_score = score(payload)
        exposure = risk_score(payload, fraud_score)
        model = _get_model()
        X = _prepare_features(model, payload)
        explanation = explain_transaction(model, X, top_n=5)
        REQUEST_COUNT.labels(status="success").inc()
        return {
            "fraud_score": fraud_score,
            "risk_score": exposure,
            "explanation": explanation.to_dict(orient="records"),
        }
    except Exception:
        REQUEST_COUNT.labels(status="error").inc()
        raise
    finally:
        REQUEST_LATENCY.observe(time.time() - start)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
