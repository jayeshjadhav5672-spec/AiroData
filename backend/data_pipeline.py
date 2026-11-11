from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


ALIASES = {
    "flight_number": "flight_id", "flight": "flight_id", "flight_no": "flight_id", "flightid": "flight_id",
    "flight_date": "flight_date", "flightdate": "flight_date", "date": "flight_date", "service_date": "flight_date",
    "tail_number": "aircraft_id", "tail": "aircraft_id", "registration": "aircraft_id", "aircraftid": "aircraft_id",
    "aircraft": "aircraft_id", "origin_airport": "origin", "departure_airport": "origin",
    "destination_airport": "destination", "arrival_airport": "destination",
    "scheduled_dep": "scheduled_departure", "scheduled_departure_time": "scheduled_departure", "scheduleddeparture": "scheduled_departure",
    "std": "scheduled_departure", "actual_dep": "actual_departure", "actualdeparture": "actual_departure",
    "actual_departure_time": "actual_departure", "atd": "actual_departure",
    "scheduled_arr": "scheduled_arrival", "scheduled_arrival_time": "scheduled_arrival", "scheduledarrival": "scheduled_arrival",
    "sta": "scheduled_arrival", "actual_arr": "actual_arrival", "actualarrival": "actual_arrival",
    "actual_arrival_time": "actual_arrival", "ata": "actual_arrival",
    "weather_condition": "condition", "weather": "condition", "temperature": "temperature_c",
    "visibility": "visibility_km", "wind_speed": "wind_kph", "wind_speed_kph": "wind_kph",
    "delay_reason": "description", "reason": "description", "delay_minutes": "delay_minutes",
    "delay_code": "delay_code", "code": "delay_code",
}

REQUIRED_SCHEDULE = ["flight_id", "flight_date", "origin", "destination", "scheduled_departure", "scheduled_arrival"]
REQUIRED_ACTUALS = ["flight_id", "flight_date", "actual_departure", "actual_arrival"]
AIRPORT_ALIASES = {
    "MUMBAI": "BOM", "VABB": "BOM", "BOMBAY": "BOM",
    "DELHI": "DEL", "NEWDELHI": "DEL", "VIDP": "DEL",
    "BENGALURU": "BLR", "BANGALORE": "BLR", "VOBL": "BLR",
    "HYDERABAD": "HYD", "VOHS": "HYD",
    "CHENNAI": "MAA", "MADRAS": "MAA", "VOMM": "MAA",
    "KOLKATA": "CCU", "CALCUTTA": "CCU", "VECC": "CCU",
    "PUNE": "PNQ", "VAPO": "PNQ",
}


@dataclass
class ProcessingResult:
    flights: pd.DataFrame
    rotations: pd.DataFrame
    weather: pd.DataFrame
    delay_codes: pd.DataFrame
    issues: pd.DataFrame
    summary: dict[str, Any]


