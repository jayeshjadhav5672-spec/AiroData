from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.data_pipeline import process_sources
from backend.database import get_metadata, load_processed, query_flights, save_processed
from backend.report_generator import build_analytical_pdf


ROOT = Path(__file__).parent
DATA = ROOT / "data"
DB_PATH = ROOT / "database" / "airline.db"
NAVY = "#0F2742"
BLUE = "#3E6E9E"
BG = "#F5F7FA"
BORDER = "#E2E8F0"
TEXT = "#1F2937"
PAGES = ["Overview", "Flight Operations", "Aircraft Turnaround", "Delay Propagation", "Weather Analysis", "Dataset Management", "Reports & Insights"]
DELAY_THRESHOLD_MIN = 15

st.set_page_config(page_title="AeroData | Airline Operations & Delay Analytics", page_icon="◫", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:Inter,system-ui,sans-serif;color:{TEXT}}}
.stApp{{background:{BG}}} section[data-testid="stSidebar"]{{background:{NAVY}}} section[data-testid="stSidebar"] *{{color:#fff!important}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{{padding:7px 10px;border-radius:6px}}
.block-container{{padding-top:1.6rem;max-width:1600px}}
.kpi{{background:#fff;border:1px solid {BORDER};border-radius:8px;padding:15px 17px;min-height:104px}}
.kpi-label{{font-size:12px;color:#5B6B7C;margin-bottom:9px}} .kpi-value{{font-size:27px;font-weight:700;color:{NAVY}}}
.kpi-note{{font-size:11px;color:#64748b;margin-top:5px}}
h1{{font-size:27px!important;color:{NAVY}!important}} h2{{font-size:18px!important;color:{NAVY}!important}}
</style>""", unsafe_allow_html=True)


def _read_sample() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    schedule = pd.read_csv(DATA / "flight_schedule.csv")
    actuals = pd.read_csv(DATA / "flight_actuals.csv")
    weather = pd.read_csv(DATA / "weather.csv")
    codes = pd.read_csv(DATA / "delay_codes.csv")
    return schedule, actuals, weather, codes


def use_sample_data() -> None:
    schedule, actuals, weather, codes = _read_sample()
    result = process_sources(schedule, actuals, weather, codes)
    save_processed(result, DB_PATH, "Synthetic sample data", {"schedule": "flight_schedule.csv", "actuals": "flight_actuals.csv", "weather": "weather.csv", "delay codes": "delay_codes.csv"})
    st.session_state.data_source = "Synthetic sample data"
    st.session_state.source_files = "Bundled synthetic sample files"
    st.session_state.pop("original_uploads", None)


def ensure_database() -> None:
    tables = load_processed(DB_PATH)
    if not DB_PATH.exists() or tables["flights"].empty:
        use_sample_data()


ensure_database()
tables = load_processed(DB_PATH)
meta = get_metadata(DB_PATH)
all_flights = tables["flights"]
all_rotations = tables["rotations"]
all_weather = tables["weather"]
all_codes = tables["delay_codes"]
all_issues = tables["issues"]
data_source = meta.get("source", st.session_state.get("data_source", "Synthetic sample data"))
source_files = meta.get("source_files", "Bundled synthetic sample files")

if all_flights.empty:
    st.error("No processed flights are available. Load the synthetic sample data or process flight schedule and actuals CSV files.")
    st.stop()

valid_flight_dates = all_flights.flight_date.dropna()
if valid_flight_dates.empty:
    st.error("Processed flight records have no valid service dates. Review the date issues in Dataset Management.")
    st.stop()
min_date = valid_flight_dates.min().date()
max_date = valid_flight_dates.max().date()

with st.sidebar:
    st.markdown("## ◫ AeroData")
    st.caption("AIRLINE OPERATIONS & DELAY ANALYTICS")
    st.divider()
    page = st.radio("NAVIGATION", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("DATA SOURCE")
    st.markdown(f"**{escape(data_source)}**")
    st.caption("Synthetic sample data — not for operational decisions" if "Synthetic" in data_source else "Uploaded data — not verified against an airline source")
    st.caption(f"{len(all_flights):,} processed flight legs")

with st.container():
    c1, c2, c3 = st.columns([1, 1.2, 2])
    with c1:
        st.markdown("**Date range**")
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date, label_visibility="collapsed")
    with c2:
        airport_options = sorted(set(all_flights.origin.dropna().astype(str)) | set(all_flights.destination.dropna().astype(str)))
        st.markdown("**Airport filter**")
        scope_airport = st.selectbox("Airport filter", ["All airports", *airport_options], label_visibility="collapsed")
    with c3:
        st.markdown("**Definitions & limitations**")
        st.caption("Departure OTP uses a 15-minute threshold. Delay propagation and weather results describe associations, not proven causes.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    flights = query_flights(DB_PATH, str(date_range[0]), str(date_range[1]), None if scope_airport == "All airports" else scope_airport)
else:
    flights = all_flights.copy()
    if isinstance(date_range, tuple) and len(date_range) == 1:
        flights = flights[flights.flight_date.dt.date.eq(date_range[0])]
    if scope_airport != "All airports":
        flights = flights[flights.origin.eq(scope_airport) | flights.destination.eq(scope_airport)]

if flights.empty:
    st.info("No flights in this date range. Choose a wider range or check the dataset.")
    if page == "Dataset Management":
        flights = all_flights.copy()
    else:
        st.stop()

visible_keys = set(flights.flight_key.dropna().astype(str)) if "flight_key" in flights else set()
rotations = all_rotations.copy()
if not rotations.empty:
    rotations = rotations[rotations.previous_flight_key.astype(str).isin(visible_keys) & rotations.next_flight_key.astype(str).isin(visible_keys)].copy()


def safe_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(bool)


def kpis(items: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{escape(label)}</div><div class="kpi-value">{escape(value)}</div><div class="kpi-note">{escape(note)}</div></div>', unsafe_allow_html=True)


def chart(fig) -> None:
    fig.update_layout(margin=dict(l=10, r=10, t=35, b=10), paper_bgcolor="white", plot_bgcolor="white", font=dict(family="Inter", color=TEXT), legend_title_text="", height=330)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EEF2F6")
    st.plotly_chart(fig, use_container_width=True)


def delay_label(value: float) -> str:
    return "Not available" if pd.isna(value) else f"{value:+.1f} min"


def fmt_pct(value: float) -> str:
    return "Not available" if pd.isna(value) else f"{value:.1f}%"


def csv_button(label: str, frame: pd.DataFrame, filename: str, key: str) -> None:
    st.download_button(label, frame.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv", key=key, disabled=frame.empty)


def enrich_rotations(rotation_frame: pd.DataFrame) -> pd.DataFrame:
    if rotation_frame.empty:
        return rotation_frame.copy()
    lookup = all_flights.set_index("flight_key")
    result = rotation_frame.copy()
    for col, key_col in [("previous_scheduled_arrival", "previous_flight_key"), ("previous_actual_arrival", "previous_flight_key"), ("next_scheduled_departure", "next_flight_key"), ("next_actual_departure", "next_flight_key"), ("previous_origin", "previous_flight_key"), ("previous_destination", "previous_flight_key"), ("next_origin", "next_flight_key"), ("next_destination", "next_flight_key")]:
        target = {"previous_scheduled_arrival": "scheduled_arrival", "previous_actual_arrival": "actual_arrival", "next_scheduled_departure": "scheduled_departure", "next_actual_departure": "actual_departure", "previous_origin": "origin", "previous_destination": "destination", "next_origin": "origin", "next_destination": "destination"}[col]
        if target in lookup:
            result[col] = result[key_col].map(lookup[target])
    return result


if page == "Overview":
    st.title("Overview")
    st.caption("Flight volume, departure punctuality, and possible delay carry-over for the current selection.")
    delayed_mask = safe_bool(flights.delayed)
    eligible_mask = safe_bool(flights.otp_eligible)
    ontime = safe_bool(flights.on_time_departure)
    otp = ontime[eligible_mask].mean() * 100 if eligible_mask.any() else np.nan
    dep = pd.to_numeric(flights.departure_delay_min, errors="coerce")
    arr = pd.to_numeric(flights.arrival_delay_min, errors="coerce")
    rotation_eligible = safe_bool(rotations.eligible) if not rotations.empty else pd.Series(dtype=bool)
    rotation_affected = safe_bool(rotations.potentially_affected) if not rotations.empty else pd.Series(dtype=bool)
    prop_rate = rotation_affected[rotation_eligible].mean() * 100 if rotation_eligible.any() else np.nan
    affected_connections = int(rotation_affected[rotation_eligible].sum()) if rotation_eligible.any() else 0
    eligible_connections = int(rotation_eligible.sum()) if rotation_eligible.any() else 0
    kpis([
        ("FLIGHTS ANALYSED", f"{len(flights):,}", "Records in selected date range"),
        ("DELAYED FLIGHTS", f"{int(delayed_mask.sum()):,}", f"Departure or arrival ≥ {DELAY_THRESHOLD_MIN} min"),
        ("DEPARTURE OTP", fmt_pct(otp), f"{int(eligible_mask.sum()):,} eligible flights · ≤15 min"),
        ("PROPAGATION RATE", fmt_pct(prop_rate), f"{int(rotation_eligible.sum()):,} eligible connections"),
        ("AVG DEPARTURE DELAY", delay_label(dep.mean()), f"Mean · {int(dep.notna().sum()):,} flights with data"),
    ])
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Departure vs arrival delay trend")
        trend = flights.groupby(flights.flight_date.dt.date)[["departure_delay_min", "arrival_delay_min"]].mean().reset_index(names="flight_date")
        trend = trend.melt("flight_date", var_name="measure", value_name="delay_min")
        chart(px.line(trend, x="flight_date", y="delay_min", color="measure", markers=True, labels={"flight_date": "Flight date", "delay_min": "Average delay (min)", "measure": "Measure"}))
    with right:
        st.subheader("Flight status distribution")
        statuses = flights.status.fillna("Unknown").value_counts().rename_axis("status").reset_index(name="flights")
        chart(px.pie(statuses, names="status", values="flights", hole=0.58))
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Average delay by airport")
        airport_delays = flights.groupby("origin").agg(avg_departure_delay=("departure_delay_min", "mean"), avg_arrival_delay=("arrival_delay_min", "mean"), flights=("flight_id", "count")).reset_index()
        long = airport_delays.melt(id_vars=["origin", "flights"], value_vars=["avg_departure_delay", "avg_arrival_delay"], var_name="measure", value_name="delay_min")
        chart(px.bar(long, x="origin", y="delay_min", color="measure", barmode="group", hover_data=["flights"], labels={"origin": "Origin airport", "delay_min": "Average delay (min)", "measure": "Measure"}))
    with right:
        st.subheader("Recent delayed flights")
        recent = flights[delayed_mask].sort_values("departure_delay_min", ascending=False).head(12)
        st.dataframe(recent[["flight_id", "flight_date", "origin", "destination", "departure_delay_min", "arrival_delay_min", "status"]], hide_index=True, use_container_width=True)
    st.caption("OTP is departure-based. A late flight following an aircraft-linked delay indicates possible association, not proof of causation.")

elif page == "Flight Operations":
    st.title("Flight Operations")
    st.caption("Search, filter, and inspect schedule and actual data for individual flight legs.")
    q = st.text_input("Search flight ID, aircraft, airport, or route")
    airports = sorted(set(flights.origin.dropna().astype(str)) | set(flights.destination.dropna().astype(str)))
    c1, c2 = st.columns(2)
    with c1:
        airport = st.selectbox("Airport", ["All airports", *airports])
    with c2:
        status_options = sorted(flights.status.fillna("Unknown").astype(str).unique())
        status_selected = st.multiselect("Flight status", status_options, default=status_options)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        view = query_flights(DB_PATH, str(date_range[0]), str(date_range[1]), None if airport == "All airports" else airport, None, q or None)
    else:
        view = flights.copy()
        if q:
            view = view[view.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)]
        if airport != "All airports":
            view = view[view.origin.eq(airport) | view.destination.eq(airport)]
    view = view[view.status.fillna("Unknown").isin(status_selected)]
    delayed_view = safe_bool(view.delayed)
    eligible_view = safe_bool(view.otp_eligible)
    ontime_view = safe_bool(view.on_time_departure)
    otp_view = ontime_view[eligible_view].mean() * 100 if eligible_view.any() else np.nan
    kpis([
        ("SCHEDULED FLIGHTS", f"{len(view):,}", "Selected records"),
        ("COMPLETED DEPARTURES", f"{int(view.actual_departure.notna().sum()):,}", "Valid actual departure"),
        ("DELAYED FLIGHTS", f"{int(delayed_view.sum()):,}", "At least one delay ≥15 min"),
        ("DEPARTURE OTP", fmt_pct(otp_view), f"{int(eligible_view.sum()):,} eligible flights"),
    ])
    left, right = st.columns(2)
    with left:
        st.subheader("Flight status distribution")
        counts = view.status.fillna("Unknown").value_counts().rename_axis("status").reset_index(name="flights")
        chart(px.bar(counts, x="status", y="flights", color="status", labels={"status": "Status", "flights": "Flights"}))
    with right:
        st.subheader("Hourly departures vs delays")
        hourly = view.assign(hour=view.scheduled_departure.dt.hour).groupby("hour").agg(departures=("flight_id", "count"), delayed_flights=("delayed", "sum")).reset_index()
        long = hourly.melt("hour", var_name="measure", value_name="flights")
        chart(px.bar(long, x="hour", y="flights", color="measure", barmode="group", labels={"hour": "Scheduled departure hour (local as recorded)", "flights": "Flights", "measure": "Measure"}))
    st.subheader("Flight records")
    cols = ["flight_id", "flight_date", "airline", "origin", "destination", "aircraft_id", "scheduled_departure", "actual_departure", "departure_delay_min", "scheduled_arrival", "actual_arrival", "arrival_delay_min", "status", "delay_code", "delay_reason"]
    cols = [col for col in cols if col in view.columns]
    st.dataframe(view[cols].sort_values("scheduled_departure"), hide_index=True, use_container_width=True)
    if not view.empty:
        selected = st.selectbox("Inspect a flight", view.flight_key.astype(str).tolist())
        record = view[view.flight_key.astype(str).eq(selected)].iloc[0]
        with st.expander("Flight detail"):
            st.json({key: (None if pd.isna(value) else str(value) if isinstance(value, (pd.Timestamp, pd.Timedelta)) else value) for key, value in record.items() if not key.startswith("_")})
    csv_button("Export filtered flights (CSV)", view, "aerodata_flights.csv", "ops-csv")
    st.caption("Departure OTP uses valid scheduled and actual departure times; cancelled flights and missing actual departures are excluded. Unknown status is never treated as on time.")

    st.title("Flight Monitoring")
    st.caption("Inspect scheduled and actual flight operations for the current selection.")
    # Synthetic data disclaimer
    if "Synthetic" in data_source:
        st.caption("Synthetic sample data — not for operational decisions.")
    
    # --- Search and filters ---
    st.markdown("### Filters")
    c1, c2, c3 = st.columns(3)
    with c1:
        search_query = st.text_input("Search flight number or airline")
    with c2:
        airport_options = sorted(set(flights.origin.dropna().astype(str)) | set(flights.destination.dropna().astype(str)))
        selected_airport = st.selectbox("Origin airport", ["All airports", *airport_options])
    with c3:
        selected_destination = st.selectbox("Destination airport", ["All destinations"] + [d for d in airport_options if d != selected_airport])
    
    # Date range filter (already in session state)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_mask = (flights.flight_date >= pd.Timestamp(date_range[0])) & (flights.flight_date <= pd.Timestamp(date_range[1]))
    else:
        date_mask = pd.Series(True, index=flights.index)
    
    # Airline filter
    airline_options = sorted(flights.airline.dropna().unique()) if "airline" in flights.columns else []
    selected_airline = st.multiselect("Airline", airline_options, default=airline_options)
    
    # Status filter
    status_options = sorted(flights.status.dropna().unique()) if "status" in flights.columns else []
    selected_status = st.multiselect("Flight status", status_options, default=status_options)
    
    # Delay threshold
    delay_threshold = st.slider("Delay threshold (min)", 0, 120, DELAY_THRESHOLD_MIN)
    
    # Apply filters
    mask = date_mask.copy()
    if selected_airport != "All airports":
        mask &= flights.origin.astype(str) == selected_airport
    if selected_destination != "All destinations":
        mask &= flights.destination.astype(str) == selected_destination
    if selected_airline:
        mask &= flights.airline.isin(selected_airline)
    if selected_status:
        mask &= flights.status.fillna("Unknown").isin(selected_status)
    
    filtered = flights[mask].copy()
    
    # Calculate delays
    if "scheduled_departure" in filtered.columns and "actual_departure" in filtered.columns:
        filtered["departure_delay_min"] = pd.to_numeric(filtered["actual_departure"], errors="coerce") - pd.to_numeric(filtered["scheduled_departure"], errors="coerce")
    else:
        filtered["departure_delay_min"] = pd.NA
    
    if "scheduled_arrival" in filtered.columns and "actual_arrival" in filtered.columns:
        filtered["arrival_delay_min"] = pd.to_numeric(filtered["actual_arrival"], errors="coerce") - pd.to_numeric(filtered["scheduled_arrival"], errors="coerce")
    else:
        filtered["arrival_delay_min"] = pd.NA
    
    # KPI row
    total = len(filtered)
    delayed = int((filtered["departure_delay_min"] >= delay_threshold) | (filtered["arrival_delay_min"] >= delay_threshold)).sum() if "departure_delay_min" in filtered.columns and "arrival_delay_min" in filtered.columns else 0
    on_time = int((filtered["departure_delay_min"] > -delay_threshold) & (filtered["departure_delay_min"] < delay_threshold) & (filtered["arrival_delay_min"] > -delay_threshold) & (filtered["arrival_delay_min"] < delay_threshold)).sum() if "departure_delay_min" in filtered.columns and "arrival_delay_min" in filtered.columns else 0
    eligible = filtered["departure_delay_min"].notna().sum() if "departure_delay_min" in filtered.columns else 0
    otp = int((filtered["departure_delay_min"] <= delay_threshold).sum()) if "departure_delay_min" in filtered.columns else 0
    otp_rate = otp / eligible * 100 if eligible > 0 else np.nan
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Flights analysed", f"{total:,}")
    with k2:
        st.metric("Delayed flights", f"{delayed:,}", f"Delay ≥ {delay_threshold} min")
    with k3:
        st.metric("On-time flights", f"{on_time:,}")
    with k4:
        if np.isnan(otp_rate):
            st.metric("Departure OTP", "N/A")
        else:
            st.metric("Departure OTP", fmt_pct(otp_rate), f"{int(eligible):,} eligible flights")
    
    # Flight operations table
    st.subheader("Flight operations table")
    
    table_cols = ["flight_id", "flight_date", "airline", "origin", "destination", "scheduled_departure", "actual_departure", "departure_delay_min", "scheduled_arrival", "actual_arrival", "arrival_delay_min", "status"]
    table_cols = [col for col in table_cols if col in filtered.columns]
    
    # Format the table
    display = filtered[table_cols].copy()
    display.columns = [col.replace("_", " ").title() for col in display.columns]
    
    # Format delay columns
    if "Departure Delay" in display.columns:
        display["Departure Delay"] = display["Departure Delay"].apply(delay_label)
    if "Arrival Delay" in display.columns:
        display["Arrival Delay"] = display["Arrival Delay"].apply(delay_label)
    
    st.dataframe(display.sort_values("Scheduled Departure"), hide_index=True, use_container_width=True)
    
    # Flight details
    if not filtered.empty:
        st.subheader("Flight detail")
        selected_flight = st.selectbox("Inspect a flight", filtered.flight_id.astype(str).tolist())
        record = filtered[filtered.flight_id.astype(str).eq(selected_flight)].iloc[0]
        with st.expander("Flight detail"):
            details = {}
            for key in record.index:
                value = record[key]
                if pd.isna(value):
                    details[key] = "Not available"
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    details[key] = str(value)
                else:
                    details[key] = value
            st.json(details)
    
    # Status summary
    st.subheader("Flight status summary")
    status_counts = filtered.status.fillna("Unknown").value_counts()
    chart_data = pd.DataFrame({"Status": status_counts.index, "Flights": status_counts.values})
    chart(px.pie(chart_data, names="Status", values="Flights", hole=0.58))
    
    st.caption("Departure delay = actual departure minus scheduled departure. Arrival delay = actual arrival minus scheduled arrival. Positive values are late; negative values are early. Missing actual times are shown as Not available, not zero.")
elif page == "Aircraft Turnaround":
    st.title("Aircraft Turnaround")
    st.caption("Explore scheduled and actual ground time between successive legs assigned to the same aircraft.")
    if rotations.empty:
        st.info("No aircraft sequences are available for this date range.")
    else:
        view = enrich_rotations(rotations)
        aircraft_options = sorted(view.aircraft_id.dropna().astype(str).unique())
        chosen_aircraft = st.selectbox("Aircraft (tail number)", ["All aircraft", *aircraft_options])
        if chosen_aircraft != "All aircraft":
            view = view[view.aircraft_id.eq(chosen_aircraft)]
        tolerance = st.number_input("On-time turnaround tolerance above schedule (minutes)", min_value=0, max_value=240, value=15, step=5, help="A turnaround is on time if its actual ground time is no more than this many minutes longer than its scheduled ground time.")
        valid = view[view.link_status.eq("Confirmed") & view.actual_turnaround_min.notna() & view.scheduled_turnaround_min.notna() & view.actual_turnaround_min.ge(0) & view.scheduled_turnaround_min.ge(0)].copy()
        valid["variance_min"] = valid.actual_turnaround_min - valid.scheduled_turnaround_min
        on_time_turn = valid.variance_min.le(tolerance)
        delayed_turn = valid.variance_min.gt(tolerance)
        avg_turn = valid.actual_turnaround_min.mean() if not valid.empty else np.nan
        on_time_rate = on_time_turn.mean() * 100 if len(valid) else np.nan
        delayed_rate = delayed_turn.mean() * 100 if len(valid) else np.nan
        kpis([
            ("TURNAROUNDS ANALYSED", f"{len(valid):,}", "Confirmed pairs with required times"),
            ("AVERAGE ACTUAL TURNAROUND", delay_label(avg_turn), f"{len(valid):,} eligible turnarounds"),
            ("ON-TIME TURNAROUND", fmt_pct(on_time_rate), f"{int(on_time_turn.sum()):,} of {len(valid):,} · tolerance +{tolerance} min"),
            ("DELAYED TURNAROUND", fmt_pct(delayed_rate), f"{int(delayed_turn.sum()):,} of {len(valid):,} · tolerance +{tolerance} min"),
        ])
        left, right = st.columns(2)
        with left:
            st.subheader("Turnaround time distribution")
            chart(px.histogram(valid, x="actual_turnaround_min", nbins=18, labels={"actual_turnaround_min": "Actual turnaround (min)", "count": "Connections"}))
        with right:
            st.subheader("Average turnaround by airport")
            airport_turn = valid.groupby("airport").actual_turnaround_min.mean().reset_index(name="average_turnaround_min")
            chart(px.bar(airport_turn, x="airport", y="average_turnaround_min", labels={"airport": "Airport", "average_turnaround_min": "Average actual turnaround (min)"}))
        st.subheader("Aircraft rotation details")
        st.dataframe(view[["aircraft_id", "previous_flight_id", "previous_scheduled_arrival", "previous_actual_arrival", "next_flight_id", "next_scheduled_departure", "next_actual_departure", "airport", "scheduled_turnaround_min", "actual_turnaround_min", "previous_arrival_delay_min", "next_departure_delay_min", "link_status", "eligible"]], hide_index=True, use_container_width=True)
        csv_button("Export turnaround records (CSV)", view, "aerodata_turnarounds.csv", "turn-csv")
        st.caption("On-time turnaround tolerance is editable and is not an industry standard. Unconfirmed pairs are visible but excluded from confirmed-link rates.")

elif page == "Delay Propagation":
    st.title("Delay Propagation")
    st.caption("Explore whether a late arrival was followed by a late departure on the same aircraft.")
    st.info("Association, not proof of causation. Crew, maintenance, weather, air traffic control, boarding, and other factors may contribute.")
    c1, c2 = st.columns(2)
    with c1:
        arrival_threshold = st.number_input("Previous arrival delay threshold (min)", min_value=1, max_value=360, value=15)
    with c2:
        departure_threshold = st.number_input("Next departure delay threshold (min)", min_value=1, max_value=360, value=15)
    if rotations.empty:
        st.info("No aircraft-linked connections are available for this date range.")
    else:
        view = enrich_rotations(rotations)
        aircraft_choices = sorted(view.aircraft_id.dropna().astype(str).unique())
        aircraft_filter = st.selectbox("Aircraft (tail number)", ["All aircraft", *aircraft_choices])
        if aircraft_filter != "All aircraft":
            view = view[view.aircraft_id.eq(aircraft_filter)]
        min_ground = st.number_input("Minimum actual ground time (min)", min_value=0, max_value=600, value=30)
        link_view = st.selectbox("Aircraft link confidence", ["Confirmed only", "Include unconfirmed links"])
        if link_view == "Confirmed only":
            view = view[view.link_status.eq("Confirmed")]
        else:
            st.warning("Unconfirmed links are included in this view and its eligible-connection denominator. Treat the resulting rate as less certain.")
        view = view[view.actual_turnaround_min.ge(min_ground) & view.actual_turnaround_min.le(900)].copy()
        required = view.previous_arrival_delay_min.notna() & view.next_departure_delay_min.notna()
        eligible = view[required].copy()
        eligible["previous_arrived_late"] = eligible.previous_arrival_delay_min.ge(arrival_threshold)
        eligible["next_departed_late"] = eligible.next_departure_delay_min.ge(departure_threshold)
        eligible["potentially_affected"] = eligible.previous_arrived_late & eligible.next_departed_late
        affected = eligible[eligible.potentially_affected]
        rate = len(affected) / len(eligible) * 100 if len(eligible) else np.nan
        avg_propagated = affected.next_departure_delay_min.mean() if not affected.empty else np.nan
        kpis([
            ("ELIGIBLE CONNECTIONS", f"{len(eligible):,}", "Confirmed aircraft-linked pairs with required times"),
            ("PREVIOUS FLIGHT ARRIVED LATE", f"{int(eligible.previous_arrived_late.sum()):,}", f"≥{arrival_threshold} min of {len(eligible):,}"),
            ("POTENTIALLY AFFECTED", f"{len(affected):,}", f"Next departure ≥{departure_threshold} min late"),
            ("DELAY-PROPAGATION RATE", fmt_pct(rate), f"{len(affected):,} of {len(eligible):,} eligible connections"),
            ("AVG NEXT DEPARTURE DELAY", delay_label(avg_propagated), f"{len(affected):,} potentially affected connections"),
        ])
        left, right = st.columns(2)
        with left:
            st.subheader("Previous arrival vs next departure delay")
            fig = px.scatter(eligible, x="previous_arrival_delay_min", y="next_departure_delay_min", color="potentially_affected", hover_data=["aircraft_id", "previous_flight_id", "next_flight_id", "actual_turnaround_min"], labels={"previous_arrival_delay_min": "Previous arrival delay (min)", "next_departure_delay_min": "Next departure delay (min)", "potentially_affected": "Potentially affected"})
            fig.add_vline(x=arrival_threshold, line_dash="dash", line_color=BLUE)
            fig.add_hline(y=departure_threshold, line_dash="dash", line_color=BLUE)
            chart(fig)
        with right:
            st.subheader("Potentially affected by airport")
            by_airport = eligible.groupby("airport").agg(rate=("potentially_affected", "mean"), eligible_connections=("potentially_affected", "size")).reset_index()
            by_airport["rate"] *= 100
            chart(px.bar(by_airport, x="airport", y="rate", text="eligible_connections", labels={"airport": "Connection airport", "rate": "Potentially affected (%)", "eligible_connections": "Eligible connections"}))
        st.subheader("Delay flow across aircraft-linked connections")
        flow_data = eligible.assign(
            previous_state=np.where(eligible.previous_arrival_delay_min.ge(arrival_threshold), "Previous arrival: late", "Previous arrival: below threshold"),
            next_state=np.where(eligible.next_departure_delay_min.ge(departure_threshold), "Next departure: late", "Next departure: below threshold"),
        ).groupby(["previous_state", "next_state"]).size().reset_index(name="connections")
        node_labels = ["Previous arrival: below threshold", "Previous arrival: late", "Next departure: below threshold", "Next departure: late"]
        node_ids = {label: index for index, label in enumerate(node_labels)}
        flow_fig = go.Figure(go.Sankey(
            node={"label": node_labels, "color": ["#8FA3B8", BLUE, "#8FA3B8", NAVY], "pad": 18, "thickness": 17},
            link={"source": [node_ids[value] for value in flow_data.previous_state], "target": [node_ids[value] for value in flow_data.next_state], "value": flow_data.connections.tolist(), "color": "rgba(62,110,158,0.32)"},
        ))
        flow_fig.update_layout(height=300, margin=dict(l=10, r=10, t=15, b=10), paper_bgcolor="white", font=dict(family="Inter", color=TEXT))
        chart(flow_fig)
        st.subheader("Potentially affected connections by flight-sequence hop")
        by_hop = eligible.groupby("connection_hop").agg(rate=("potentially_affected", "mean"), eligible_connections=("potentially_affected", "size")).reset_index()
        by_hop["rate"] *= 100
        chart(px.bar(by_hop, x="connection_hop", y="rate", text="eligible_connections", labels={"connection_hop": "Connection hop in aircraft sequence", "rate": "Potentially affected (%)", "eligible_connections": "Eligible connections"}))
        st.subheader("Aircraft-linked connection records")
        st.dataframe(eligible[["aircraft_id", "connection_hop", "previous_flight_id", "previous_scheduled_arrival", "previous_actual_arrival", "previous_arrival_delay_min", "actual_turnaround_min", "next_flight_id", "next_scheduled_departure", "next_actual_departure", "next_departure_delay_min", "link_status", "potentially_affected"]], hide_index=True, use_container_width=True)
        csv_button("Export eligible connections (CSV)", eligible, "aerodata_connections.csv", "prop-csv")
        st.caption("The rate is potentially affected connections ÷ eligible connections. A matching aircraft ID and timing pattern do not prove the earlier flight caused the later delay.")

elif page == "Weather Analysis":
    st.title("Weather Analysis")
    st.caption("Review recorded weather conditions that overlap with flight delays; this page does not establish cause.")
    condition_options = sorted(flights.weather_condition.dropna().astype(str).unique())
    selected_conditions = st.multiselect("Weather condition", condition_options, default=condition_options)
    weather_matched_all = flights.weather_condition.notna()
    all_matched = flights[weather_matched_all].copy()
    matched = all_matched.copy()
    if selected_conditions:
        matched = matched[matched.weather_condition.isin(selected_conditions)]
    else:
        matched = matched.iloc[0:0]
    delayed = safe_bool(flights.delayed)
    delayed_with_weather = matched[delayed.loc[matched.index]].copy()
    total_delayed = int(delayed.sum())
    share_delays = len(delayed_with_weather) / total_delayed * 100 if total_delayed else np.nan
    avg_matched = pd.to_numeric(all_matched.departure_delay_min, errors="coerce").mean() if not all_matched.empty else np.nan
    coverage = len(all_matched) / len(flights) * 100 if len(flights) else np.nan
    kpis([
        ("WEATHER-MATCHED FLIGHTS", f"{len(all_matched):,} of {len(flights):,}", f"{fmt_pct(coverage)} coverage"),
        ("DELAYED FLIGHTS WITH WEATHER", f"{len(delayed_with_weather):,}", "Weather overlap, not attribution"),
        ("SHARE OF ALL DELAYS", fmt_pct(share_delays), f"{len(delayed_with_weather):,} of {total_delayed:,} delayed flights"),
        ("AVG DEPARTURE DELAY WITH WEATHER", delay_label(avg_matched), f"{int(matched.departure_delay_min.notna().sum()):,} matched flights with data"),
        ("MISSING WEATHER", f"{int((~weather_matched_all).sum()):,}", "Not classified as clear"),
    ])
    st.info("Weather overlap does not prove weather caused a delay. Conditions are matched to the nearest origin-airport observation within 180 minutes of scheduled departure.")
    left, right = st.columns(2)
    with left:
        st.subheader("Delay rate by weather condition")
        if matched.empty:
            st.info("No weather records match these flights.")
        else:
            by_condition = matched.assign(delayed=delayed.loc[matched.index]).groupby("weather_condition").agg(delay_rate=("delayed", "mean"), flights=("flight_key", "size")).reset_index()
            by_condition["delay_rate"] *= 100
            chart(px.bar(by_condition, x="weather_condition", y="delay_rate", text="flights", labels={"weather_condition": "Recorded condition", "delay_rate": "Delayed flights (%)", "flights": "Flights (n)"}))
    with right:
        st.subheader("Weather record coverage")
        coverage_df = pd.DataFrame({"Coverage": ["Weather matched", "No weather record"], "Flights": [len(all_matched), int((~weather_matched_all).sum())]})
        chart(px.pie(coverage_df, names="Coverage", values="Flights", hole=0.58))
    st.subheader("Average departure delay by weather condition")
    if not matched.empty:
        weather_delay = matched.groupby("weather_condition").agg(average_departure_delay_min=("departure_delay_min", "mean"), flights_with_data=("departure_delay_min", "count")).reset_index()
        chart(px.bar(weather_delay, x="weather_condition", y="average_departure_delay_min", text="flights_with_data", labels={"weather_condition": "Recorded condition", "average_departure_delay_min": "Average departure delay (min)", "flights_with_data": "Flights with data"}))
    airport_total = flights.groupby("origin").agg(total_flights=("flight_key", "size"), average_departure_delay=("departure_delay_min", "mean")).reset_index()
    airport_match = all_matched.groupby("origin").size().reset_index(name="weather_matched") if not all_matched.empty else pd.DataFrame(columns=["origin", "weather_matched"])
    airport_summary = airport_total.merge(airport_match, on="origin", how="left").fillna({"weather_matched": 0})
    airport_summary["weather_coverage_pct"] = np.where(airport_summary.total_flights.gt(0), airport_summary.weather_matched / airport_summary.total_flights * 100, np.nan)
    st.subheader("Weather coverage by airport")
    st.dataframe(airport_summary, hide_index=True, use_container_width=True)
    st.subheader("Flight-level weather records")
    cols = ["flight_id", "flight_date", "origin", "scheduled_departure", "weather_condition", "weather_time", "weather_match_delta_min", "temperature_c", "visibility_km", "wind_kph", "departure_delay_min", "arrival_delay_min"]
    st.dataframe(matched[[col for col in cols if col in matched.columns]], hide_index=True, use_container_width=True)
    csv_button("Export weather-linked flights (CSV)", matched, "aerodata_weather_flights.csv", "weather-csv")

elif page == "Dataset Management":
    st.title("Dataset Management")
    st.caption("Upload source files, inspect cleaning and validation results, and see which rows support the analysis.")
    st.info("Processed records are stored locally in SQLite. Uploaded raw files are not retained as files; original previews remain in this browser session only.")
    with st.expander("Upload CSV sources", expanded=True):
        st.markdown("Schedule and actuals are required. Weather and flight-level delay codes are optional.")
        c1, c2 = st.columns(2)
        with c1:
            schedule_file = st.file_uploader("Flight schedule CSV", type=["csv"], key="upload_schedule")
            weather_file = st.file_uploader("Weather CSV (optional)", type=["csv"], key="upload_weather")
        with c2:
            actuals_file = st.file_uploader("Flight actuals CSV", type=["csv"], key="upload_actuals")
            codes_file = st.file_uploader("Delay codes CSV (optional)", type=["csv"], key="upload_codes")
        process_button = st.button("Process uploaded datasets", type="primary", disabled=not (schedule_file and actuals_file))
        if process_button:
            try:
                source_frames = {
                    "schedule": pd.read_csv(BytesIO(schedule_file.getvalue())),
                    "actuals": pd.read_csv(BytesIO(actuals_file.getvalue())),
                    "weather": pd.read_csv(BytesIO(weather_file.getvalue())) if weather_file else pd.DataFrame(),
                    "delay_codes": pd.read_csv(BytesIO(codes_file.getvalue())) if codes_file else pd.DataFrame(),
                }
                result = process_sources(source_frames["schedule"], source_frames["actuals"], source_frames["weather"], source_frames["delay_codes"])
                uploaded_names = {key: widget.name for key, widget in [("schedule", schedule_file), ("actuals", actuals_file), ("weather", weather_file), ("delay codes", codes_file)] if widget}
                save_processed(result, DB_PATH, "Uploaded data", uploaded_names)
                st.session_state.original_uploads = source_frames
                st.success(f"Processed {len(result.flights):,} flight records; found {len(result.issues):,} validation and cleaning notes.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not process these CSV files: {error}")
    if st.button("Return to synthetic sample data"):
        use_sample_data()
        st.rerun()
    meta = get_metadata(DB_PATH)
    st.subheader("Dataset overview")
    st.caption(f"Source: {meta.get('source', data_source)} · Files: {meta.get('source_files', source_files)}")
    if not all_issues.empty:
        corrected = int(all_issues.issue_type.eq("Overnight arrival").sum())
        rejected = int(all_issues.loc[all_issues.severity.eq("Failed"), "record_key"].nunique())
        duplicate_rows = int(all_issues.issue_type.eq("Duplicate flight key").sum())
        missing_values = int(all_issues.issue_type.str.startswith("Missing").sum())
    else:
        corrected = rejected = duplicate_rows = missing_values = 0
    kpis([
        ("ROWS RECEIVED", str(meta.get("schedule_rows", len(all_flights))), "Flight schedule records"),
        ("VALID FLIGHTS", f"{int((all_flights.flight_id.notna() & all_flights.scheduled_departure.notna() & all_flights.scheduled_arrival.notna() & all_flights.origin.notna() & all_flights.destination.notna()).sum()):,}", "Valid required schedule fields"),
        ("RECORDS CORRECTED", f"{corrected:,}", "Overnight timestamps adjusted"),
        ("RECORDS REJECTED", f"{rejected:,}", "Failed validation checks"),
        ("DUPLICATES REMOVED", f"{duplicate_rows:,}", "Duplicate keys retained once"),
    ])
    st.subheader("Original and cleaned data previews")
    source_names = ["schedule", "actuals", "weather", "delay_codes"]
    source_label = st.selectbox("Source file", source_names)
    raw_uploads = st.session_state.get("original_uploads")
    if raw_uploads and source_label in raw_uploads and not raw_uploads[source_label].empty:
        st.caption("Original upload preview — raw rows from this session.")
        st.dataframe(raw_uploads[source_label].head(20), hide_index=True, use_container_width=True)
    else:
        st.caption("Original bundled file preview — synthetic sample data.")
        try:
            sample_frames = dict(zip(source_names, _read_sample()))
            st.dataframe(sample_frames[source_label].head(20), hide_index=True, use_container_width=True)
        except Exception:
            st.info("No original preview is available for this source.")
    st.caption("Cleaned flight preview — processed records stored in SQLite.")
    preview_cols = ["flight_id", "flight_date", "origin", "destination", "aircraft_id", "scheduled_departure", "actual_departure", "departure_delay_min", "scheduled_arrival", "actual_arrival", "arrival_delay_min", "status"]
    st.dataframe(all_flights[[col for col in preview_cols if col in all_flights.columns]].head(20), hide_index=True, use_container_width=True)
    st.subheader("Cleaning and validation results")
    st.caption("No missing value is replaced with zero. Invalid or missing fields remain visible and are excluded only from measures that require them.")
    if all_issues.empty:
        st.success("No validation issues were recorded.")
    else:
        severity = st.multiselect("Issue severity", ["Failed", "Warning", "Info"], default=["Failed", "Warning", "Info"])
        issue_view = all_issues[all_issues.severity.isin(severity)]
        st.dataframe(issue_view, hide_index=True, use_container_width=True)
        csv_button("Export validation issues (CSV)", issue_view, "aerodata_data_issues.csv", "issues-csv")
    st.caption(f"Missing-field issue count: {missing_values:,}. Review record references and reasons before interpreting aggregate results.")

else:
    st.title("Reports & Insights")
    st.caption("Summarize the selected dataset with its scope, definitions, and limitations attached.")
    delayed_mask = safe_bool(flights.delayed)
    eligible_mask = safe_bool(flights.otp_eligible)
    otp = safe_bool(flights.on_time_departure)[eligible_mask].mean() * 100 if eligible_mask.any() else np.nan
    dep = pd.to_numeric(flights.departure_delay_min, errors="coerce")
    arr = pd.to_numeric(flights.arrival_delay_min, errors="coerce")
    rotation_eligible = safe_bool(rotations.eligible) if not rotations.empty else pd.Series(dtype=bool)
    rotation_affected = safe_bool(rotations.potentially_affected) if not rotations.empty else pd.Series(dtype=bool)
    prop_rate = rotation_affected[rotation_eligible].mean() * 100 if rotation_eligible.any() else np.nan
    affected_connections = int(rotation_affected[rotation_eligible].sum()) if rotation_eligible.any() else 0
    eligible_connections = int(rotation_eligible.sum()) if rotation_eligible.any() else 0
    weather_count = int(flights.weather_condition.notna().sum())
    kpis([
        ("FLIGHTS ANALYSED", f"{len(flights):,}", data_source),
        ("DELAYED FLIGHTS", f"{int(delayed_mask.sum()):,}", "Departure or arrival delay ≥15 min"),
        ("DEPARTURE OTP", fmt_pct(otp), f"{int(eligible_mask.sum()):,} eligible flights"),
        ("AVG DEPARTURE DELAY", delay_label(dep.mean()), f"{int(dep.notna().sum()):,} flights with data"),
        ("AVG ARRIVAL DELAY", delay_label(arr.mean()), f"{int(arr.notna().sum()):,} flights with data"),
    ])
    if eligible_mask.any():
        st.markdown(f"- Departure OTP was **{otp:.1f}%** ({int(safe_bool(flights.on_time_departure)[eligible_mask].sum()):,} of {int(eligible_mask.sum()):,} eligible flights departed no more than 15 minutes after schedule).")
    else:
        st.markdown("- Departure OTP is not available because no flights have valid scheduled and actual departure times.")
    st.markdown(f"- **{int(delayed_mask.sum()):,} of {len(flights):,}** flights meet the delayed-flight definition (departure or arrival delay ≥15 minutes).")
    st.markdown(f"- Weather observations matched **{weather_count:,} of {len(flights):,}** flights; unmatched records are not treated as clear weather.")
    st.markdown(f"- Delay-propagation rate: **{fmt_pct(prop_rate)}** ({affected_connections:,} potentially affected of {eligible_connections:,} eligible aircraft-linked connections).")
    if not all_codes.empty and "delay_code" in all_codes and all_codes.flight_id.notna().any():
        st.subheader("Delay-code summary")
        st.dataframe(all_codes.groupby(["delay_code", "description"], dropna=False).agg(records=("flight_id", "count"), delay_minutes=("delay_minutes", "sum")).reset_index(), hide_index=True, use_container_width=True)
    else:
        st.info("No flight-level delay-code records are available for this dataset.")
    st.subheader("Limitations")
    st.markdown("- Synthetic data is for demonstration and not operational decisions.\n- Missing values are not treated as zero.\n- Aircraft links depend on normalized aircraft IDs, route continuity, and plausible timing.\n- Delay propagation and weather findings are associations, not proof of causation.\n- This summary reflects only the selected date range.")
    active_range = f"{date_range[0]} to {date_range[1]}" if isinstance(date_range, tuple) and len(date_range) == 2 else str(date_range)
    active_filters = "All airports" if scope_airport == "All airports" else f"Airport: {scope_airport}"
    pdf = build_analytical_pdf(flights, rotations, data_source, active_range, active_filters)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Download analytical report (PDF)", pdf, file_name="aerodata_analytical_report.pdf", mime="application/pdf")
    with c2:
        csv_button("Export selected flights (CSV)", flights, "aerodata_flights.csv", "report-flights-csv")
    with c3:
        csv_button("Export aircraft rotations (CSV)", rotations, "aerodata_rotations.csv", "report-rotations-csv")

st.divider()
st.caption(f"AeroData · {data_source} · {len(flights):,} flight records in current date range · Not for operational decisions")
