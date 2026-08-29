# SHAP explanations: tabular feature matrix

import lightgbm
import pandas as pd
import shap

VELOCITY_FEATURES = [
    "txn_count_1h",
    "txn_count_24h",
    "txn_count_7d",
    "txn_amount_1h",
    "txn_amount_24h",
    "txn_amount_7d",
]


def _align_columns(model, X: pd.DataFrame) -> pd.DataFrame:
    # drop split only column, match training column order
    X = X.drop(columns=["step"], errors="ignore")
    return X[list(model.feature_name_)]


def summary_plot(model, X_test: pd.DataFrame, show: bool = True) -> pd.DataFrame:
    # SHAP summary plot across the test set, all features always displayed
    X = _align_columns(model, X_test)
    explainer = shap.TreeExplainer(model)
    explanation = explainer(X)

    shap.summary_plot(explanation, X, max_display=X.shape[1], show=show)

    mean_abs_shap = pd.DataFrame(
        {
            "feature": X.columns,
            "mean_abs_shap": abs(explanation.values).mean(axis=0),
        }
    )
    mean_abs_shap["is_velocity_feature"] = mean_abs_shap["feature"].isin(VELOCITY_FEATURES)
    return mean_abs_shap.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def explain_transaction(model, transaction: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    # top contributing SHAP features for one flagged transaction
    X = _align_columns(model, transaction)
    explainer = shap.TreeExplainer(model)
    explanation = explainer(X)

    row = pd.DataFrame(
        {
            "feature": X.columns,
            "feature_value": X.iloc[0].values,
            "shap_value": explanation.values[0],
        }
    )
    row["abs_shap_value"] = row["shap_value"].abs()
    return row.sort_values("abs_shap_value", ascending=False).head(top_n).drop(columns=["abs_shap_value"]).reset_index(drop=True)
