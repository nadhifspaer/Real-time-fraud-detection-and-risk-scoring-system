# Streamlit app

import lightgbm
import os
import sqlite3
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.explainability import explain_transaction
from src.score_pipeline import _get_model, _prepare_features, risk_score, score

APP_MODE = os.environ.get("APP_MODE", "cloud")
DATA_PATH = os.path.join(REPO_ROOT, "data", "paysim_transactions.csv")
DB_PATH = os.path.join(REPO_ROOT, "scored_transactions.db")

RAW_FIELDS = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
]


def render_header(subtitle: str):
    # shared page setup, both modes
    st.set_page_config(page_title="Fraud Detection", layout="wide")
    st.title("Fraud Detection")
    st.caption(subtitle)


def render_score_panel(fraud_score: float, exposure: float, explanation: pd.DataFrame):
    # shared score display, both modes
    col1, col2 = st.columns(2)
    col1.metric("Fraud score", f"{fraud_score:.4f}")
    col2.metric("Risk score", f"{exposure:.2f}")
    fig = px.bar(
        explanation.sort_values("shap_value"),
        x="shap_value",
        y="feature",
        orientation="h",
    )
    st.plotly_chart(fig, width='stretch')
    st.dataframe(explanation, width='stretch')


@st.cache_resource
def load_sample_transactions(n: int = 5000) -> pd.DataFrame:
    # cloud mode only, reads the bundled sample since the full dataset is not deployed
    sample_path = os.path.join(REPO_ROOT, "data", "paysim_sample.csv")
    return pd.read_csv(sample_path, nrows=n)


def run_cloud_mode():
    # score in-process, model loaded directly, no FastAPI call
    render_header("cloud mode, in-process scoring")

    pool = load_sample_transactions()
    fraud_rows = pool[pool["isFraud"] == 1].sample(9, random_state=1)
    legit_rows = pool[pool["isFraud"] == 0].sample(21, random_state=1)
    sample = pd.concat([fraud_rows, legit_rows])
    labels = [
        f"row {i}: step {r.step}, amount {r.amount:.2f}, isFraud={r.isFraud}"
        for i, r in sample.iterrows()
    ]
    st.caption(
        "This picker draws from a small subset of the full 6.3 million "
        "transaction dataset, not the complete set, and that subset only "
        "covers the earliest simulated time range."
    )
    choice = st.selectbox("sample transaction", labels)
    row = sample.iloc[labels.index(choice)]
    transaction = {field: row[field] for field in RAW_FIELDS}

    st.json(transaction)

    if st.button("score transaction"):
        fraud_score = score(transaction)
        exposure = risk_score(transaction, fraud_score)
        model = _get_model()
        X = _prepare_features(model, transaction)
        explanation = explain_transaction(model, X, top_n=5)
        render_score_panel(fraud_score, exposure, explanation)


def run_local_mode():
    # poll the live scored-transaction store on a short interval
    render_header("local mode, live scored-transaction feed")

    @st.fragment(run_every="2s")
    def live_feed():
        if not os.path.exists(DB_PATH):
            st.warning("no scored transactions yet")
            return

        conn = sqlite3.connect(DB_PATH)
        feed = pd.read_sql_query(
            "SELECT * FROM scored_transactions ORDER BY scored_at DESC LIMIT 50",
            conn,
        )
        try:
            top_accounts = pd.read_sql_query(
                "SELECT * FROM account_risk ORDER BY cumulative_risk DESC LIMIT 10",
                conn,
            )
        except sqlite3.OperationalError:
            top_accounts = pd.DataFrame()
        conn.close()

        if feed.empty:
            st.warning("no scored transactions yet")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("scored transactions", len(feed))
        col2.metric("mean score", f"{feed['score'].mean():.4f}")
        col3.metric("max score", f"{feed['score'].max():.4f}")

        fig = px.line(feed.sort_values("scored_at"), x="scored_at", y="score")
        st.plotly_chart(fig, width='stretch')

        st.dataframe(feed, width='stretch')

        st.subheader("Top accounts by accumulated risk")
        st.caption(
            "Account identifiers in this dataset behave as near-unique IDs, "
            "so this table will show few or no repeat accounts on a typical "
            "replay. That reflects a characteristic of the simulated "
            "dataset, not a defect in the accumulation logic."
        )
        st.dataframe(top_accounts, width='stretch')

    live_feed()


if APP_MODE == "local":
    run_local_mode()
else:
    run_cloud_mode()
