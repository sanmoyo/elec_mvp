"""
TEC Register Watch - Streamlit front-end.

Reads the CSVs and Markdown reports already produced by the GitHub Action
and local scripts. Does not fetch or modify any data itself.

Run:
    uv run streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="TEC Register Watch", layout="wide")

# Each boundary: its CSV from the report scripts, and its ETYS limit.
# Keep limits here as the single source of truth for the app.
BOUNDARIES = {
    "B13 (South West England)": {
        "csv": Path("data/b13_queue.csv"),
        "limit_mw": 2900,
        "report_dir": Path("b13_reports"),
        "rebuild_hint": "python b13_report.py",
    },
    "SW1 (South Wales)": {
        "csv": Path("data/sw1_queue.csv"),
        "limit_mw": 3800,
        "report_dir": Path("sw1_reports"),
        "rebuild_hint": "python sw1_report.py",
    },
}

CAPACITY_COL = "Cumulative Total Capacity (MW)"


def show_boundary(name, cfg):
    st.header(name)

    if not cfg["csv"].exists():
        st.warning(f"{cfg['csv']} not found. Run `{cfg['rebuild_hint']}` first.")
        return

    df = pd.read_csv(cfg["csv"])
    df[CAPACITY_COL] = pd.to_numeric(df[CAPACITY_COL], errors="coerce").fillna(0)

    limit = cfg["limit_mw"]
    built = df.loc[df["Project Status"] == "Built", CAPACITY_COL].sum()
    pipeline = df[CAPACITY_COL].sum() - built
    headroom = limit - built
    ratio = pipeline / headroom if headroom > 0 else None

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Boundary limit", f"{limit:,} MW")
    col2.metric("Already built", f"{built:,.0f} MW", f"{built / limit:.0%} of limit")
    col3.metric("Remaining headroom", f"{headroom:,.0f} MW")
    col4.metric(
        "Pipeline vs headroom",
        f"{ratio:.1f}x" if ratio is not None else "Over limit",
    )

    gate2 = df.loc[pd.to_numeric(df["Gate"], errors="coerce") >= 2, CAPACITY_COL].sum()
    st.caption(f"Gate 2+ (firm offer) capacity: {gate2:,.0f} MW")

    left, right = st.columns(2)
    with left:
        st.subheader("Pipeline by status")
        by_status = (
            df.groupby("Project Status")[CAPACITY_COL].sum().sort_values(ascending=False)
        )
        st.bar_chart(by_status)
    with right:
        st.subheader("Pipeline by gate")
        by_gate = df.groupby(df["Gate"].fillna("(blank)").astype(str))[CAPACITY_COL].sum()
        st.bar_chart(by_gate)

    st.subheader("Queued projects")
    st.dataframe(
        df[["Project Name", "Connection Site", CAPACITY_COL, "Stage", "Gate", "Project Status"]]
        .sort_values(CAPACITY_COL, ascending=False),
        width="stretch",
        hide_index=True,
    )

    snapshots = sorted(cfg["report_dir"].glob("*.md")) if cfg["report_dir"].exists() else []
    if len(snapshots) >= 2:
        st.subheader("Headroom over time")
        st.caption("Built capacity from dated snapshots. Grows as the automation runs.")
        history = []
        for path in snapshots:
            for line in path.read_text().splitlines():
                if line.startswith("- Already built:"):
                    mw = line.split(":")[1].split("MW")[0].replace(",", "").strip()
                    history.append({"date": path.stem, "built_mw": float(mw)})
        if history:
            st.line_chart(pd.DataFrame(history).set_index("date"))


def show_register_changes():
    st.header("Recent register changes")
    changes_dir = Path("changes")
    reports = sorted(changes_dir.glob("*.md"), reverse=True) if changes_dir.exists() else []
    if reports:
        st.caption(f"Latest report: {reports[0].stem}")
        st.markdown(reports[0].read_text())
    else:
        st.info("No change reports yet. They appear after NESO's next real update.")


# --- Sidebar navigation ---
st.sidebar.title("TEC Register Watch")
view = st.sidebar.radio(
    "View",
    ["Boundary headroom", "Register changes"],
)

if view == "Boundary headroom":
    boundary_name = st.sidebar.selectbox("Boundary", list(BOUNDARIES.keys()))
    st.title(boundary_name)
    st.caption("GB grid connection queue vs. published boundary capability")
    show_boundary(boundary_name, BOUNDARIES[boundary_name])
else:
    st.title("Register changes")
    st.caption("Meaningful changes between NESO register snapshots")
    show_register_changes()