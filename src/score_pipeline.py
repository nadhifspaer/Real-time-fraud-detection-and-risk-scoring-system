# single stable interface scoring function

import lightgbm
import joblib
import pandas as pd

from src.feature_engineering import build_features

MODEL_PATH = "models/lightgbm_model.joblib"

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _prepare_features(model, transaction: dict) -> pd.DataFrame:
    # raw transaction dict to a single aligned feature row
    raw = pd.DataFrame([transaction])
    features = build_features(raw)
    X = features.drop(columns=["step", "isFraud"], errors="ignore")
    return X[list(model.feature_name_)]


def score(transaction: dict) -> float:
    # feature lookup, model load, predict
    model = _get_model()
    X = _prepare_features(model, transaction)
    return float(model.predict_proba(X)[:, 1][0])


def risk_score(transaction: dict, fraud_score: float) -> float:
    # expected dollar exposure, fraud_score times transaction amount
    return fraud_score * float(transaction["amount"])
