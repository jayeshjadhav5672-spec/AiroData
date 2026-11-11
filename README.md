# AeroData — Airline Operations & Delay Analytics

AeroData is a local Streamlit web application for exploring flight performance, aircraft turnaround, possible delay propagation, and weather-associated delay patterns. It starts with reproducible synthetic data and accepts CSV uploads without requiring an API key.

## Run locally

From this project folder, create and activate a Python virtual environment, install the dependencies, and start Streamlit:

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Included synthetic data

The `data/` directory contains four CSV files:

- `flight_schedule.csv` — flight ID, date, airline, origin, destination, aircraft ID, scheduled times, and status.
- `flight_actuals.csv` — flight ID, date, and actual departure and arrival times.
- `weather.csv` — airport, observation time, condition, temperature, visibility, and wind speed.
- `delay_codes.csv` — flight-level delay code, reason, and delay minutes.

The data generator creates 420 flight legs with route-contiguous aircraft rotations and coded delay records. All bundled figures are synthetic and are not suitable for operational decisions. Regenerate the four CSV files with:

```bash
python data/generate_sample_data.py
```

## Application structure

```text
AeroData/
├── app.py
├── requirements.txt
├── backend/
│   ├── data_pipeline.py
│   ├── database.py
│   └── report_generator.py
├── data/
│   ├── generate_sample_data.py
│   ├── flight_schedule.csv
│   ├── flight_actuals.csv
│   ├── weather.csv
│   └── delay_codes.csv
└── database/
    └── airline.db  # generated locally; ignored by Git
```

## Data processing and storage

The processing pipeline standardizes column names and flight IDs, parses common date/time formats, joins schedule and actual records by normalized flight ID and service date, adjusts overnight arrival timestamps, flags duplicate and invalid records, calculates departure and arrival delay, and links aircraft legs only when aircraft ID, route continuity, and timing support the link.

Normalized flights, aircraft rotations, weather observations, flight-level delay codes, processed flight metrics, data-quality issues, and dataset provenance are stored in the local SQLite database at `database/airline.db`. The dashboard reads processed rows from SQLite and uses parameterized queries for date and airport filtering.

From **Dataset Management**, upload a schedule and actuals CSV; weather and flight-level delay-code files are optional. Review the original previews, then process the files to replace the active processed dataset. Use **Return to synthetic sample data** to restore the bundled sample. Raw upload files are not saved as files; processed records are retained in SQLite.

## Key measure definitions

- **Departure delay:** actual departure minus scheduled departure, in minutes. Positive means late; negative means early.
- **Arrival delay:** actual arrival minus scheduled arrival, in minutes. Positive means late; negative means early.
- **Departure on-time performance (OTP):** share of eligible flights that departed no more than 15 minutes after schedule. Cancelled flights and flights without valid scheduled and actual departure times are excluded.
- **Actual turnaround:** next actual departure minus previous actual arrival for a confirmed successive aircraft pair.
- **Delay-propagation rate:** potentially affected eligible aircraft-linked connections divided by all eligible confirmed connections. A potentially affected connection has a late previous arrival followed by a late next departure at the configured thresholds.

Missing values are not converted to zero. Missing times are excluded only from measures that require them. Delay propagation and weather overlap show association, not proof of causation. Unconfirmed aircraft links are shown separately and excluded from confirmed-link rates.

## Main pages

1. **Overview** — flight count, delayed flights, departure OTP, delay trends, airport delay comparison, and recent delayed flights.
2. **Flight Operations** — status and hourly charts, searchable records, and flight-level inspection.
3. **Aircraft Turnaround** — confirmed rotation records, average ground time, turnaround rates, and airport comparisons.
4. **Delay Propagation** — eligible connections, threshold controls, potentially affected pairs, and supporting records.
5. **Weather Analysis** — weather coverage, delay overlap, condition comparisons, and matched records.
6. **Dataset Management** — four CSV inputs, previews, cleaning notes, validation issues, and SQLite processing.
7. **Reports & Insights** — filtered summary measures plus PDF and CSV downloads.

## Data limitations

- Synthetic records demonstrate workflow and calculations; they do not represent real airline operations.
- Aircraft sequences are supported only where normalized aircraft ID, route continuity, and plausible scheduled timing agree. Missing, reused, or conflicting identifiers can prevent confirmation.
- Weather is matched to the nearest observation for the origin airport within 180 minutes of scheduled departure. Missing matches are not treated as clear weather.
- Uploaded data is not verified against an airline source. Review Dataset Management validation issues before interpreting results.
- The turnaround tolerance is an editable analytical setting, not an industry standard.
