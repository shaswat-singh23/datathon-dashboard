"""Starter dashboard. Replace once we pick a challenge.

Run: uv run streamlit run app/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from src import io  # noqa: E402

st.set_page_config(page_title="Datathon", layout="wide")
st.title("Team dashboard")
st.caption("Starter stub. Swap in the real dashboard once we pick a challenge.")


@st.cache_data
def list_tables() -> dict[str, str]:
    return {k: str(v) for k, v in io.tables().items()}


@st.cache_data
def load_table(name: str):
    return io.sql(f'select * from "{name}" limit 200000').to_pandas()


tables = list_tables()
if not tables:
    st.info(
        "No data found. Put files in data/raw/ (local) or app/data/ (deployed), "
        "or run `uv run python scripts/make_sample_data.py`."
    )
    st.stop()

name = st.sidebar.selectbox("Table", sorted(tables))
df = load_table(name)

c1, c2, c3 = st.columns(3)
c1.metric("Rows (loaded)", f"{len(df):,}")
c2.metric("Columns", len(df.columns))
c3.metric("Null cells", f"{int(df.isna().sum().sum()):,}")

st.dataframe(df.head(500), width="stretch")

numeric = df.select_dtypes("number").columns.tolist()
if numeric:
    st.subheader("Quick chart")
    kind = st.radio("Type", ["histogram", "scatter", "line", "bar"], horizontal=True)
    left, right = st.columns(2)
    x = left.selectbox("x", df.columns)
    y = right.selectbox("y", numeric)
    plot_df = df.sample(min(len(df), 20000), random_state=0) if kind == "scatter" else df
    if kind == "histogram":
        fig = px.histogram(df, x=y)
    elif kind == "scatter":
        fig = px.scatter(plot_df, x=x, y=y, opacity=0.5)
    else:
        agg = df.groupby(x, as_index=False)[y].sum().sort_values(x)
        fig = (px.line if kind == "line" else px.bar)(agg, x=x, y=y)
    st.plotly_chart(fig, width="stretch")
