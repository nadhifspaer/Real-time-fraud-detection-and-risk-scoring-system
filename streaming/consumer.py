# Kafka consumer, calls /predict and writes the scored result to SQLite

import argparse
import json
import sqlite3
import time

import requests
from kafka import KafkaConsumer

TOPIC = "transactions"
BOOTSTRAP_SERVERS = "localhost:9092"
API_URL = "http://127.0.0.1:8000/predict"
DB_PATH = "scored_transactions.db"


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scored_transactions (
            transaction_id INTEGER PRIMARY KEY,
            score REAL NOT NULL,
            scored_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def consume(
    topic: str = TOPIC,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    api_url: str = API_URL,
    db_path: str = DB_PATH,
    max_messages: int = None,
):
    conn = init_db(db_path)
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
    )

    scored = 0
    for message in consumer:
        transaction = dict(message.value)
        transaction_id = transaction.pop("transaction_id")

        response = requests.post(api_url, json=transaction, timeout=10)
        response.raise_for_status()
        fraud_score = response.json()["fraud_score"]
        scored_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        conn.execute(
            "INSERT OR REPLACE INTO scored_transactions (transaction_id, score, scored_at) VALUES (?, ?, ?)",
            (transaction_id, fraud_score, scored_at),
        )
        conn.commit()

        scored += 1
        if max_messages and scored >= max_messages:
            break

    conn.close()
    return scored


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default=TOPIC)
    parser.add_argument("--bootstrap-servers", type=str, default=BOOTSTRAP_SERVERS)
    parser.add_argument("--api-url", type=str, default=API_URL)
    parser.add_argument("--db-path", type=str, default=DB_PATH)
    parser.add_argument("--max-messages", type=int, default=None)
    args = parser.parse_args()
    count = consume(
        topic=args.topic,
        bootstrap_servers=args.bootstrap_servers,
        api_url=args.api_url,
        db_path=args.db_path,
        max_messages=args.max_messages,
    )
    print(f"scored {count} messages into {args.db_path}")
