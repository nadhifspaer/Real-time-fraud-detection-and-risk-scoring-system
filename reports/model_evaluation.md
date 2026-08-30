# Model Evaluation

## Excluded Features

- Three features and one derived-feature category are excluded from the feature matrix, decided before training began.
- `newbalanceOrig` is excluded.
  - Combined with `amount` and `oldbalanceOrg`, it reconstructs the near-exact identity `newbalanceOrig = oldbalanceOrg - amount`, which holds far more often for fraud rows than for non-fraud rows in this simulator.
  - Why it matters: this is a bookkeeping artifact of how the simulator generates fraud transactions, not a transferable fraud behavior, so the column and any ratio derived from it (for example an amount-to-balance ratio) are excluded from the feature matrix.
- `type` is excluded.
  - The simulator generates fraud exclusively as `TRANSFER` or `CASH_OUT` transactions.
  - Why it matters: using raw `type` as a feature is close to reading the label directly, since a model could learn to flag those two transaction types almost regardless of any other signal.
- `isFlaggedFraud` is excluded.
  - It is a legacy rule-based flag from the simulator, not ground truth.
  - Why it matters: it is never used as a feature or a target.
- What remains in the feature matrix: velocity features (transaction count and total amount per account, in the last 1 hour, 24 hours, and 7 days, computed strictly backward from each transaction's step), a time-of-day feature derived from step, and the raw numeric columns not implicated in the reconciliation identity above (`amount`, `oldbalanceOrg`, `oldbalanceDest`, `newbalanceDest`).

## Velocity Feature Importance

- SHAP analysis on the trained classifier shows the six velocity features, `txn_count_1h`, `txn_count_24h`, `txn_count_7d`, `txn_amount_1h`, `txn_amount_24h`, and `txn_amount_7d`, carry near-zero importance, both by split-count and by mean absolute SHAP value. All six sit several orders of magnitude below `oldbalanceOrg` and `amount`, the two most important features by both measures.
- Of 6,362,620 total rows, 6,353,307 have a unique `nameOrig`. PaySim accounts almost never transact more than once, so an account with no prior transaction produces a value of zero for all six velocity features on its one and only row.
- With unique accounts making up the overwhelming majority of rows, the velocity features are near-constant at zero across nearly the entire dataset. This leaves a tree-based classifier almost nothing to split on.
- This is a limitation of this feature category for this dataset, not a defect in the feature engineering or in the SHAP analysis itself. The velocity features are computed correctly and would carry real signal on a dataset where accounts transact repeatedly.

## Account-Level Risk Aggregation

- `risk_score` is computed as `fraud_score` multiplied by the transaction amount, representing expected dollar exposure for that transaction.
  - It is produced by the same scoring function as `fraud_score`, alongside it, not by a separate model.
- A separate account-level aggregation accumulates a per-transaction risk value by account identifier across every transaction scored for that account.
  - This aggregation is limited by the same account-identifier characteristic described above.
- Across the full 123,580-row held-out test split, only 2 accounts have more than one transaction, every other account appears exactly once.
  - Why it matters: replaying this split through the aggregation will show a running transaction count of 1 for nearly every account, not because the aggregation logic is broken, but because accounts in this simulated dataset essentially never transact more than once.
- The aggregation logic was verified directly against the 2 real accounts in the test split that do have repeat transactions.
  - Both accounts' running totals matched the exact sum of each transaction's individual risk contribution, and their transaction counts incremented correctly rather than resetting or overwriting.
- This is a data limitation for any account-level aggregation feature built on this dataset, not a defect in the aggregation logic itself.

## Evaluation Setup

The split is temporal, not random. Training uses the earlier 80% of the step range, testing uses the later 20%.

| Split | Rows | Fraud rows | Fraud rate |
|---|---|---|---|
| Train | 6,239,040 | 6,559 | 0.105% |
| Test | 123,580 | 1,654 | 1.34% |

The test-split fraud rate is roughly 12.7 times the train-split rate. This is a byproduct of the temporal, step-based split rather than a random split. Fraud is not distributed evenly across the simulated time range, and the later 20% of steps happens to carry a much higher concentration of fraud than the earlier 80%.
- Every metric below should be read against this shifted prior.
  - A PR-AUC computed against a 1.34% positive rate is not directly comparable to one computed against a 0.105% positive rate. The difference in base rate between train and test is a property of this dataset's temporal structure, not a modeling choice.

## PR-AUC

- PR-AUC on the test split: **0.9229**. This number should be read against the test-split fraud rate of 1.34%, not the train-split rate of 0.105%, for the reason stated above.

## Precision@K and Recall@K

K is set to 100, on the stated assumption that a fraud-analyst team can manually review about 100 flagged transactions per day.

| Metric | Value |
|---|---|
| Precision@100 | 1.00 |
| Recall@100 | 0.0605 |

- All 100 of the highest-scored transactions in the test split are true fraud. Recall@100 is low in absolute terms because the test split contains 1,654 fraud rows and only the top 100 are being counted.
- This figure is a single-batch top-100 over the entire test split, not a cumulative multi-day capacity figure. The test split spans roughly 6.2 simulated days (steps 595 through 743). A single top-100 ranking over the full 6.2-day window is not the same as a fraud-analyst team reviewing 100 transactions on each of those 6.2 days, which would represent a cumulative review capacity closer to 600 transactions and would be expected to produce a materially higher recall figure.
  - Why it matters: Recall@100 as reported here must be read strictly as single-batch capacity, not scaled by the number of days in the test window.

## False Positive Rate at Target Recall

At a target recall of 0.80, the false positive rate on the test split is **0.00151**. At the threshold needed to catch 80% of fraud, roughly 0.15% of legitimate transactions are flagged.

## Cost-Based Metric

Net benefit is defined as prevented fraud value minus false-positive friction cost, computed across a range of score thresholds from 0.00 to 1.00 in steps of 0.05.
Two dollar-value assumptions drive the dollar columns below: an average loss of $500 per missed fraud and an average friction cost of $5 per false positive. Neither is derived from PaySim, both are stated business assumptions.

| Threshold | TP | FP | FN | Prevented fraud value | Friction cost | Net benefit |
|---|---|---|---|---|---|---|
| 0.00 | 1,654 | 121,926 | 0 | $827,000 | $609,630 | $217,370 |
| 0.20 | 1,653 | 6,335 | 1 | $826,500 | $31,675 | $794,825 |
| 0.40 | 1,651 | 4,012 | 3 | $825,500 | $20,060 | $805,440 |
| 0.45 | 1,648 | 3,600 | 6 | $824,000 | $18,000 | $806,000 |
| 0.50 | 1,648 | 3,262 | 6 | $824,000 | $16,310 | $807,690 |
| 0.55 | 1,645 | 2,937 | 9 | $822,500 | $14,685 | $807,815 |
| 0.60 | 1,641 | 2,583 | 13 | $820,500 | $12,915 | $807,585 |
| 0.80 | 1,568 | 1,184 | 86 | $784,000 | $5,920 | $778,080 |
| 1.00 | 0 | 0 | 1,654 | $0 | $0 | $0 |

The threshold 0.00 row is the flag-everything case, not a true no-screening baseline: the no-screening case is the threshold 1.00 row, where nothing is flagged.
