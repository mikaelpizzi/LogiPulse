import os

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "logipulse.duckdb")

st.set_page_config(
    page_title="LogiPulse | Operational Dashboard",
    page_icon="LP",
    layout="wide",
)


def load_data():
    """Load the final mart from DuckDB."""
    conn = duckdb.connect(DB_PATH)
    try:
        return conn.execute("SELECT * FROM main.fct_deliveries").fetchdf()
    finally:
        conn.close()


if not os.path.exists(DB_PATH):
    st.error(
        f"Database file '{DB_PATH}' was not found. Run 'python scripts/main.py' and 'dbt run' first."
    )
    st.stop()

try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to read 'main.fct_deliveries': {exc}")
    st.stop()

if df.empty:
    st.warning("The mart table is empty. Run the ingestion and dbt pipeline first.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"])

st.title("LogiPulse: Operational Dashboard")
st.markdown(
    "Operational analysis and automated remediation of critical last-mile delivery delays."
)
st.divider()

total_deliveries = len(df)
delayed_deliveries = int(df["is_severely_delayed"].sum())
delay_rate = (delayed_deliveries / total_deliveries) * 100 if total_deliveries else 0
avg_delay = df.loc[df["delay_minutes"] > 0, "delay_minutes"].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total completed deliveries", f"{total_deliveries:,}")
with col2:
    st.metric("Critical delays", f"{delayed_deliveries:,}", delta_color="inverse")
with col3:
    st.metric("Critical delay rate", f"{delay_rate:.1f}%")
with col4:
    st.metric(
        "Average delay among delayed orders",
        f"{avg_delay:.1f} min" if pd.notna(avg_delay) else "0 min",
    )

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Delay Distribution")
    fig_hist = px.histogram(
        df,
        x="delay_minutes",
        color="is_severely_delayed",
        nbins=30,
        barmode="overlay",
        labels={"delay_minutes": "Delay minutes", "count": "Orders"},
        color_discrete_map={False: "#9ae6b4", True: "#feb2b2"},
        title="Orders by delay minutes",
    )
    fig_hist.add_vline(x=15, line_dash="dash", line_color="red")
    st.plotly_chart(fig_hist, use_container_width=True)

with right_col:
    st.subheader("Delay Trend")
    fig_scatter = px.scatter(
        df,
        x="created_at",
        y="delay_minutes",
        color="is_severely_delayed",
        color_discrete_map={False: "#10b981", True: "#ef4444"},
        labels={"created_at": "Order time", "delay_minutes": "Delay minutes"},
        title="Delay history by order time",
        hover_data=["order_id", "user_id", "driver_id"],
    )
    fig_scatter.add_hline(y=15, line_dash="dash", line_color="red")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.subheader("Orders requiring remediation")

delayed_df = df[df["is_severely_delayed"]].sort_values(by="delay_minutes", ascending=False)

if delayed_df.empty:
    st.info("No critical delays were found in the current mart data.")
else:
    st.dataframe(
        delayed_df[["order_id", "user_id", "driver_id", "amount", "created_at", "delay_minutes"]],
        use_container_width=True,
        hide_index=True,
    )
