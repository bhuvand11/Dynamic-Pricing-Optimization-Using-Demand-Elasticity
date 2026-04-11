from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Phase 6 - Pricing Dashboard", page_icon="📈", layout="wide")


DATA_PATH = Path("output") / "phase5_executive_recommendations.csv"
VALID_STATUSES = ["Not Started", "Piloting", "Live"]


@st.cache_data
def load_recommendations(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalize column naming for UI usage while keeping source columns intact.
    df = df.rename(
        columns={
            "Store": "Store_ID",
            "Elasticity_Segment": "Segment",
            "Elasticity": "Elasticity",
            "Current_Price": "Current_Price",
            "Recommended_Price": "Recommended_Price",
            "Price_Change_Pct": "Price_Change_Pct",
            "Baseline_Revenue": "Baseline_Revenue",
            "Recommended_Revenue": "Recommended_Revenue",
            "Expected_Revenue_Change_Abs": "Revenue_Uplift_Abs",
            "Expected_Revenue_Change_Pct": "Revenue_Uplift_Pct",
            "Expected_Demand_Change_Pct": "Demand_Change_Pct",
            "Implementation_Risk": "Implementation_Risk",
            "Decision_Type": "Decision_Type",
        }
    )

    expected = [
        "Store_ID",
        "Segment",
        "Elasticity",
        "Current_Price",
        "Recommended_Price",
        "Price_Change_Pct",
        "Baseline_Revenue",
        "Recommended_Revenue",
        "Revenue_Uplift_Abs",
        "Revenue_Uplift_Pct",
        "Demand_Change_Pct",
        "Implementation_Risk",
        "Decision_Type",
    ]
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in {path}: {missing}")

    return df


def initialize_status_map(df: pd.DataFrame) -> None:
    if "store_status_map" in st.session_state:
        return

    # Localhost demo default: low-risk stores start in pilot.
    status_map: dict[int, str] = {}
    for row in df.itertuples(index=False):
        store_id = int(row.Store_ID)
        risk = str(row.Implementation_Risk).strip().upper()
        status_map[store_id] = "Piloting" if risk == "LOW" else "Not Started"

    st.session_state.store_status_map = status_map


def add_status_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Implementation_Status"] = out["Store_ID"].astype(int).map(st.session_state.store_status_map)
    return out


def render_header(df: pd.DataFrame) -> None:
    baseline_total = float(df["Baseline_Revenue"].sum())
    recommended_total = float(df["Recommended_Revenue"].sum())
    uplift_abs = recommended_total - baseline_total
    uplift_pct = (uplift_abs / baseline_total * 100.0) if baseline_total else 0.0

    st.title("Phase 6: Simple Real-Time Pricing Dashboard")
    st.caption("Audience: teammates | Scope: localhost only | Data source: Phase 5 output CSV")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stores", f"{df['Store_ID'].nunique()}")
    c2.metric("Baseline Revenue", f"${baseline_total:,.0f}")
    c3.metric("Recommended Revenue", f"${recommended_total:,.0f}")
    c4.metric("Portfolio Uplift", f"${uplift_abs:,.0f}", f"{uplift_pct:.2f}%")


def render_controls(df: pd.DataFrame) -> pd.DataFrame:
    st.subheader("Store Filters")
    c1, c2, c3 = st.columns([2, 2, 1])

    segments = sorted(df["Segment"].dropna().unique().tolist())
    selected_segments = c1.multiselect("Segment", options=segments, default=segments)

    store_ids = sorted(df["Store_ID"].astype(int).unique().tolist())
    selected_store = c2.selectbox("Store", options=["All"] + store_ids)

    show_live_only = c3.checkbox("Live only", value=False)

    filtered = df[df["Segment"].isin(selected_segments)]
    if selected_store != "All":
        filtered = filtered[filtered["Store_ID"] == int(selected_store)]
    if show_live_only:
        filtered = filtered[filtered["Implementation_Status"] == "Live"]

    return filtered


def render_charts(df: pd.DataFrame) -> None:
    st.subheader("Quick Insights")

    c1, c2 = st.columns(2)
    with c1:
        seg_summary = (
            df.groupby("Segment", as_index=False)
            .agg(Stores=("Store_ID", "count"), Uplift_USD=("Revenue_Uplift_Abs", "sum"))
            .sort_values("Uplift_USD", ascending=False)
        )
        st.markdown("**Revenue Uplift by Segment**")
        st.bar_chart(seg_summary.set_index("Segment")["Uplift_USD"])

    with c2:
        scatter = df[["Elasticity", "Baseline_Revenue"]].copy()
        st.markdown("**Elasticity vs Baseline Revenue**")
        st.scatter_chart(scatter, x="Elasticity", y="Baseline_Revenue")


def render_table(df: pd.DataFrame) -> None:
    st.subheader("Store Performance")

    display_cols = [
        "Store_ID",
        "Segment",
        "Elasticity",
        "Current_Price",
        "Recommended_Price",
        "Price_Change_Pct",
        "Baseline_Revenue",
        "Recommended_Revenue",
        "Revenue_Uplift_Abs",
        "Revenue_Uplift_Pct",
        "Demand_Change_Pct",
        "Implementation_Risk",
        "Implementation_Status",
    ]

    table_df = df[display_cols].sort_values("Revenue_Uplift_Abs", ascending=False)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Elasticity": st.column_config.NumberColumn(format="%.4f"),
            "Current_Price": st.column_config.NumberColumn(format="$%.2f"),
            "Recommended_Price": st.column_config.NumberColumn(format="$%.2f"),
            "Price_Change_Pct": st.column_config.NumberColumn("Price Change %", format="%.2f%%"),
            "Baseline_Revenue": st.column_config.NumberColumn(format="$%,.0f"),
            "Recommended_Revenue": st.column_config.NumberColumn(format="$%,.0f"),
            "Revenue_Uplift_Abs": st.column_config.NumberColumn("Uplift $", format="$%,.0f"),
            "Revenue_Uplift_Pct": st.column_config.NumberColumn("Uplift %", format="%.2f%%"),
            "Demand_Change_Pct": st.column_config.NumberColumn("Demand Change %", format="%.2f%%"),
        },
    )

    csv_data = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered stores (CSV)",
        data=csv_data,
        file_name="phase6_filtered_store_recommendations.csv",
        mime="text/csv",
    )


