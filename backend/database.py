from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .data_pipeline import ProcessingResult


TABLES = {
    "flights": "flights",
    "rotations": "aircraft_rotations",
    "weather": "weather_observations",
    "delay_codes": "flight_delay_codes",
    "metrics": "processed_flight_metrics",
    "issues": "data_issues",
}


def initialize_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("CREATE TABLE IF NOT EXISTS dataset_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_dataset_metadata_key ON dataset_metadata(key)")


def save_processed(result: ProcessingResult, db_path: str | Path, source: str, source_files: dict[str, str] | None = None) -> None:
    """Replace the active processed dataset atomically and retain its provenance."""
    path = Path(db_path)
    initialize_database(path)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metadata: dict[str, Any] = {
        "source": source,
        "source_files": ", ".join(f"{key}: {name}" for key, name in (source_files or {}).items()) or "Bundled synthetic sample files",
        "processed_at_utc": now,
        **result.summary,
    }
    frames = {
        "flights": result.flights,
        "rotations": result.rotations,
        "weather": result.weather,
        "delay_codes": result.delay_codes,
        "metrics": result.flights.reindex(columns=["flight_key", "flight_id", "flight_date", "departure_delay_min", "arrival_delay_min", "delayed", "otp_eligible", "on_time_departure"]),
        "issues": result.issues,
    }
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        try:
            for key, frame in frames.items():
                clean_frame = frame.astype(object).where(pd.notna(frame), None)
                clean_frame.to_sql(TABLES[key], connection, if_exists="replace", index=False)
            connection.execute("DELETE FROM dataset_metadata")
            connection.executemany(
                "INSERT INTO dataset_metadata(key, value) VALUES (?, ?)",
                [(key, str(value)) for key, value in metadata.items()],
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_flights_date ON flights(flight_date)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_flights_id_date ON flights(flight_id, flight_date)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_rotations_aircraft ON aircraft_rotations(aircraft_id)")
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def get_metadata(db_path: str | Path) -> dict[str, str]:
    path = Path(db_path)
    if not path.exists():
        return {}
    with sqlite3.connect(path) as connection:
        try:
            return dict(connection.execute("SELECT key, value FROM dataset_metadata").fetchall())
        except sqlite3.OperationalError:
            return {}


def load_processed(db_path: str | Path) -> dict[str, pd.DataFrame]:
    path = Path(db_path)
    if not path.exists():
        return {key: pd.DataFrame() for key in TABLES}
    with sqlite3.connect(path) as connection:
        result = {}
        for key, table in TABLES.items():
            try:
                result[key] = pd.read_sql_query(f'SELECT * FROM "{table}"', connection)
            except pd.errors.DatabaseError:
                result[key] = pd.DataFrame()
    for col in ["flight_date", "scheduled_departure", "scheduled_arrival", "actual_departure", "actual_arrival", "weather_time"]:
        if col in result["flights"]:
            result["flights"][col] = pd.to_datetime(result["flights"][col], errors="coerce")
    if "flight_date" in result["metrics"]:
        result["metrics"]["flight_date"] = pd.to_datetime(result["metrics"]["flight_date"], errors="coerce")
    for col in ["flight_date", "weather_time"]:
        if col in result["weather"]:
            result["weather"][col] = pd.to_datetime(result["weather"][col], errors="coerce")
    return result


def query_flights(
    db_path: str | Path,
    start_date: str | None = None,
    end_date: str | None = None,
    airport: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> pd.DataFrame:
    """Query processed flight records with optional, parameterized filters."""
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame()
    clauses: list[str] = []
    params: list[Any] = []
    if start_date:
        clauses.append("date(flight_date) >= date(?)"); params.append(start_date)
    if end_date:
        clauses.append("date(flight_date) <= date(?)"); params.append(end_date)
    if airport:
        clauses.append("(origin = ? OR destination = ?)"); params.extend([airport.upper(), airport.upper()])
    if status:
        clauses.append("status = ?"); params.append(status)
    if search:
        clauses.append("(flight_id LIKE ? OR aircraft_id LIKE ? OR origin LIKE ? OR destination LIKE ?)")
        pattern = f"%{search}%"; params.extend([pattern, pattern, pattern, pattern])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with sqlite3.connect(path) as connection:
        frame = pd.read_sql_query(f"SELECT * FROM flights{where} ORDER BY scheduled_departure", connection, params=params)
    for col in ["flight_date", "scheduled_departure", "scheduled_arrival", "actual_departure", "actual_arrival"]:
        if col in frame:
            frame[col] = pd.to_datetime(frame[col], errors="coerce")
    return frame