def _columns(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    data = frame.copy()
    names = []
    for value in data.columns:
        key = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
        names.append(ALIASES.get(key, key))
    data.columns = names
    data["_source_row"] = np.arange(2, len(data) + 2)
    return data


def _parse_date(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format="mixed", errors="coerce").dt.normalize()


def _parse_time(values: pd.Series, dates: pd.Series | None = None) -> pd.Series:
    parsed = pd.to_datetime(values, format="mixed", errors="coerce")
    if dates is not None:
        date_values = pd.to_datetime(dates, errors="coerce").dt.normalize()
        time_only = parsed.notna() & parsed.dt.year.le(1900)
        if time_only.any():
            text_times = values.astype("string").str.strip()
            combined = pd.to_datetime(date_values.dt.strftime("%Y-%m-%d") + " " + text_times, format="mixed", errors="coerce")
            parsed.loc[time_only] = combined.loc[time_only]
    return parsed


def _normalize_id(values: pd.Series) -> pd.Series:
    return values.astype("string").str.upper().str.replace(r"[^A-Z0-9]", "", regex=True).replace({"": pd.NA})


def _normalize_airport(values: pd.Series) -> pd.Series:
    cleaned = values.astype("string").str.strip().str.upper()
    lookup_key = cleaned.str.replace(r"[^A-Z0-9]", "", regex=True)
    return lookup_key.map(AIRPORT_ALIASES).fillna(cleaned)


def _issue(rows: list[dict[str, Any]], source: str, row: Any, key: Any, kind: str, severity: str, detail: str, action: str) -> None:
    rows.append({"source": source, "source_row": row, "record_key": key, "issue_type": kind, "severity": severity, "detail": detail, "action": action})


def _prepare_flights(schedule: pd.DataFrame, actuals: pd.DataFrame, issue_rows: list[dict[str, Any]]) -> pd.DataFrame:
    s, a = _columns(schedule), _columns(actuals)
    if "flight_date" not in s and "scheduled_departure" in s:
        s["flight_date"] = pd.to_datetime(s.scheduled_departure, format="mixed", errors="coerce").dt.normalize()
    if "flight_date" not in a and "actual_departure" in a:
        a["flight_date"] = pd.to_datetime(a.actual_departure, format="mixed", errors="coerce").dt.normalize()
    missing = [col for col in REQUIRED_SCHEDULE if col not in s]
    if missing:
        raise ValueError("Flight schedule is missing required columns: " + ", ".join(missing))
    missing = [col for col in REQUIRED_ACTUALS if col not in a]
    if missing:
        raise ValueError("Flight actuals is missing required columns: " + ", ".join(missing))

    s["flight_id"] = _normalize_id(s.flight_id)
    s["flight_date"] = _parse_date(s.flight_date)
    s["scheduled_departure"] = _parse_time(s.scheduled_departure, s.flight_date)
    s["scheduled_arrival"] = _parse_time(s.scheduled_arrival, s.flight_date)
    a["flight_id"] = _normalize_id(a.flight_id)
    a["flight_date"] = _parse_date(a.flight_date)
    a["actual_departure"] = _parse_time(a.actual_departure, a.flight_date)
    a["actual_arrival"] = _parse_time(a.actual_arrival, a.flight_date)

    for frame, source, id_col, time_col in [(s, "schedule", "scheduled_departure", "scheduled_arrival"), (a, "actuals", "actual_departure", "actual_arrival")]:
        frame["_join_id"] = frame.flight_id
        frame["_join_date"] = frame.flight_date
        for idx in frame.index[frame.flight_id.isna()]:
            frame.loc[idx, "_join_id"] = f"__MISSING_{source}_{idx}"
        for idx in frame.index[frame.flight_date.isna()]:
            source_offset = 100000 if source == "actuals" else 0
            frame.loc[idx, "_join_date"] = pd.Timestamp("1900-01-01") + pd.Timedelta(days=int(idx) + source_offset)
        dupe = frame.duplicated(["_join_id", "_join_date"], keep="first")
        for idx in frame.index[dupe]:
            _issue(issue_rows, source, frame.loc[idx, "_source_row"], f"{frame.loc[idx, '_join_id']} / {frame.loc[idx, '_join_date']}", "Duplicate flight key", "Warning", "More than one row has the same normalized flight ID and date.", "Retained the first row; review this record before relying on aggregates.")
        frame.drop_duplicates(["_join_id", "_join_date"], keep="first", inplace=True)

    schedule_keys = set(zip(s._join_id.astype(str), s._join_date.astype(str)))
    for idx, row in a.iterrows():
        if (str(row["_join_id"]), str(row["_join_date"])) not in schedule_keys:
            _issue(issue_rows, "actuals", row["_source_row"], f"{row.flight_id} / {row.flight_date}", "Actual without schedule", "Warning", "Actual-time record has no matching schedule row after normalizing flight ID and date.", "Check the flight ID and date formats; unmatched actuals are not added as standalone flights.")

    # Handle overnight services when source values contain clock times on the flight date.
    overnight = s.scheduled_arrival.notna() & s.scheduled_departure.notna() & (s.scheduled_arrival < s.scheduled_departure)
    s.loc[overnight, "scheduled_arrival"] += pd.Timedelta(days=1)
    overnight_actual = a.actual_arrival.notna() & a.actual_departure.notna() & (a.actual_arrival < a.actual_departure)
    a.loc[overnight_actual, "actual_arrival"] += pd.Timedelta(days=1)
    for idx in s.index[overnight]:
        _issue(issue_rows, "schedule", s.loc[idx, "_source_row"], s.loc[idx, "flight_id"], "Overnight arrival", "Info", "Arrival time was earlier on the clock than departure and was moved to the following day.", "Review the corrected timestamp in the cleaned preview.")
    for idx in a.index[overnight_actual]:
        _issue(issue_rows, "actuals", a.loc[idx, "_source_row"], a.loc[idx, "flight_id"], "Overnight arrival", "Info", "Actual arrival time was earlier on the clock than departure and was moved to the following day.", "Review the corrected timestamp in the cleaned preview.")

    keep_s = ["_join_id", "_join_date", "flight_id", "flight_date", "origin", "destination", "scheduled_departure", "scheduled_arrival", "_source_row"]
    for optional in ["aircraft_id", "airline", "status"]:
        if optional in s:
            keep_s.append(optional)
    keep_a = ["_join_id", "_join_date", "actual_departure", "actual_arrival", "_source_row"]
    out = s[keep_s].merge(a[keep_a], on=["_join_id", "_join_date"], how="left", suffixes=("_schedule", "_actual"), indicator=True)
    out.rename(columns={"_source_row_schedule": "schedule_source_row", "_source_row_actual": "actual_source_row", "_source_row": "schedule_source_row"}, inplace=True)
    out.drop(columns=["_join_id", "_join_date", "_merge"], inplace=True, errors="ignore")
    out["origin"] = _normalize_airport(out.origin)
    out["destination"] = _normalize_airport(out.destination)
    if "aircraft_id" not in out:
        out["aircraft_id"] = pd.NA
    out["aircraft_id"] = out.aircraft_id.astype("string").str.strip().str.upper().replace({"": pd.NA, "NAN": pd.NA, "<NA>": pd.NA})
    if "airline" not in out:
        out["airline"] = out.flight_id.astype("string").str.extract(r"^([A-Z]+)", expand=False)
    if "status" not in out:
        out["status"] = pd.NA
    out["status"] = out.status.astype("string").str.strip().str.title()
    out["departure_delay_min"] = (out.actual_departure - out.scheduled_departure).dt.total_seconds() / 60
    out["arrival_delay_min"] = (out.actual_arrival - out.scheduled_arrival).dt.total_seconds() / 60

    for idx, row in out.iterrows():
        record = row.flight_id if pd.notna(row.flight_id) else f"schedule row {row.get('schedule_source_row', '?')}"
        for col in ["flight_id", "flight_date", "origin", "destination", "scheduled_departure", "scheduled_arrival"]:
            if pd.isna(row.get(col)):
                _issue(issue_rows, "schedule", row.get("schedule_source_row"), record, f"Missing or invalid {col}", "Failed", f"Required field {col} is missing or could not be parsed.", "Record the issue and exclude it from measures that require this field.")
        if pd.notna(row.scheduled_departure) and pd.notna(row.scheduled_arrival) and row.scheduled_arrival < row.scheduled_departure:
            _issue(issue_rows, "schedule", row.get("schedule_source_row"), record, "Invalid scheduled sequence", "Failed", "Scheduled arrival is before scheduled departure after overnight adjustment.", "Exclude this leg from duration-based measures.")
        if pd.isna(row.actual_departure):
            _issue(issue_rows, "actuals", row.get("actual_source_row"), record, "Missing actual departure", "Warning", "Departure delay and departure OTP cannot be calculated.", "Keep it out of those denominators; do not treat it as zero.")
        if pd.isna(row.aircraft_id):
            _issue(issue_rows, "schedule", row.get("schedule_source_row"), record, "Missing aircraft ID", "Warning", "Aircraft rotation cannot be confirmed for this flight.", "Do not link it to another leg by assumption.")
        for airport_field in ["origin", "destination"]:
            airport_value = row.get(airport_field)
            if pd.notna(airport_value) and not re.fullmatch(r"[A-Z]{3}", str(airport_value)):
                _issue(issue_rows, "schedule", row.get("schedule_source_row"), record, "Malformed airport code", "Warning", f"{airport_field.title()} value {airport_value!s} is not a normalized three-letter code.", "Review airport mapping before airport-level comparisons.")

    dep_late = out.departure_delay_min.ge(15).fillna(False)
    arr_late = out.arrival_delay_min.ge(15).fillna(False)
    inferred = np.select(
        [
            out.status.eq("Cancelled").fillna(False).to_numpy(dtype=bool),
            (dep_late | arr_late).to_numpy(dtype=bool),
            (out.departure_delay_min.notna() & out.arrival_delay_min.notna()).to_numpy(dtype=bool),
        ],
        ["Cancelled", "Delayed", "On Time"],
        default="Unknown",
    )
    out["status"] = out.status.where(out.status.isin(["Cancelled", "Diverted", "Delayed", "On Time", "Unknown"]), inferred)
    out["otp_eligible"] = out.scheduled_departure.notna() & out.actual_departure.notna() & out.status.ne("Cancelled")
    out["on_time_departure"] = out.otp_eligible & out.departure_delay_min.le(15)
    out["delayed"] = dep_late | arr_late
    out["flight_key"] = out.flight_id.astype("string") + "|" + out.flight_date.dt.strftime("%Y-%m-%d").fillna("UNKNOWN")
    return out


def _prepare_weather(weather: pd.DataFrame | None, issues: list[dict[str, Any]]) -> pd.DataFrame:
    w = _columns(weather)
    if w.empty:
        return pd.DataFrame(columns=["airport", "weather_time", "condition", "temperature_c", "visibility_km", "wind_kph"])
    if "weather_time" not in w and "flight_date" in w:
        if "time" in w:
            w["weather_time"] = w.flight_date.astype("string") + " " + w.time.astype("string")
        else:
            w.rename(columns={"flight_date": "weather_time"}, inplace=True)
    for col in ["airport", "weather_time", "condition"]:
        if col not in w:
            _issue(issues, "weather", "", "", "Missing weather column", "Warning", f"Weather data has no {col} column.", "Weather analysis is unavailable until this field is supplied.")
            return pd.DataFrame(columns=["airport", "weather_time", "condition", "temperature_c", "visibility_km", "wind_kph"])
    w["airport"] = _normalize_airport(w.airport)
    w["weather_time"] = _parse_time(w.weather_time)
    w["condition"] = w.condition.astype("string").str.strip().str.title()
    for col in ["temperature_c", "visibility_km", "wind_kph"]:
        if col not in w:
            w[col] = np.nan
        w[col] = pd.to_numeric(w[col], errors="coerce")
    invalid = w.weather_time.isna() | w.airport.isna() | ~w.airport.astype("string").str.fullmatch(r"[A-Z]{3}", na=False)
    for idx in w.index[invalid]:
        _issue(issues, "weather", w.loc[idx, "_source_row"], "", "Invalid weather key", "Warning", "Airport or observation time is missing or invalid.", "Exclude this observation from matching.")
    return w.loc[~invalid, ["airport", "weather_time", "condition", "temperature_c", "visibility_km", "wind_kph", "_source_row"]].drop_duplicates(["airport", "weather_time"], keep="first").reset_index(drop=True)


def _prepare_codes(codes: pd.DataFrame | None, issues: list[dict[str, Any]]) -> pd.DataFrame:
    c = _columns(codes)
    columns = ["flight_id", "flight_date", "delay_code", "description", "delay_minutes"]
    if c.empty:
        return pd.DataFrame(columns=columns)
    if "delay_code" not in c:
        _issue(issues, "delay_codes", "", "", "Missing delay code", "Warning", "No delay_code column was found.", "Delay-code analysis is unavailable.")
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in c:
            c[col] = pd.NA
    c["flight_id"] = _normalize_id(c.flight_id)
    c["flight_date"] = _parse_date(c.flight_date)
    c["delay_code"] = c.delay_code.astype("string").str.strip().str.upper()
    c["description"] = c.description.astype("string").str.strip()
    c["delay_minutes"] = pd.to_numeric(c.delay_minutes, errors="coerce")
    # A small code-description dictionary is useful metadata but is not flight-level delay data.
    if c.flight_id.isna().all():
        _issue(issues, "delay_codes", "", "", "Code dictionary only", "Warning", "This file maps delay codes to descriptions but has no flight IDs; it cannot be joined to individual flights.", "Upload flight-level delay codes to analyze them by flight.")
        return c[columns].drop_duplicates(["delay_code", "description"]).reset_index(drop=True)
    return c[columns].drop_duplicates(["flight_id", "flight_date", "delay_code"], keep="first").reset_index(drop=True)


def _link_rotations(flights: pd.DataFrame, issues: list[dict[str, Any]], min_ground_min: int = 0, max_ground_min: int = 900) -> pd.DataFrame:
    columns = ["aircraft_id", "connection_hop", "previous_flight_key", "next_flight_key", "previous_flight_id", "next_flight_id", "airport", "scheduled_turnaround_min", "actual_turnaround_min", "previous_arrival_delay_min", "next_departure_delay_min", "link_status", "eligible", "potentially_affected"]
    rows: list[dict[str, Any]] = []
    valid = flights[flights.aircraft_id.notna() & flights.scheduled_departure.notna()].sort_values(["aircraft_id", "scheduled_departure"])
    for tail, group in valid.groupby("aircraft_id", sort=False):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            prev, nxt = group.iloc[i], group.iloc[i + 1]
            sched_ground = (nxt.scheduled_departure - prev.scheduled_arrival).total_seconds() / 60 if pd.notna(prev.scheduled_arrival) else np.nan
            actual_ground = (nxt.actual_departure - prev.actual_arrival).total_seconds() / 60 if pd.notna(nxt.actual_departure) and pd.notna(prev.actual_arrival) else np.nan
            route_ok = pd.notna(prev.destination) and pd.notna(nxt.origin) and prev.destination == nxt.origin
            time_ok = pd.notna(sched_ground) and min_ground_min <= sched_ground <= max_ground_min
            confirmed = bool(route_ok and time_ok)
            link_status = "Confirmed" if confirmed else "Unconfirmed"
            eligible = bool(confirmed and pd.notna(actual_ground) and min_ground_min <= actual_ground <= max_ground_min and pd.notna(prev.arrival_delay_min) and pd.notna(nxt.departure_delay_min))
            potentially = bool(eligible and prev.arrival_delay_min >= 15 and nxt.departure_delay_min >= 15)
            rows.append({"aircraft_id": tail, "connection_hop": i + 1, "previous_flight_key": prev.flight_key, "next_flight_key": nxt.flight_key, "previous_flight_id": prev.flight_id, "next_flight_id": nxt.flight_id, "airport": prev.destination, "scheduled_turnaround_min": sched_ground, "actual_turnaround_min": actual_ground, "previous_arrival_delay_min": prev.arrival_delay_min, "next_departure_delay_min": nxt.departure_delay_min, "link_status": link_status, "eligible": eligible, "potentially_affected": potentially})
            if not confirmed:
                _issue(issues, "rotations", "", f"{prev.flight_key} → {nxt.flight_key}", "Unconfirmed aircraft link", "Warning", "Aircraft ID matches, but route continuity or scheduled ground time could not confirm a consecutive rotation.", "Keep the pair visible as unconfirmed and exclude it from confirmed-link rates.")
    return pd.DataFrame(rows, columns=columns)


def _match_weather(flights: pd.DataFrame, weather: pd.DataFrame, tolerance_minutes: int = 180) -> pd.DataFrame:
    out = flights.copy()
    out["weather_condition"] = pd.NA
    out["weather_time"] = pd.NaT
    out["temperature_c"] = np.nan
    out["visibility_km"] = np.nan
    out["wind_kph"] = np.nan
    out["weather_match_delta_min"] = np.nan
    if weather.empty or out.empty:
        return out
    left = out[["flight_key", "origin", "scheduled_departure"]].dropna(subset=["origin", "scheduled_departure"]).copy()
    right = weather.rename(columns={"airport": "origin", "condition": "weather_condition"}).copy()
    left = left.sort_values("scheduled_departure"); right = right.sort_values("weather_time")
    chunks=[]
    for airport, lgroup in left.groupby("origin", sort=False):
        rgroup = right[right.origin == airport].sort_values("weather_time")
        if rgroup.empty: continue
        matched = pd.merge_asof(lgroup.sort_values("scheduled_departure"), rgroup.sort_values("weather_time"), left_on="scheduled_departure", right_on="weather_time", direction="nearest", tolerance=pd.Timedelta(minutes=tolerance_minutes))
        matched["weather_match_delta_min"] = (matched.scheduled_departure - matched.weather_time).dt.total_seconds().abs() / 60
        chunks.append(matched[["flight_key", "weather_condition", "weather_time", "temperature_c", "visibility_km", "wind_kph", "weather_match_delta_min"]])
    if chunks:
        matches = pd.concat(chunks, ignore_index=True).drop_duplicates("flight_key")
        out = out.merge(matches, on="flight_key", how="left", suffixes=("", "_matched"))
        for col in ["weather_condition", "weather_time", "temperature_c", "visibility_km", "wind_kph", "weather_match_delta_min"]:
            matched_col = f"{col}_matched"
            if matched_col in out:
                out[col] = out[matched_col]
                out.drop(columns=[matched_col], inplace=True)
    return out


def process_sources(schedule: pd.DataFrame, actuals: pd.DataFrame, weather: pd.DataFrame | None = None, delay_codes: pd.DataFrame | None = None, weather_tolerance_min: int = 180) -> ProcessingResult:
    issue_rows: list[dict[str, Any]] = []
    flights = _prepare_flights(schedule, actuals, issue_rows)
    clean_weather = _prepare_weather(weather, issue_rows)
    clean_codes = _prepare_codes(delay_codes, issue_rows)

    if not clean_codes.empty and clean_codes.flight_id.notna().any():
        join_codes = clean_codes.dropna(subset=["flight_id", "flight_date"]).groupby(["flight_id", "flight_date"], as_index=False).agg(
            delay_code=("delay_code", lambda s: ", ".join(s.dropna().astype(str).unique())),
            delay_reason=("description", lambda s: "; ".join(s.dropna().astype(str).unique())),
            delay_code_minutes=("delay_minutes", "sum"),
        )
        flights = flights.merge(join_codes, on=["flight_id", "flight_date"], how="left")
        matched_keys = flights.loc[flights.flight_id.notna() & flights.flight_date.notna(), ["flight_id", "flight_date"]]
        known = set(zip(matched_keys.flight_id, matched_keys.flight_date))
        for _, row in clean_codes.dropna(subset=["flight_id", "flight_date"]).iterrows():
            if (row.flight_id, row.flight_date) not in known:
                _issue(issue_rows, "delay_codes", "", f"{row.flight_id}|{row.flight_date}", "Delay code without flight", "Warning", "Delay-code row did not match a schedule flight.", "Review normalized flight ID and service date.")
    else:
        flights["delay_code"] = pd.NA
        flights["delay_reason"] = pd.NA
        flights["delay_code_minutes"] = np.nan
    flights = _match_weather(flights, clean_weather, weather_tolerance_min)
    rotations = _link_rotations(flights, issue_rows)
    issues = pd.DataFrame(issue_rows, columns=["source", "source_row", "record_key", "issue_type", "severity", "detail", "action"])
    summary = {
        "schedule_rows": int(len(schedule)), "actual_rows": int(len(actuals)), "flights": int(len(flights)),
        "valid_schedule": int((flights.scheduled_departure.notna() & flights.scheduled_arrival.notna()).sum()),
        "weather_rows": int(len(clean_weather)), "weather_matched_flights": int(flights.weather_condition.notna().sum()),
        "delay_code_rows": int(len(clean_codes)), "rotations": int(len(rotations)),
        "eligible_connections": int(rotations.eligible.sum()) if not rotations.empty else 0,
        "potentially_affected": int(rotations.potentially_affected.sum()) if not rotations.empty else 0,
        "issue_count": int(len(issues)), "issue_failures": int(issues.severity.eq("Failed").sum()) if not issues.empty else 0,
        "duplicate_rows_removed": int(issues.issue_type.eq("Duplicate flight key").sum()) if not issues.empty else 0,
        "corrected_rows": int(issues.issue_type.eq("Overnight arrival").sum()) if not issues.empty else 0,
        "rejected_records": int(issues.loc[issues.severity.eq("Failed"), "record_key"].nunique()) if not issues.empty else 0,
    }
    return ProcessingResult(flights, rotations, clean_weather, clean_codes, issues, summary)
