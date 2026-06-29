from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.config import DAILY_FILE, FORECAST_FILE, MODEL_COMPARISON_FILE  # noqa: E402
from src.data_processing import run_processing  # noqa: E402


st.set_page_config(
    page_title="UAC Capacity Analytics",
    layout="wide",
)

STATE_COLORS = {
    "Normal": "#2E7D32",
    "Watch": "#B7791F",
    "Strained": "#B42318",
    "Relief": "#1D4ED8",
    "Missing Report": "#6B7280",
}

METRIC_LABELS = {
    "total_system_load": "Total System Load",
    "hhs_care": "HHS Care Load",
    "cbp_custody": "CBP Custody",
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17202a;
            --muted: #667085;
            --line: #d9e2ec;
            --panel: #ffffff;
            --canvas: #f6f8fb;
            --teal: #0f766e;
            --gold: #b7791f;
            --red: #b42318;
            --blue: #1d4ed8;
        }
        .stApp {
            background: var(--canvas);
            color: var(--ink);
        }
        .block-container {
            padding-top: 1.15rem;
            padding-bottom: 2.5rem;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        h1 {
            font-size: 1.9rem;
            line-height: 1.18;
            margin-bottom: 0.2rem;
        }
        h2, h3 {
            color: var(--ink);
        }
        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
            box-shadow: 0 8px 22px rgba(23, 32, 42, 0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }
        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.55rem;
        }
        .hero-panel {
            background: linear-gradient(135deg, #ffffff 0%, #f1fbf9 54%, #fff8ec 100%);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 28px rgba(23, 32, 42, 0.06);
        }
        .hero-eyebrow {
            color: var(--teal);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .hero-copy {
            color: var(--muted);
            max-width: 920px;
            margin: 0.25rem 0 0;
            font-size: 0.98rem;
            line-height: 1.55;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.75rem 0 1.05rem;
        }
        .status-tile {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            min-height: 76px;
        }
        .status-label {
            color: var(--muted);
            font-size: 0.78rem;
            margin-bottom: 0.25rem;
        }
        .status-value {
            color: var(--ink);
            font-size: 1.05rem;
            font-weight: 700;
        }
        .status-note {
            color: var(--muted);
            font-size: 0.77rem;
            margin-top: 0.16rem;
        }
        .state-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            color: white;
            font-size: 0.85rem;
            font-weight: 700;
            padding: 0.22rem 0.62rem;
            min-width: 76px;
        }
        .section-note {
            color: var(--muted);
            margin-top: -0.4rem;
            margin-bottom: 0.65rem;
            font-size: 0.9rem;
        }
        @media (max-width: 900px) {
            .status-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 560px) {
            .status-grid {
                grid-template-columns: 1fr;
            }
            h1 {
                font-size: 1.45rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DAILY_FILE.exists():
        run_processing()
    df = pd.read_csv(DAILY_FILE, parse_dates=["date"])
    return df


@st.cache_data(show_spinner=False)
def load_forecasts() -> tuple[pd.DataFrame, pd.DataFrame]:
    comparison = (
        pd.read_csv(MODEL_COMPARISON_FILE)
        if MODEL_COMPARISON_FILE.exists()
        else pd.DataFrame()
    )
    forecasts = (
        pd.read_csv(FORECAST_FILE, parse_dates=["date"])
        if FORECAST_FILE.exists()
        else pd.DataFrame()
    )
    return comparison, forecasts


def metric_delta(series: pd.Series) -> float:
    if len(series.dropna()) < 2:
        return 0.0
    return float(series.dropna().iloc[-1] - series.dropna().iloc[-2])


def format_delta(value: float, suffix: str = "") -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,.0f}{suffix}"


def plot_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 18, "r": 18, "t": 48, "b": 18},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font={"family": "Arial", "color": "#17202a"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf2f7", linecolor="#d9e2ec")
    fig.update_yaxes(showgrid=True, gridcolor="#edf2f7", linecolor="#d9e2ec")
    return fig


df = load_data()
comparison_df, forecast_df = load_forecasts()
apply_theme()

st.markdown(
    """
    <div class="hero-panel">
      <div class="hero-eyebrow">Healthcare Capacity Intelligence</div>
      <h1>System Capacity & Care Load Analytics for Unaccompanied Children</h1>
      <p class="hero-copy">
        Executive view of CBP custody pressure, HHS care load, net intake balance,
        backlog risk, relief periods, volatility, and short-term forecasting.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis Controls")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    granularity = st.selectbox("Time granularity", ["Daily", "Weekly", "Monthly"])
    rolling_window = st.slider("Rolling average window", 7, 30, 14)
    show_missing = st.toggle("Show missing-report dates", value=False)
    selected_metrics = st.multiselect(
        "System load metrics",
        ["total_system_load", "hhs_care", "cbp_custody"],
        default=["total_system_load", "hhs_care"],
    )
    forecast_horizon = st.slider("Forecast horizon", 7, 30, 30)

filtered = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)].copy()
if not show_missing:
    filtered = filtered[filtered["is_observed"]]

if granularity == "Weekly":
    chart_df = (
        filtered.set_index("date")
        .resample("W-SUN")
        .agg(
            total_system_load=("total_system_load", "mean"),
            hhs_care=("hhs_care", "mean"),
            cbp_custody=("cbp_custody", "mean"),
            net_daily_intake=("net_daily_intake", "sum"),
            discharged_hhs=("discharged_hhs", "sum"),
            transferred_out_cbp=("transferred_out_cbp", "sum"),
            care_load_volatility_index=("care_load_volatility_index", "mean"),
        )
        .reset_index()
    )
elif granularity == "Monthly":
    chart_df = (
        filtered.set_index("date")
        .resample("MS")
        .agg(
            total_system_load=("total_system_load", "mean"),
            hhs_care=("hhs_care", "mean"),
            cbp_custody=("cbp_custody", "mean"),
            net_daily_intake=("net_daily_intake", "sum"),
            discharged_hhs=("discharged_hhs", "sum"),
            transferred_out_cbp=("transferred_out_cbp", "sum"),
            care_load_volatility_index=("care_load_volatility_index", "mean"),
        )
        .reset_index()
    )
else:
    chart_df = filtered.copy()

chart_df["selected_rolling_avg"] = (
    chart_df["total_system_load"].rolling(rolling_window, min_periods=1).mean()
)

observed_filtered = filtered[filtered["is_observed"]]
latest = observed_filtered.sort_values("date").tail(1)
if latest.empty:
    st.warning("No observed records are available for the selected filters.")
    st.stop()
latest_row = latest.iloc[0]
previous_rows = observed_filtered.sort_values("date").tail(2)
state = latest_row["system_state"]
state_color = STATE_COLORS.get(state, "#6B7280")
observed_days = int(observed_filtered["is_observed"].sum())
missing_days = int(filtered["flag_missing_date"].sum())
strain_days = int(observed_filtered["system_state"].eq("Strained").sum())
relief_days = int(observed_filtered["system_state"].eq("Relief").sum())
anomaly_count = int(
    observed_filtered[
        [
            "flag_transfers_gt_cbp_custody",
            "flag_discharges_gt_hhs_care",
            "flag_zero_transfer_ratio",
            "volatility_spike_flag",
            "net_intake_spike_flag",
        ]
    ]
    .fillna(False)
    .any(axis=1)
    .sum()
)

st.markdown(
    f"""
    <div class="status-grid">
      <div class="status-tile">
        <div class="status-label">Latest Reporting Date</div>
        <div class="status-value">{latest_row['date'].date()}</div>
        <div class="status-note">{observed_days:,} observed reporting days selected</div>
      </div>
      <div class="status-tile">
        <div class="status-label">Current System State</div>
        <div class="status-value"><span class="state-pill" style="background:{state_color};">{state}</span></div>
        <div class="status-note">{strain_days:,} strained days; {relief_days:,} relief days</div>
      </div>
      <div class="status-tile">
        <div class="status-label">Data Coverage</div>
        <div class="status-value">{missing_days:,} missing dates</div>
        <div class="status-note">Missing reports are flagged in the panel</div>
      </div>
      <div class="status-tile">
        <div class="status-label">Quality Review Items</div>
        <div class="status-value">{anomaly_count:,}</div>
        <div class="status-note">Observed days with at least one alert</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Total Children Under Care",
    f"{latest_row['total_system_load']:,.0f}",
    format_delta(metric_delta(previous_rows["total_system_load"])),
)
col2.metric(
    "HHS Care Load",
    f"{latest_row['hhs_care']:,.0f}",
    format_delta(metric_delta(previous_rows["hhs_care"])),
)
col3.metric(
    "CBP Custody",
    f"{latest_row['cbp_custody']:,.0f}",
    format_delta(metric_delta(previous_rows["cbp_custody"])),
)
col4.metric(
    "Net Intake Pressure",
    f"{latest_row['net_daily_intake']:,.0f}",
    format_delta(metric_delta(previous_rows["net_daily_intake"])),
)
ratio = latest_row["discharge_offset_ratio"]
col5.metric("Discharge Offset Ratio", "N/A" if pd.isna(ratio) else f"{ratio:,.2f}")

overview_tab, stress_tab, forecast_tab, quality_tab = st.tabs(
    ["Overview", "Flow & Stress", "Forecasts", "Data Quality"]
)

with overview_tab:
    st.subheader("System Load Overview")
    st.markdown(
        '<div class="section-note">Total care burden combines CBP custody and HHS care census.</div>',
        unsafe_allow_html=True,
    )
    load_fig = go.Figure()
    palette = ["#0f766e", "#1d4ed8", "#b7791f"]
    for idx, metric in enumerate(selected_metrics):
        load_fig.add_trace(
            go.Scatter(
                x=chart_df["date"],
                y=chart_df[metric],
                mode="lines",
                name=METRIC_LABELS.get(metric, metric),
                line={"color": palette[idx % len(palette)], "width": 2.2},
            )
        )
    load_fig.add_trace(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["selected_rolling_avg"],
            mode="lines",
            name=f"{rolling_window}-period total load average",
            line={"dash": "dash", "color": "#b42318", "width": 2},
        )
    )
    load_fig.update_layout(xaxis_title="Date", yaxis_title="Children", legend_title_text="Metric")
    st.plotly_chart(plot_layout(load_fig), use_container_width=True)

    st.subheader("CBP vs HHS Load Comparison")
    comparison_fig = px.line(
        chart_df,
        x="date",
        y=["cbp_custody", "hhs_care"],
        labels={"value": "Children", "variable": "Metric"},
        color_discrete_sequence=["#b7791f", "#0f766e"],
    )
    comparison_fig.update_traces(line={"width": 2.2})
    st.plotly_chart(plot_layout(comparison_fig), use_container_width=True)

with stress_tab:
    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("Net Intake & Backlog Trends")
        net_fig = px.bar(
            filtered[filtered["is_observed"]],
            x="date",
            y="net_daily_intake",
            color="system_state",
            color_discrete_map=STATE_COLORS,
            labels={"net_daily_intake": "Transfers minus discharges"},
        )
        net_fig.add_hline(y=0, line_color="#667085", line_width=1)
        st.plotly_chart(plot_layout(net_fig), use_container_width=True)

    with right:
        st.subheader("Care Load Volatility")
        vol_fig = px.area(
            chart_df,
            x="date",
            y="care_load_volatility_index",
            labels={"care_load_volatility_index": "Volatility index"},
            color_discrete_sequence=["#1d4ed8"],
        )
        st.plotly_chart(plot_layout(vol_fig), use_container_width=True)

    st.subheader("System State Timeline")
    state_fig = px.scatter(
        filtered,
        x="date",
        y="total_system_load",
        color="system_state",
        color_discrete_map=STATE_COLORS,
        hover_data=["net_daily_intake", "care_load_volatility_index", "flag_transfers_gt_cbp_custody"],
        labels={"total_system_load": "Total system load"},
    )
    state_fig.update_traces(marker={"size": 7, "line": {"width": 0.4, "color": "#ffffff"}})
    st.plotly_chart(plot_layout(state_fig), use_container_width=True)

with forecast_tab:
    st.subheader("Forecasting")
    if comparison_df.empty or forecast_df.empty:
        st.info("Forecast outputs are not available yet. Run `python run_pipeline.py` to generate them.")
    else:
        target = st.selectbox("Forecast target", sorted(forecast_df["target"].unique()))
        available_models = sorted(forecast_df.loc[forecast_df["target"].eq(target), "model"].unique())
        model = st.selectbox("Forecast model", available_models)
        target_forecast = forecast_df[
            forecast_df["target"].eq(target) & forecast_df["model"].eq(model)
        ].head(forecast_horizon)

        history_column = {
            "Total System Load": "total_system_load",
            "HHS Care Load": "hhs_care",
            "Net Daily Intake": "net_daily_intake",
            "Discharge Volume": "discharged_hhs",
        }[target]
        history = df[df["is_observed"]][["date", history_column]].tail(180)
        forecast_fig = go.Figure()
        forecast_fig.add_trace(
            go.Scatter(
                x=history["date"],
                y=history[history_column],
                mode="lines",
                name="Observed history",
                line={"color": "#0f766e", "width": 2},
            )
        )
        forecast_fig.add_trace(
            go.Scatter(
                x=target_forecast["date"],
                y=target_forecast["forecast"],
                mode="lines",
                name="Forecast",
                line={"color": "#b42318", "width": 2.4, "dash": "dash"},
            )
        )
        forecast_fig.update_layout(xaxis_title="Date", yaxis_title=target)
        st.plotly_chart(plot_layout(forecast_fig), use_container_width=True)

        st.dataframe(
            comparison_df[comparison_df["target"].eq(target)].sort_values(["status", "rmse"]),
            use_container_width=True,
            hide_index=True,
        )

with quality_tab:
    st.subheader("Anomaly Review")
    anomaly_cols = [
        "date",
        "flag_missing_date",
        "flag_stock_interpolated",
        "flag_transfers_gt_cbp_custody",
        "flag_discharges_gt_hhs_care",
        "flag_zero_transfer_ratio",
        "volatility_spike_flag",
        "net_intake_spike_flag",
    ]
    anomalies = filtered[
        filtered[
            [c for c in anomaly_cols if c.startswith("flag_")]
            + ["volatility_spike_flag", "net_intake_spike_flag"]
        ]
        .fillna(False)
        .any(axis=1)
    ][anomaly_cols]
    st.dataframe(anomalies, use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="uac_filtered_capacity_data.csv",
        mime="text/csv",
    )