def render_status_editor(df: pd.DataFrame) -> None:
    st.subheader("Implementation Tracker (Session-only)")
    st.caption("Status updates persist during this Streamlit session and are not written to disk.")

    options = sorted(df["Store_ID"].astype(int).unique().tolist())
    c1, c2 = st.columns([1, 2])
    with c1:
        selected_store = st.selectbox("Select store", options=options, key="status_store")
    with c2:
        current = st.session_state.store_status_map[int(selected_store)]
        new_status = st.radio(
            "Set status",
            options=VALID_STATUSES,
            horizontal=True,
            index=VALID_STATUSES.index(current),
            key="status_value",
        )

    st.session_state.store_status_map[int(selected_store)] = new_status

    status_df = pd.DataFrame(
        {
            "Store_ID": options,
            "Implementation_Status": [st.session_state.store_status_map[s] for s in options],
        }
    )
    counts = status_df["Implementation_Status"].value_counts().reindex(VALID_STATUSES, fill_value=0)

    c3, c4, c5 = st.columns(3)
    c3.metric("Not Started", int(counts["Not Started"]))
    c4.metric("Piloting", int(counts["Piloting"]))
    c5.metric("Live", int(counts["Live"]))


def main() -> None:
    if not DATA_PATH.exists():
        st.error(f"Could not find required data file: {DATA_PATH}")
        st.stop()

    df = load_recommendations(DATA_PATH)
    initialize_status_map(df)
    df = add_status_column(df)

    render_header(df)
    filtered_df = render_controls(df)

    if filtered_df.empty:
        st.warning("No stores match the current filters.")
        return

    render_charts(filtered_df)
    render_table(filtered_df)
    render_status_editor(df)


if __name__ == "__main__":
    main()
