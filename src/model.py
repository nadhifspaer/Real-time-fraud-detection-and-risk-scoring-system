# classifier training function

import lightgbm as lgb
import pandas as pd


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> lgb.LGBMClassifier:
    # step is split-only
    X = X_train.drop(columns=["step"], errors="ignore")
    model = lgb.LGBMClassifier(class_weight="balanced", random_state=42, verbose=-1)
    model.fit(X, y_train)
    return model
