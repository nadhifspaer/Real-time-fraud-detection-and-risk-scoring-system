# tabular features, temporal split

import pandas as pd


def _velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    # backward-window velocity, 1h/24h/7d, per nameOrig
    d = df[["nameOrig", "step", "amount"]].copy()
    d["ts"] = pd.to_datetime(d["step"], unit="h", origin="2000-01-01")
    d = d.sort_values(["nameOrig", "ts"])
    g = d.groupby("nameOrig")
    windows = {"1h": "1h", "24h": "24h", "7d": "7D"}
    count_cols = []
    amount_cols = []
    for label, offset in windows.items():
        roll = g.rolling(offset, on="ts", closed="left")["amount"]
        count_col = f"txn_count_{label}"
        amount_col = f"txn_amount_{label}"
        d[count_col] = roll.count().values
        d[amount_col] = roll.sum().values
        count_cols.append(count_col)
        amount_cols.append(amount_col)
    d[count_cols] = d[count_cols].fillna(0).astype(int)
    d[amount_cols] = d[amount_cols].fillna(0)
    return d[count_cols + amount_cols].reindex(df.index)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    # velocity (backward-window, 1h/24h/7d), behavioral, raw numeric features
    # excluded: isFlaggedFraud, newbalanceOrig, balance-reconciliation ratio, type
    out = pd.DataFrame(index=df.index)
    out["amount"] = df["amount"]
    out["oldbalanceOrg"] = df["oldbalanceOrg"]
    out["oldbalanceDest"] = df["oldbalanceDest"]
    out["newbalanceDest"] = df["newbalanceDest"]
    out["hour_of_day"] = df["step"] % 24
    out = out.join(_velocity_features(df))
    out["step"] = df["step"]
    if "isFraud" in df.columns:
        out["isFraud"] = df["isFraud"]
    return out


def temporal_split(df: pd.DataFrame, train_frac: float = 0.8):
    # split by step range, not random
    min_step = df["step"].min()
    max_step = df["step"].max()
    cutoff = min_step + train_frac * (max_step - min_step)
    train = df[df["step"] <= cutoff]
    test = df[df["step"] > cutoff]
    return train, test
