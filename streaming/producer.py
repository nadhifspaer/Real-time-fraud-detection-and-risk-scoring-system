# Kafka producer, replays held-out test-split transactions at a configurable rate

import argparse
import json
import os
import sys
import time

import pandas as pd
from kafka import KafkaProducer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from src.feature_engineering import temporal_split

TOPIC = "transactions"
BOOTSTRAP_SERVERS = "localhost:9092"
DATA_PATH = os.path.join(REPO_ROOT, "data", "paysim_transactions.csv")


def load_test_transactions(data_path: str = DATA_PATH) -> pd.DataFrame:
    # held-out test split only, same cutoff used at training time
    df = pd.read_csv(data_path)
    _, test = temporal_split(df, train_frac=0.8)
    return test


def produce(
    rate: float,
    topic: str = TOPIC,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    limit: int = None,
):
    # publish one message per row, at rate messages per second
    test = load_test_transactions()
    if limit:
        test = test.head(limit)

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    delay = 1.0 / rate if rate > 0 else 0.0
    sent = 0
    for row in test.itertuples():
        message = {
            "transaction_id": int(row.Index),
            "step": int(row.step),
            "type": row.type,
            "amount": float(row.amount),
            "nameOrig": row.nameOrig,
            "oldbalanceOrg": float(row.oldbalanceOrg),
            "newbalanceOrig": float(row.newbalanceOrig),
            "nameDest": row.nameDest,
            "oldbalanceDest": float(row.oldbalanceDest),
            "newbalanceDest": float(row.newbalanceDest),
        }
        producer.send(topic, message)
        sent += 1
        if delay:
            time.sleep(delay)

    producer.flush()
    producer.close()
    return sent


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=5.0, help="messages per second")
    parser.add_argument("--topic", type=str, default=TOPIC)
    parser.add_argument("--bootstrap-servers", type=str, default=BOOTSTRAP_SERVERS)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    count = produce(
        rate=args.rate,
        topic=args.topic,
        bootstrap_servers=args.bootstrap_servers,
        limit=args.limit,
    )
    print(f"sent {count} messages to {args.topic}")
