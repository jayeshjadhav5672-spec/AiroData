import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -- Page Configuration --
st.set_page_config(
    page_title="AeroData — Airline Operations & Delay Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Global CSS — minimal, enterprise style --
st.markdown(
    """
    <style>
      :root {
        --navy: #0F2742;
        --darker-navy: #0A1A2E;
        --primary: #3E6E9E;
        --light-bg: #F5F7FA;
        --card-bg: #FFFFFF;
        --border: #E2E8F0;
        --text: #1F2937;
        --muted: #5B6B7C;
        --warning: #B7791F;
        --error: #B42318;
        --success: #027A48;
      }

      /* Sidebar */
      [data-testid="stSidebar"] {
        background: var(--navy);
        color: var(--text);
      }
      [data-testid="stSidebar"] .css-1d3flt0 {
        color: var(--muted);
      }
      [data-testid="stSidebar"] hr {
        border-color: var(--border);
      }
      [data-testid="stSidebar"] .css-10trblm {
        font-size: 14px;
        font-weight: 600;
      }

      /* Header */
      .header {
        background: var(--card-bg);
        padding: 0.5rem 1rem;
        margin: -1rem -1rem 1rem -1rem;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .header .logo {
        font-size: 20px;
        font-weight: 700;
        color: var(--navy);
      }
      .header .sub {
        font-size: 12px;
        color: var(--muted);
      }

      /* KPI cards */
      .kpi-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
      }
      .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--navy);
        margin: 0.2rem 0;
      }
      .kpi-label {
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      /* Plotly theme override */
      .js-plotly-atom .tick text {
        fill: var(--muted);
        font-size: 12px;
      }
      .js-plotly-atom .axis-line,
      .js-plotly-atom .grid {
        stroke: var(--border);
      }

      /* Dataframe */
      [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
      }

      /* Filter labels */
      .stSelectbox label,
      .stDateInput label {
        font-weight: 600;
        color: var(--text);
      }

      /* Button */
      .stButton > button {
        background: var(--primary);
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
      }
      .stButton > button:hover {
        background: var(--warning);
        color: var(--navy);
      }

      /* Info badge */
      .badge-synthetic {
        background: #FBBF24;
        color: var(--navy);
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 4px;
        vertical-align: middle;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Session state initialization --
if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "data" not in st.session_state:
    st.session_state.data = None
if "synthetic" not in st.session_state:
    st.session_state.synthetic = True
if "filters" not in st.session_state:
    st.session_state.filters = {}

# -- Helper: synthetic sample data generator --
@st.cache_data
def generate_synthetic_data(n=500):
    np.random.seed(42)
    dates = pd.date_range("2026-09-01", periods=n, freq="D")
    airports = ["JFK", "LHR", "CDG", "DXB", "NRT", "HKG"]
    airlines = ["AA", "BA", "DL", "AF", "CX", "QR"]
    rows = []
    for i in range(n):
        origin = np.random.choice(airports)
        dest = np.random.choice([a for a in airports if a != origin])
        sch_dep = pd.Timestamp(dates[i] + pd.Timedelta(hours=np.random.randint(6, 22)))
        actual_dep = sch_dep + pd.Timedelta(minutes=np.random.randint(-30, 60))
        sch_arr = actual_dep + pd.Timedelta(hours=np.random.randint(2, 12))
        actual_arr = sch_arr + pd.Timedelta(minutes=np.random.randint(-30, 60))
        dep_delay = (actual_dep - sch_dep).seconds // 60
        arr_delay = (actual_arr - sch_arr).seconds // 60
        aircraft = f"Tail-{np.random.randint(100, 999)}"
        status = np.random.choice(["On time", "Delayed", "Cancelled"], p=[0.65, 0.25, 0.10])
        rows.append({
            "flight_id": f"FD{i+100}",
            "date": dates[i].date(),
            "airline": np.random.choice(airlines),
            "origin": origin,
            "destination": dest,
            "sch_dep": sch_dep.time(),
            "act_dep": actual_dep.time(),
            "sch_arr": sch_arr.time(),
            "act_arr": actual_arr.time(),
            "dep_delay": dep_delay,
            "arr_delay": arr_delay,
            "status": status,
            "aircraft": aircraft,
        })
    df = pd.DataFrame(rows)
    df["dep_delay"] = pd.to_numeric(df["dep_delay"])
    df["arr_delay"] = pd.to_numeric(df["arr_delay"])
    return df

# -- KPI computation helpers --
def compute_kpis(df, synthetic):
    total = len(df)
    delayed = int((df["dep_delay"] >= 15) | (df["arr_delay"] >= 15)).sum()
    on_time = int(((df["dep_delay"] > -15) & (df["dep_delay"] < 15)) & (df["arr_delay"] > -15)).sum()
    avg_dep_delay = df["dep_delay"].mean()
    # Departure OTP: eligible flights departing no more than 15 minutes after schedule
    eligible = df[df["dep_delay"].notna()]
    otp = int((eligible["dep_delay"].fillna(0) <= 15).sum())
    otp_rate = otp / len(eligible) * 100 if len(eligible) > 0 else 0
    return {
        "total": total,
        "delayed": delayed,
        "on_time": on_time,
        "avg_dep_delay": round(avg_dep_delay, 1),
        "otp": otp,
        "otp_rate": round(otp_rate, 1),
        "eligible": len(eligible),
        "synthetic": synthetic,
    }

# -- Render sidebar navigation --
def render_sidebar():
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; padding:1rem 0;">
          <div class="logo">AeroData</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(f'<div class="sub">Airline Operations & Delay Analytics</div>', unsafe_allow_html=True)
    st.sidebar.divider()

    cols = st.sidebar.columns([1])
    with cols[0]:
        if st.sidebar.button("Overview", use_container_width=True):
            st.session_state.page = "Overview"
        if st.sidebar.button("Flight Monitoring", use_container_width=True):
            st.session_state.page = "Flight Monitoring"
        if st.sidebar.button("Aircraft Rotation", use_container_width=True):
            st.session_state.page = "Aircraft Rotation"
        if st.sidebar.button("Delay Analysis", use_container_width=True):
            st.session_state.page = "Delay Analysis"
        if st.sidebar.button("Airport Weather", use_container_width=True):
            st.session_state.page = "Airport Weather"
        if st.sidebar.button("Dataset Management", use_container_width=True):
            st.session_state.page = "Dataset Management"
        if st.sidebar.button("Reports", use_container_width=True):
            st.session_state.page = "Reports"

    st.sidebar.divider()
    # Active page highlight

    # Global filter bar
    st.sidebar.markdown("### Global Filters")
    with st.sidebar.expander("Filters", expanded=True):
        data_source = "Synthetic sample data" if st.session_state.synthetic else "Uploaded data"
        st.caption(f"Data source: {data_source}")
        # Date range
        if st.session_state.data is not None:
            min_date = pd.to_datetime(st.session_state.data["date"]).min().date()
            max_date = pd.to_datetime(st.session_state.data["date"]).max().date()
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            st.session_state.filters["date_range"] = date_range
        else:
            st.caption("No data loaded")
        # Airport filter
        if st.session_state.data is not None:
            airports = sorted(st.session_state.data["origin"].unique())
            selected_airports = st.multiselect("Airport", airports, airports)
            st.session_state.filters["airports"] = selected_airports
        else:
            st.caption("No data loaded")
        # Airline filter
        if st.session_state.data is not None:
            airlines = sorted(st.session_state.data["airline"].unique())
            selected_airlines = st.multiselect("Airline", airlines, airlines)
            st.session_state.filters["airlines"] = selected_airlines
        else:
            st.caption("No data loaded")
        # Flight status
        if st.session_state.data is not None:
            statuses = ["All", "On time", "Delayed", "Cancelled"]
            selected_status = st.radio("Status", statuses, horizontal=True)
            st.session_state.filters["status"] = selected_status
        else:
            st.caption("No data loaded")
        # Delay threshold
        st.session_state.filters["delay_threshold"] = st.slider("Delay threshold (min)", 0, 120, 15)
    st.sidebar.divider()
    st.sidebar.caption("AeroData v0.1.0")

# -- Page: Overview --
def render_overview():
    st.title("Overview")
    st.markdown("Airline Operations & Delay Analytics")

    # Load data if not loaded
    if st.session_state.data is None:
        with st.spinner("Generating synthetic sample data..."):
            df = generate_synthetic_data(n=500)
            st.session_state.data = df
            st.session_state.synthetic = True

    kpis = compute_kpis(st.session_state.data, st.session_state.synthetic)
    df = st.session_state.data

    # Apply filters
    daterange = st.session_state.filters.get("date_range", (df["date"].min(), df["date"].max()))
    masks = (df["date"] >= daterange[0]) & (df["date"] <= daterange[1])
    if st.session_state.filters.get("airports"):
        masks &= df["origin"].isin(st.session_state.filters["airports"])
    if st.session_state.filters.get("airlines"):
        masks &= df["airline"].isin(st.session_state.filters["airlines"])
    if st.session_state.filters.get("status") != "All":
        masks &= df["status"] == st.session_state.filters["status"]
    threshold = st.session_state.filters.get("delay_threshold", 15)
    masks &= ((df["dep_delay"] >= threshold) | (df["arr_delay"] >= threshold))

    filtered = df[masks]

    # KPI row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis["total"]}</div><div class="kpi-label">Total flights analysed</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis["delayed"]}</div><div class="kpi-label">Delayed flights</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis["on_time"]}</div><div class="kpi-label">On-time departures</div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis["avg_dep_delay"]}</div><div class="kpi-label">Avg departure delay (min)</div></div>', unsafe_allow_html=True)

    # Trend chart: daily departure and arrival delay
    st.markdown("### Daily departure and arrival delay trend")
    daily = filtered.groupby("date").agg(
        avg_dep=("dep_delay", "mean"),
        avg_arr=("arr_delay", "mean"),
        count=("flight_id", "count"),
    ).reset_index()
    fig_trend = px.line(
        daily, x="date", y=["avg_dep", "avg_arr"],
        labels={"value": "delay (min)", "variable": "measure", "date": "date"},
        markers=True,
    )
    fig_trend.update_layout(
        legend_title_text="Measure",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Average delay by airport
    st.markdown("### Average delay by airport")
    dep_by_airport = filtered.groupby("origin").agg(
        avg_dep=("dep_delay", "mean"),
        n=("flight_id", "count"),
    ).reset_index()
    arr_by_airport = filtered.groupby("destination").agg(
        avg_arr=("arr_delay", "mean"),
        n=("flight_id", "count"),
    ).reset_index()
    airport_delays = dep_by_airport.merge(arr_by_airport, left_on="origin", right_on="destination", suffixes=("_dep", "_arr"))
    airport_delays = airport_delays.rename(columns={"origin": "airport"})
    fig_airport = px.bar(
        airport_delays.head(10), x="airport", y=["avg_dep", "avg_arr"],
        labels={"value": "delay (min)", "variable": "measure", "airport": "airport"},
        text_auto=".2f",
    )
    fig_airport.update_layout(showlegend=True, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_airport, use_container_width=True)

    # Recent delayed flights
    st.markdown("### Recent delayed flights")
    delayed_flights = filtered[filtered["dep_delay"] >= threshold or filtered["arr_delay"] >= threshold].sort_values("date", ascending=False).head(10)
    if len(delayed_flights) > 0:
        disp = delayed_flights[["flight_id", "date", "airline", "origin", "destination", "sch_dep", "act_dep", "dep_delay", "arr_delay", "status"]].copy()
        disp.columns = ["Flight", "Date", "Airline", "Origin", "Destination", "STD", "ATD", "Dep Delay", "Arr Delay", "Status"]
        st.dataframe(disp, hide_index=True, use_container_width=True)
    else:
        st.info("No delayed flights match the current filters.")

    # Data quality and coverage panel
    st.markdown("### Data quality and coverage")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Records", len(filtered))
        if st.session_state.synthetic:
            st.caption("Synthetic sample data — not for operational decisions.")
    with c2:
        missing_dep = filtered["act_dep"].isna().sum()
        st.metric("Missing actual departure", missing_dep)
        if missing_dep > 0:
            st.caption("Excluded from departure-delay and OTP measures.")

    # Synthetic disclaimer at bottom
    st.divider()
    if st.session_state.synthetic:
        st.caption(
            "Synthetic sample data — these records do not represent real flights, aircraft, or airlines. "
            "Do not use sample figures for operational decisions."
        )

# -- Page stubs for remaining pages (will be fleshed out in later stages) --
def render_flight_monitoring():
    st.title("Flight Monitoring")
    st.info("Page under construction — Stage 3 implementation pending approval.")

def render_aircraft_rotation():
    st.title("Aircraft Rotation")
    st.info("Page under construction — Stage 4 implementation pending approval.")

def render_delay_analysis():
    st.title("Delay Analysis")
    st.info("Page under construction — Stage 5 implementation pending approval.")

def render_airport_weather():
    st.title("Airport Weather")
    st.info("Page under construction — Stage 6 implementation pending approval.")

def render_dataset_management():
    st.title("Dataset Management")
    st.info("Page under construction — Stage 7 implementation pending approval.")

def render_reports():
    st.title("Reports")
    st.info("Page under construction — Stage 8 implementation pending approval.")

# -- Main app shell --
def main():
    render_sidebar()

    page = st.session_state.page
    #st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.rerun()

    # Route to page
    if page == "Overview":
        render_overview()
    elif page == "Flight Monitoring":
        render_flight_monitoring()
    elif page == "Aircraft Rotation":
        render_aircraft_rotation()
    elif page == "Delay Analysis":
        render_delay_analysis()
    elif page == "Airport Weather":
        render_airport_weather()
    elif page == "Dataset Management":
        render_dataset_management()
    elif page == "Reports":
        render_reports()

if __name__ == "__main__":
    main()