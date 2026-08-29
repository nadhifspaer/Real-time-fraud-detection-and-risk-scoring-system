# PR-AUC, Precision@K, Recall@K, FPR at target recall, cost-based metric

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_curve


def pr_auc(y_true, y_score) -> float:
    # area under the precision-recall curve
    return average_precision_score(y_true, y_score)


def precision_recall_at_k(y_true, y_score, k: int = 100):
    # K=100: assumed fraud-analyst daily review capacity
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    order = np.argsort(y_score)[::-1][:k]
    tp = int(y_true[order].sum())
    total_positive = int(y_true.sum())
    precision = tp / k
    recall = tp / total_positive if total_positive > 0 else float("nan")
    return precision, recall


def fpr_at_recall(y_true, y_score, target_recall: float = 0.8) -> float:
    # false positive rate at the lowest threshold reaching target_recall
    fpr, tpr, _ = roc_curve(y_true, y_score)
    idx = int(np.searchsorted(tpr, target_recall))
    idx = min(idx, len(fpr) - 1)
    return float(fpr[idx])


def cost_based_metric(
    y_true,
    y_score,
    thresholds,
    avg_loss_per_missed_fraud: float = 500.0,
    avg_friction_cost_per_fp: float = 5.0,
) -> pd.DataFrame:
    # Cost assumptions: $500 avg. Loss per missed fraud, $5 avg friction cost per false positive
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    rows = []
    for t in thresholds:
        flagged = y_score >= t
        tp = int((flagged & (y_true == 1)).sum())
        fp = int((flagged & (y_true == 0)).sum())
        fn = int((~flagged & (y_true == 1)).sum())
        tn = int((~flagged & (y_true == 0)).sum())
        prevented_fraud_value = tp * avg_loss_per_missed_fraud
        friction_cost = fp * avg_friction_cost_per_fp
        net_benefit = prevented_fraud_value - friction_cost
        rows.append(
            {
                "threshold": t,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "prevented_fraud_value": prevented_fraud_value,
                "friction_cost": friction_cost,
                "net_benefit": net_benefit,
            }
        )
    return pd.DataFrame(rows)
