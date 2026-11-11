"""Generate reproducible synthetic flight, actuals, weather and delay-code data."""

from pathlib import Path

import numpy as np
import pandas as pd


OUT = Path(__file__).parent
RNG = np.random.default_rng(42)
AIRPORTS = ["BOM", "DEL", "BLR", "HYD", "MAA", "CCU"]
AIRLINES = ["AI", "6E", "UK", "SG"]
AIRCRAFT = [f"VT-{number:03d}" for number in range(101, 122)]
CODE_REASONS = {
    "WX": "Weather conditions",
    "ATC": "Air traffic control restrictions",
    "OPS": "Airport or ground operations",
    "ROT": "Aircraft rotation and turnaround",
    "OTH": "Other or unspecified operational reason",
}


def _delay_for_leg(previous_arrival_delay: float | None, is_second_leg: bool) -> tuple[float, float, str]:
    cancelled = RNG.random() < 0.035
    diverted = not cancelled and RNG.random() < 0.025
    if cancelled:
        return np.nan, np.nan, "Cancelled"
    independent_delay = float(np.clip(RNG.normal(3, 12), -10, 55))
    departure_delay = independent_delay
    if is_second_leg and previous_arrival_delay is not None and previous_arrival_delay >= 15 and RNG.random() < 0.68:
        departure_delay = max(independent_delay, previous_arrival_delay * float(RNG.uniform(0.45, 0.82)))
    arrival_delay = departure_delay + float(RNG.normal(3, 10))
    status = "Diverted" if diverted else ("Delayed" if departure_delay >= 15 or arrival_delay >= 15 else "On time")
    return round(departure_delay, 1), round(arrival_delay, 1), status


def generate() -> None:
    schedule_rows = []
    actual_rows = []
    weather_rows = {}
    code_rows = []
    flight_number = 1001
    start = pd.Timestamp("2025-04-01")
    day_index = np.arange(30)

    # Each aircraft operates two route-contiguous legs on ten days. Its ending
    # airport carries into the next operating day, producing plausible sequences.
    for aircraft_id in AIRCRAFT:
        operating_days = sorted(RNG.choice(day_index, size=10, replace=False).tolist())
        current_airport = str(RNG.choice(AIRPORTS))
        for active_day in operating_days:
            service_date = start + pd.Timedelta(days=int(active_day))
            first_departure = service_date + pd.Timedelta(hours=int(RNG.integers(5, 9)), minutes=int(RNG.integers(0, 60)))
            previous_arrival_delay = None
            for leg_number in range(2):
                origin = current_airport
                destination = str(RNG.choice([airport for airport in AIRPORTS if airport != origin]))
                scheduled_departure = first_departure if leg_number == 0 else previous_scheduled_arrival + pd.Timedelta(minutes=int(RNG.integers(75, 145)))
                duration_min = int(RNG.integers(75, 185))
                scheduled_arrival = scheduled_departure + pd.Timedelta(minutes=duration_min)
                departure_delay, arrival_delay, status = _delay_for_leg(previous_arrival_delay, leg_number == 1)
                actual_departure = scheduled_departure + pd.Timedelta(minutes=departure_delay) if pd.notna(departure_delay) else pd.NaT
                actual_arrival = scheduled_arrival + pd.Timedelta(minutes=arrival_delay) if pd.notna(arrival_delay) else pd.NaT
                airline = str(RNG.choice(AIRLINES))
                flight_id = f"{airline}{flight_number}"
                flight_number += 1

                schedule_rows.append({
                    "flight_id": flight_id, "flight_date": service_date.date().isoformat(),
                    "airline": airline,
                    "origin": origin, "destination": destination, "aircraft_id": aircraft_id,
                    "scheduled_departure": scheduled_departure, "scheduled_arrival": scheduled_arrival,
                    "status": status,
                })
                actual_rows.append({
                    "flight_id": flight_id, "flight_date": service_date.date().isoformat(),
                    "actual_departure": actual_departure, "actual_arrival": actual_arrival,
                })

                observation_time = scheduled_departure.floor("h")
                weather_key = (origin, observation_time)
                if weather_key not in weather_rows:
                    condition = str(RNG.choice(["Clear", "Cloudy", "Rain", "Fog", "Wind", "Storm"], p=[0.43, 0.20, 0.16, 0.08, 0.09, 0.04]))
                    weather_rows[weather_key] = {
                        "airport": origin, "weather_time": observation_time,
                        "condition": condition,
                        "temperature_c": round(float(RNG.normal(27, 5)), 1),
                        "visibility_km": round(float(RNG.uniform(0.5, 10)), 1),
                        "wind_kph": round(float(RNG.uniform(2, 48)), 1),
                    }

                if status != "Cancelled" and pd.notna(departure_delay) and (departure_delay >= 15 or arrival_delay >= 15):
                    code = str(RNG.choice(list(CODE_REASONS), p=[0.25, 0.22, 0.23, 0.20, 0.10]))
                    code_rows.append({
                        "flight_id": flight_id, "flight_date": service_date.date().isoformat(),
                        "delay_code": code, "delay_reason": CODE_REASONS[code],
                        "delay_minutes": int(max(departure_delay, arrival_delay, 0)),
                    })

                current_airport = destination
                previous_scheduled_arrival = scheduled_arrival
                previous_arrival_delay = arrival_delay if pd.notna(actual_arrival) else None

    pd.DataFrame(schedule_rows).to_csv(OUT / "flight_schedule.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    pd.DataFrame(actual_rows).to_csv(OUT / "flight_actuals.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    pd.DataFrame(weather_rows.values()).sort_values(["weather_time", "airport"]).to_csv(OUT / "weather.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    pd.DataFrame(code_rows, columns=["flight_id", "flight_date", "delay_code", "delay_reason", "delay_minutes"]).to_csv(OUT / "delay_codes.csv", index=False)
    print(f"Generated {len(schedule_rows)} synthetic flights, {len(weather_rows)} weather observations, and {len(code_rows)} flight-level delay-code records in {OUT}")


if __name__ == "__main__":
    generate()
