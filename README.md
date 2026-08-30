# Real-Time Fraud & Risk Scoring System

## Introduction & Goals

This project scores e-wallet transactions for fraud risk using the PaySim simulated dataset, roughly 6.3 million mobile money transactions covering payments, transfers, cash-outs, cash-ins, and debits, with fraud under 1% of all rows and not evenly spread across the simulated time range. Each row carries the transaction type, amount, sender and receiver identifiers, sender and receiver balances before and after the transaction, and a fraud label.

The core of the system is a single tabular LightGBM classifier. SHAP explains each score the classifier produces, so a flagged transaction comes with a reason attached, not just a number. That scoring logic is served two ways from one codebase: a FastAPI service exposes it as a live endpoint, a Kafka producer and consumer pipeline replays transactions through that endpoint and streams the results into a shared store, and a Streamlit dashboard displays the outcome either by loading the model directly or by reading that live store. Docker Compose brings the full local stack up as one unit, and Prometheus and Grafana watch the API's request rate, latency, and error rate while it runs.

**Goals**

1. Catch a high share of fraud while keeping false positives low enough to stay within a realistic daily review capacity.
   How I know it worked: PR-AUC of 0.9229 and Precision@100 of 1.00 on the held-out test split, meaning every one of the top 100 highest-scored transactions was genuinely fraudulent.
2. Turn the flagging threshold into a stated business decision, not a guess.
   How I know it worked: the cost-based analysis shows a net value of $807,815 at the chosen threshold, versus $0 net value doing no screening at all, under the stated dollar assumptions.
3. Prove the scoring pipeline works as a real, live system, not only a notebook.
   How I know it worked: a verified end-to-end run where real transactions were produced through Kafka, scored through a live API, and landed in a shared store, observed at roughly one transaction scored per second. This reflects one verified test run, not a load-tested or guaranteed throughput figure.

## Approach

- **LightGBM**: the classifier at the core of the system, chosen because it handles the tabular, imbalanced, mixed-scale features here without heavy preprocessing. It trains on velocity features (transaction count and amount moved per account over the last hour, day, and week, counted strictly from prior transactions), a time-of-day feature, and the raw balance and amount columns not excluded for leakage. Trained on a temporal split, earlier data for training and a later held-out stretch for evaluation, with class weighting instead of synthetic oversampling to handle the fraud imbalance.
- **FastAPI**: exposes the trained classifier as a live scoring endpoint, chosen for its low overhead and straightforward request/response contract. It sits in the middle of the local stack, called by the Kafka consumer for every transaction and available for direct scoring requests. Set up as a single service loading the model once at startup and scoring on each incoming request.
- **Kafka**: streams transactions through the system the way a live feed would, chosen to demonstrate the scoring pipeline under a real streaming pattern rather than a batch job. A producer replays held-out transactions onto a topic, and a consumer reads each one, calls the FastAPI endpoint, and writes the scored result to a shared store. Set up as a producer/consumer pair running against a local Kafka broker in the Docker Compose stack.
- **Streamlit**: the single dashboard codebase, chosen so one app covers both a public-facing demo and a full local view without maintaining two frontends. It reads an environment variable to decide whether to load the model directly and score in place, or to read live scores from the Kafka-fed store. Set up as one `app.py` with the mode switch at the top and no other code path duplicated between the two modes.
- **Docker (Compose)**: packages the full local stack, chosen to bring up FastAPI, Kafka, the dashboard, Prometheus, and Grafana together as one reproducible unit rather than requiring each piece to be started by hand. It sits underneath the local deployment mode only. Set up as a single Compose file defining every service and the network between them.
- **Prometheus/Grafana**: monitors the API while the stack runs, chosen to give request rate, latency, and error rate visibility into a service that is otherwise a black box once it is handling live traffic. Prometheus scrapes metrics from the FastAPI service, and Grafana reads from Prometheus to render them. Set up as local-only components in the Compose stack, never wired toward the public cloud deployment.

## Excluded Features

Three features are deliberately left out of the model, each for a different reason.

The sender's post-transaction balance is excluded, along with any ratio computed from it against the transaction amount and the sender's starting balance. In this simulator, that balance change follows an almost exact arithmetic rule for fraudulent transactions far more consistently than it does for legitimate ones. A model trained on it would be learning to read a simulator quirk, not a pattern that would hold on real transactions.

The transaction type is excluded. In this dataset, fraud only ever appears as one of two specific transaction types. Including the raw type would let the model largely solve the problem by checking which type a transaction is, rather than by learning from the sender's behavior, the amounts involved, or the account history. That shortcut would not generalize.

A legacy rule-based flag included in the raw data is excluded entirely. It reflects an old, simple business rule, not a verified fraud outcome, and using it as an input would mean training the model partly on someone else's guess rather than on ground truth.

## Results Highlights

PR-AUC on the held-out evaluation split is 0.9229.

At a review capacity of 100 transactions, precision is 1.00 and recall is 0.0605. This recall figure is a single-batch number: it reflects the top 100 highest-scored transactions across the entire evaluation split at once, not a cumulative daily capacity added up over the several simulated days that split spans. Read as a one-time snapshot, not a running total.

Each transaction also receives an expected dollar exposure score, the fraud probability multiplied by the transaction amount, useful for prioritizing review by financial impact rather than fraud likelihood alone. Scored transactions are also aggregated per account into a running exposure total. This aggregation reflects real, verified logic rather than a heavily-populated feature, since accounts in this dataset rarely repeat.

## Business Impact

Under two stated dollar assumptions, an average loss per missed fraud and an average friction cost per false positive, scoring every transaction and reviewing only the ones above a chosen threshold produces substantially more net value than either reviewing nothing or reviewing everything indiscriminately. Both dollar figures are illustrative business assumptions, not researched numbers, and the resulting net value scales directly with them.

## Deployment

One Streamlit codebase, two modes, chosen by an environment variable.

Cloud mode loads the trained model directly inside the app process and scores transactions in place, with no separate backend and no dependency on Kafka or a live feed. It is meant to run standalone, including on a public hosting platform with no other infrastructure behind it.

Local mode is part of a full local stack: a FastAPI service exposing the scoring model, a Kafka producer replaying held-out transactions, a Kafka consumer scoring each one through the API and writing results to a shared store, and the dashboard reading that store on a short interval to show a live-updating view. Prometheus and Grafana provide request rate, latency, and error rate visibility into the API. This full stack runs through a single Docker Compose file and is local-only by design.

Live demo link: https://real-time-fraud-detection-and-risk-scoring-system-p5bn7gemlte7.streamlit.app/

## Setup

```
pip install -r requirements.txt
```
