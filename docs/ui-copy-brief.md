# AeroData — UI Content & Wording Brief

| | |
|---|---|
| **Product** | AeroData |
| **Subtitle** | Airline Operations & Delay Analytics |
| **Audience** | App developer, reviewer |
| **Scope** | Page-by-page content, labels, and microcopy for the seven app pages |
| **Status** | Draft for review |
| **Out of scope** | Python/Streamlit code, data models, schema, storage, dependencies, deployment |

This brief describes **what each page must communicate and how it should say it**. It does not prescribe backend implementation. Where a decision belongs to the developer or product owner, it is listed in [Section 9](#9-open-questions-for-the-developer).

---

## 1. How to use this brief

1. Treat the **Purpose** of each page as the page's job. If a component does not serve that job, remove it.
2. Use the **Suggested wording** as a copy deck. Wording may be shortened for space, but the meaning and caveats must survive.
3. Apply the **Non-negotiable content rules** below to every screen, chart, tooltip, empty state, and export.
4. Do not add filler (welcome messages, motivational copy, invented "insights"). Every sentence must help an analyst interpret a number, filter a record, or understand a limitation.

### 1.1 Non-negotiable content rules

| Rule | What it means in the UI |
|---|---|
| **Synthetic is labelled synthetic** | Sample data carries a visible "Synthetic sample data" badge with a short explanation. Never imply it is live, current, or real airline operations. |
| **Association is not causation** | Delay propagation and weather analyses are described as associations. Use "may indicate", "possible", "potentially affected". Never "caused by", "proves", or "due to". |
| **Missing is not zero** | Show "No data", "Not available", or "Missing" — never `0`, `0 min`, or `0%` for an absent value. Exclude missing records from rates and show how many were excluded. |
| **Every rate shows its denominator** | Write `68.7% (8,568 of 12,480 flights)`, not `68.7%`. |
| **Unconfirmed links are labelled** | When two legs cannot be confidently tied to the same aircraft, say "Unconfirmed aircraft link" or "Not linked". Do not present the pair as a confirmed rotation. |
| **Scope is always visible** | Every page states the active date range and filters, or shows a "Filtered view" indicator. |
| **No operational advice** | Never phrase findings as instructions ("ground this aircraft", "expect delays"). The app describes data; it does not direct operations. |

---

## 2. Visual and verbal direction

### 2.1 Visual style

Enterprise analytics, not a marketing site. Calm, dense, and legible.

| Element | Direction |
|---|---|
| **Palette** | Deep navy `#0F2742` (navigation, headings), white `#FFFFFF` (cards), muted blue `#3E6E9E` (primary series, links), light background `#F5F7FA`, border `#E2E8F0`, body text `#1F2937`, secondary text `#5B6B7C`. Amber `#B7791F` for warnings, muted red `#B42318` only for failed checks or critical flags. |
| **Typography** | Inter (or system sans). 14 px body, 24–28 px page title, 12 px captions/axis labels. Tabular numerals for all figures so columns align. |
| **Layout** | Persistent left navigation on navy; main area on light background; content in white cards with 1 px borders and 8 px radius. Consistent 8/16/24 px spacing. |
| **Icons** | Simple 20 px outline icons only, used to aid scanning (filter, download, info, warning). No filled, 3D, or decorative icons. |
| **Charts** | Navy and muted blue as primary series; one accent colour for comparison; red reserved for failed/flagged states. No gradients, drop shadows on charts, 3D effects, or animation. Label axes with units. |
| **Density** | Tables are first-class. Prefer sortable tables and small multiples over oversized hero visuals. |
| **Avoid** | Decorative illustrations, stock aviation photos, animated counters, glassmorphism, "AI-powered" badges, generic dashboard filler. |

Status must never rely on colour alone: pair colour with a text label or icon.

### 2.2 Voice and tone

- Plain, specific, operational. Short sentences.
- Use the analyst's words: flight, leg, aircraft, turnaround, departure delay, arrival delay.
- Prefer "may indicate" over "shows"; "not available" over "N/A" in prose.
- No exclamation marks, no marketing adjectives, no anthropomorphism.
- Sentence case for headings and labels ("Recent delayed flights", not "Recent Delayed Flights").

### 2.3 Formatting conventions

| Item | Convention | Example |
|---|---|---|
| Date | `d MMM yyyy` | `11 Nov 2026` |
| Date range | En dash | `1–30 Sep 2026` |
| Time | 24-hour, airport local time, timezone stated once per page | `14:35` |
| Delay | Signed minutes; late is positive | `+18 min`, `−6 min` (early) |
| Duration | Minutes under 60; hours and minutes above | `45 min`, `1 h 24 min` |
| Percentage | One decimal place, with denominator | `18.2% (402 of 2,209)` |
| Counts | Thousands separators | `12,480` |
| Missing | Explicit label, neutral styling | `No data` |

State the time basis once per page, e.g. "All times are local to the airport." If timezone conversion is not applied, say so in the page's caveat block rather than implying UTC or a single zone.

---

## 3. Global shell and shared patterns

### 3.1 Header and navigation

- Product wordmark: **AeroData**
- Subtitle directly beneath: **Airline Operations & Delay Analytics**
- Navigation labels, in this order:
  1. Overview
  2. Flight Operations
  3. Aircraft Turnaround
  4. Delay Propagation
  5. Weather Analysis
  6. Dataset Management
  7. Reports & Insights
- Global area (top right): **data source badge**, **active date range**, and a **Definitions & limitations** link.
- Footer on every page: `AeroData · [data source] · Figures reflect the current filters only` plus a link to definitions.

### 3.2 Data source badges (must appear on every page)

| Source | Badge label | Help text (tooltip or inline) |
|---|---|---|
| Synthetic sample | **Synthetic sample data** | "Generated for demonstration. These records do not represent real flights, aircraft, or airlines." |
| Uploaded file | **Uploaded data — {filename}** | "Provided by you and not verified against an airline or airport source." |
| Public/reference | **Public reference data** | "Sourced from a public dataset. Coverage and accuracy vary by provider." |

Rules:

- Never use "Live", "Real-time", "Current operations", or "Production data" unless that is factually true and confirmed.
- The badge persists on drill-down views, printed pages, and exports.
- When the source is synthetic, include the sentence "Do not use sample figures for operational decisions." in the Dataset Management page and in exported reports.

### 3.3 Filters

- Filter bar sits directly below the page title and above all content it affects.
- Show active filters as removable chips: `Airport: DEL ×`, `Dates: 1–30 Sep 2026 ×`.
- Provide **Reset filters** and, when more than two filters are active, a "Filtered view" indicator.
- Filters must state their effect on denominators where relevant: "Rates recalculate for the filtered flights."
- Filter labels: **Date range**, **Airline**, **Origin airport**, **Destination airport**, **Aircraft (tail number)**, **Operational status**, **Delay threshold**, **Data source**.

### 3.4 Measure definitions pattern

Every KPI card has an outline info icon. The tooltip is two short sentences: what it measures and its denominator. A "See all definitions" link opens the glossary (Section 4) as a side panel or modal.

Tooltip structure:

> **{Measure}** — {one-sentence definition}. Based on {population/denominator}.

### 3.5 Loading, empty, and error states

| State | Copy |
|---|---|
| Loading | "Loading flight data…" (no spinners longer than necessary; no fake progress) |
| No data in range | "No flights in this date range. Choose a wider range or check the dataset." |
| No filter matches | "No flights match these filters. Remove a filter or widen the date range." |
| Missing required field | "This record has no {field}. It is excluded from {measure}." |
| Unconfirmed aircraft link | "Aircraft link unconfirmed — these flights may not be consecutive legs of the same aircraft." |
| Calculation not possible | "Not enough data to calculate. {X} of {Y} records have the required times." |
| Load failure | "The dataset could not be loaded. Check the file and try again." (include the reason, if known, in plain language) |

### 3.6 Export pattern

- Export labels: **Export table (CSV)**, **Download report (PDF)**, **Print**.
- Every export includes a header block with: data source, date range, active filters, generated timestamp, and the relevant definitions/caveats.
- Disable export with an explanation when there is nothing to export: "Nothing to export for the current filters."

---

## 4. Measures, definitions, and help text

This is the canonical glossary. Use these names everywhere. Do not introduce synonyms on individual pages.

| Measure | Plain-language definition | Population / denominator | Watch-outs |
|---|---|---|---|
| **Departure delay** | Actual departure time minus scheduled departure time, in minutes. Positive means late; negative means early. | Flights with both a valid scheduled and valid actual departure time. | Missing actual departure → "No data", not zero. Cancelled flights have no departure delay. |
| **Arrival delay** | Actual arrival time minus scheduled arrival time, in minutes. Positive means late; negative means early. | Flights with both a valid scheduled and valid actual arrival time. | Diverted flights may not have a comparable arrival time; show them separately. |
| **On-time performance (OTP)** | Share of eligible flights that departed no more than 15 minutes after their scheduled departure time. | Flights with valid scheduled and actual departure times; cancelled flights and records without a valid actual departure are excluded and counted separately. Diverted flights remain eligible for departure OTP when both departure times are valid, but may be excluded from arrival measures. | This project defines OTP using departure performance. The 15-minute threshold is a convention, not a universal standard; state it next to the figure. |
| **Turnaround time** | Ground time between two consecutive flights on the same aircraft. Scheduled turnaround uses scheduled times; actual turnaround uses actual times. | Consecutive legs on the same aircraft with the required times and a confirmed aircraft link. | Negative or implausibly short turnarounds are data issues, not fast operations. |
| **Eligible connection** | Two consecutive flights on the same aircraft where the previous actual arrival and the next actual departure are both available, the ground time is plausible, and the aircraft link is confirmed (or explicitly included). | Forms the denominator of the delay-propagation rate. | "Connection" here means an aircraft-linked sequence, **not** a passenger connection. Say so on the page. |
| **Potentially affected connection** | An eligible connection where the previous flight arrived late by at least the arrival threshold **and** the next flight departed late by at least the departure threshold. | Subset of eligible connections. | "Potentially affected" is deliberately cautious. It is not proof that the delay was carried forward. |
| **Delay-propagation rate** | Share of eligible connections that are potentially affected. | `potentially affected connections ÷ eligible connections`. | Threshold changes move the rate; always show the active thresholds. Small denominators make the rate unstable — show `n`. |
| **Delayed flight** | A flight with departure delay ≥ the active threshold **or** arrival delay ≥ the active threshold. | Flights with at least one computable delay; default threshold 15 minutes. | A flight delayed on departure but on time on arrival counts as delayed. State whether departure, arrival, or either drives the count. |

### 4.1 Required help text (use or adapt these sentences)

- **Departure delay:** "How late the flight left the gate, compared with its schedule. Positive values are late; negative values are early. Flights without an actual departure time are excluded."
- **Arrival delay:** "How late the flight arrived, compared with its schedule. Positive values are late; negative values are early. Flights without an actual arrival time are excluded."
- **On-time performance:** "The share of eligible flights that departed no more than 15 minutes after schedule. Based on flights with valid scheduled and actual departure times; cancelled flights and records without a valid actual departure are excluded."
- **Turnaround time:** "The ground time between an aircraft's previous arrival and its next departure. Actual turnaround uses actual times; scheduled turnaround uses scheduled times."
- **Delay-propagation rate:** "The share of eligible aircraft-linked connections where a late arrival was followed by a late departure. This is an association, not evidence that the first delay caused the second."
- **Delay threshold:** "Flights at or above this many minutes late are counted as delayed. Changing the threshold recalculates every rate on this page."

### 4.2 Reusable limitations block

Use this block, adapted to the page, at the bottom of analytical pages and in every export:

> **What this view can and cannot tell you**
>
> - Results describe only the flights in the current filter and dataset.
> - Delay propagation is an association between a late arrival and a later departure on the same aircraft. Other factors — crew, maintenance, air traffic control, weather, boarding, and airport operations — may also contribute.
> - Weather overlap shows that delays occurred during certain conditions. It does not show that weather caused them.
> - Missing values are excluded from calculations and shown as "No data", not as zero.
> - Aircraft links marked "Unconfirmed" should not be read as the same aircraft operating both legs.

---

## 5. Page specifications

Each page below defines its purpose, required content, copy, caveats, and user actions.

---

### 5.1 Overview Dashboard

#### Purpose

Give the analyst a one-screen read on the selected flights: how much flying there is, how punctual it is, where delays concentrate, and whether lateness appears to travel between consecutive legs. It is a starting point for investigation, not a verdict.

#### Key content

1. **Scope and provenance strip** — data source badge, date range, flight count, last refresh or generation time.
2. **KPI row** (four or five cards, each with a definition tooltip):
   - Flights analysed — secondary: `of {records} records · {n} excluded`
   - Delayed flights — secondary: `{x}% of flights analysed · threshold {n} min`
   - On-time performance — secondary: `{on-time} of {denominator} eligible flights departed no more than 15 min after schedule`
   - Delay-propagation rate — secondary: `{affected} of {eligible} eligible connections`
   - Average departure delay — secondary: `median {n} min · {count} flights with data`
3. **Flight delay trend** — line chart comparing daily average departure delay and average arrival delay in minutes. Allow a 7-day or 30-day view. Label both axes and show the valid-flight count for each day; mark days with incomplete data.
4. **Average delay by airport** — grouped bar chart of average departure delay and average arrival delay by airport, with `n` valid flights shown for each measure. Pair it with a sortable airport performance table showing departures, arrivals, average departure delay, on-time performance, delay-propagation rate, and `n` for each rate. Do not rank airports below the stated minimum sample size.
5. **Recent delayed flights** — latest 10–20 delayed flights: flight, date, route, scheduled departure, actual departure, departure delay, arrival delay, status. Link each row to Flight Operations.
6. **Small data-quality note** — count of excluded records and a link to Dataset Management.

#### Suggested wording

- Page title: **Overview**
- Page subtitle: "Flight volume, punctuality, and possible delay carry-over for the current selection."
- Section headings: **Network summary**, **Delay trend**, **Airport performance**, **Recent delayed flights**
- KPI labels: **Flights analysed**, **Delayed flights**, **On-time performance**, **Delay-propagation rate**, **Average departure delay**
- KPI help examples:
  - Delayed flights: "Flights at least 15 minutes late on departure or arrival. Threshold can be changed in filters."
  - On-time performance: "Share of eligible flights departing no more than 15 minutes after schedule. Cancelled flights and records without valid departure times are excluded."
  - Delay-propagation rate: "Share of eligible aircraft-linked connections where a late arrival was followed by a late departure. Association, not causation."
- Chart titles: **Average departure and arrival delay by day**, **Average departure and arrival delay by airport**
- Table headings: **Airport**, **Departures**, **Arrivals**, **Avg departure delay**, **On-time performance**, **Propagation rate**, **Flights**
- Empty state: "No flights in this selection. Widen the date range or remove a filter."
- Footer note: "Synthetic sample data — not for operational decisions." (when applicable)

#### Caveats

- All figures describe the filtered subset, not the whole dataset. State this in the subtitle or scope strip.
- The delayed-flight count uses "departure **or** arrival delayed". Say so in the tooltip so it is not confused with departure-based OTP.
- Rates must show denominators; airport rankings must show `n` and should not rank airports below a minimum sample size (suggested: 30 flights).
- Do not describe a high propagation rate as a "delay chain" or "cascade" without the association caveat.
- Missing times reduce denominators; show the excluded count rather than implying full coverage.

#### User actions

- Change date range, airline, origin/destination airport, and delay threshold.
- Reset filters; remove individual filter chips.
- Click a KPI to open Flight Operations with the matching filter applied.
- Click an airport row to open that airport's flights.
- Click a recent delayed flight to open its record.
- Export the airport table or recent delayed flights as CSV.
- Open Dataset Management from the data-quality note.

---

### 5.2 Flight Operations

#### Purpose

Find a specific flight or set of flights and inspect what was scheduled versus what actually happened. This is the record-level page used to verify individual legs and understand data-quality flags.

#### Key content

1. **Search and filter bar**
   - Search with placeholder: "Search flight number, aircraft, airport, or route"
   - Filters: date range, airline, origin, destination, operational status, delay band (`Any delay`, `On time`, `1–14 min`, `15–59 min`, `60+ min`), data quality (`All records`, `Complete records`, `Records with data issues`).
   - Result count: "248 flights · 6 with data issues".
2. **Results table** (sortable, paginated): flight number, date, airline, origin → destination, STD, ATD, departure delay, STA, ATA, arrival delay, status, aircraft, data-quality flag.
   - Keep delay values aligned and signed. Use a subtle delayed/on-time text label in addition to colour.
3. **Flight status distribution** — chart showing counts of On time, Delayed, Cancelled, Diverted, and Unknown flights for the current filters. State the status rules and show counts, not percentages without denominators.
4. **Hourly departures vs delays** — chart showing scheduled departure volume by hour alongside delayed-flight counts or delay rate by hour. Label the time basis and show the denominator for any rate.
5. **Flight record detail** (side panel or expanded row), grouped:
   - **Schedule and actual** — scheduled and actual departure/arrival, with time basis stated.
   - **Delay** — departure delay, arrival delay, active threshold, whether each is computable.
   - **Aircraft and rotation** — aircraft/tail number, previous flight, next flight, link confidence.
   - **Record quality** — missing fields, duplicate flag, invalid sequence flag, source row reference if available.
6. **Status legend** — short definitions for On time, Delayed, Cancelled, Diverted, Unknown.
7. **Data-quality summary strip** — number of records with missing times, invalid times, or unconfirmed links, linking to Dataset Management.

#### Suggested wording

- Page title: **Flight Operations**
- Page subtitle: "Search, filter, and inspect individual flight legs."
- Section headings: **Flight records**, **Flight record**, **Schedule and actual**, **Delay**, **Aircraft and rotation**, **Record quality**
- Labels: **Flight number**, **Date**, **Airline**, **Origin**, **Destination**, **Scheduled departure (STD)**, **Actual departure (ATD)**, **Scheduled arrival (STA)**, **Actual arrival (ATA)**, **Departure delay**, **Arrival delay**, **Operational status**, **Aircraft (tail number)**, **Data quality**
- Help text — departure delay: "Actual departure minus scheduled departure. Positive values are late; negative values are early. Missing actual times are excluded."
- Detail copy when a time is missing: "Actual departure is missing, so departure delay cannot be calculated. This flight is excluded from departure-delay and on-time measures."
- Detail copy for an unconfirmed link: "Aircraft link unconfirmed. The previous or next flight may not be the same aircraft."
- Status definitions:
  - **On time** — "Departure and arrival are both within the active delay threshold. On-time performance (OTP) is a separate departure-based measure using departure time only."
  - **Delayed** — "Departure or arrival delay meets or exceeds the active delay threshold."
  - **Cancelled** — "The flight did not operate. Excluded from delay and on-time measures."
  - **Diverted** — "Landed somewhere other than the scheduled destination. Arrival delay may not be comparable."
  - **Unknown** — "Times are missing or invalid, so punctuality cannot be determined."
- Filtered empty state: "No flights match these filters. Try a different date range, airport, or status."

#### Caveats

- One row represents one flight leg, not a passenger itinerary. The same flight number appears on multiple dates.
- Duplicate records are flagged, not silently dropped. Direct the analyst to the duplicate note in Record quality.
- Invalid times (for example, arrival before departure) are excluded from measures and labelled; do not correct them silently on this page.
- Times are local to each airport. If the app does not convert timezones, say so: "Times are shown as recorded; no timezone conversion is applied."
- Cancelled flights are excluded from delay and OTP rates. Diverted flights can remain in departure-based OTP when both departure times are valid, but are excluded from arrival measures. State this next to the status legend.
- "Unknown" must never be presented as "On time".

#### User actions

- Search by flight number, aircraft, airport, or route.
- Filter by date, airline, airports, status, delay band, and data quality.
- Sort and paginate the results table.
- Select a flight to open its record; move to previous/next record.
- Jump to the aircraft's turnaround or propagation sequence.
- Export the filtered table as CSV.
- Open Dataset Management to review flagged records.

---

### 5.3 Aircraft Turnaround

#### Purpose

Show how long each aircraft actually spent on the ground between flights, how that compares with the schedule, and which turnarounds were shorter or longer than planned.

#### Key content

1. **Aircraft selector** — searchable by tail number, with a default list ordered by number of turnarounds in the selected period. Selected aircraft shows type and flight count.
2. **Turnaround summary** — KPI cards:
   - Turnarounds analysed — `{n}`
   - Average actual turnaround — `{n} min`
   - Median actual turnaround — `{n} min` (optional supporting measure)
   - On-time turnaround — `{n}% ({on-time} of {eligible})`, using the tolerance confirmed by the developer
   - Delayed turnaround — `{n}% ({delayed} of {eligible})`, using the same tolerance; on-time and delayed groups must use the same eligible denominator and non-overlapping threshold rule
   - Median variance vs schedule — `{+n} min`
   - Turnarounds below minimum — `{n} of {total}`
   - Unlinked legs — `{n}`
3. **Rotation timeline** — chronological legs for the aircraft with ground segments between them. Each segment shows scheduled and actual ground time and is labelled "Confirmed" or "Unconfirmed" link.
4. **Turnaround table** — previous flight, previous arrival (scheduled/actual), next flight, next departure (scheduled/actual), scheduled turnaround, actual turnaround, variance, link confidence.
5. **Turnaround time by airport** — bar chart showing average actual turnaround by airport, with sample counts.
6. **Turnaround distribution** — chart of actual turnaround times or variance vs schedule, with units and sample count.
7. **Turnaround detail** — selecting a pair shows both flight records, the ground time calculation, and any data-quality flags.

#### Suggested wording

- Page title: **Aircraft Turnaround**
- Page subtitle: "Scheduled and actual ground time between consecutive flights on the same aircraft."
- Section headings: **Aircraft rotation**, **Turnaround summary**, **Turnaround by airport**, **Turnaround detail**, **Turnaround distribution**
- Labels: **Aircraft (tail number)**, **Previous flight**, **Previous arrival (actual)**, **Next flight**, **Next departure (actual)**, **Scheduled turnaround**, **Actual turnaround**, **Average turnaround**, **On-time turnaround**, **Delayed turnaround**, **Turnaround tolerance**, **Variance vs schedule**, **Minimum turnaround**, **Aircraft link**
- Help text: "Scheduled turnaround is the next scheduled departure minus the previous scheduled arrival. Actual turnaround uses actual times and is shown only when both are available. On-time turnaround means actual turnaround is no more than the confirmed tolerance above schedule; delayed turnaround exceeds that tolerance."
- Link labels: **Confirmed** — "Same aircraft identifier, consecutive in time, with no conflicting leg." / **Unconfirmed** — "The aircraft identifier is missing, reused, or overlaps another leg. Treat this pair as a possible rotation, not a confirmed one."
- Detail copy when a time is missing: "Actual turnaround cannot be calculated because the previous actual arrival (or next actual departure) is missing."
- Detail copy for a negative value: "The calculated turnaround is negative, which indicates a data issue rather than a short turnaround. Check the recorded times."
- Empty state: "No consecutive flights found for this aircraft in the selected period."

#### Caveats

- Actual turnaround requires both actual times. Missing times reduce the sample; show how many pairs were excluded.
- Sequences are built from the aircraft identifier and time order. Missing, duplicated, or reused tail numbers can create false pairs — mark these Unconfirmed.
- Aircraft type changes and same-day tail substitutions can break the sequence. Do not imply continuity that the data does not support.
- Overnight and multi-day ground time is a valid turnaround only if the same aircraft operates the next leg; label long gaps clearly (for example, "overnight ground time").
- Turnaround length alone does not explain a delay. Short ground time may be planned; long ground time may reflect schedule buffer, maintenance, or schedule changes.
- Times are local to each airport; state the time basis and any timezone limitation.

#### User actions

- Select an aircraft by tail number or from the ranked list.
- Filter by date range, minimum scheduled turnaround, and link confidence.
- Inspect a turnaround pair and open either flight record.
- Export the turnaround table as CSV.
- Move to Delay Propagation for the same aircraft.

---

### 5.4 Delay Propagation

#### Purpose

Help the analyst explore whether late arrivals were followed by late departures on the same aircraft, and how often that pattern occurs among connections where the comparison is valid. The page quantifies **possible** propagation; it does not establish cause.

#### Key content

1. **Plain-language explainer** directly under the title: one sentence defining the page's question, plus the association-not-causation callout.
2. **KPI row**, each with denominator:
   - Eligible connections — `2,209`
   - Previous flight arrived late — `612 (27.7% of eligible)`
   - Potentially affected connections — `402`
   - Delay-propagation rate — `18.2% (402 of 2,209)`
   - Average next-flight departure delay for potentially affected connections — `+34 min ({n} potentially affected connections with valid departure delay)`
   - Median departure delay after a late arrival — optional supporting measure
3. **Threshold and eligibility controls**, always visible because they change the rate:
   - Late arrival threshold (default 15 min)
   - Late departure threshold (default 15 min)
   - Minimum ground time (default 30 min)
   - Aircraft link (`Confirmed only` default; `Include unconfirmed`)
4. **Eligibility note** — inline text stating what counts as eligible and what was excluded, with counts.
5. **Connection explorer** — table of aircraft-linked pairs: aircraft, previous flight, previous actual arrival, arrival delay, ground time, next flight, next actual departure, departure delay, assessment, link confidence, with row selection for detail.
6. **Pair detail** — previous leg → ground time → next leg, showing the delay arithmetic and the caveat. Include a "View flights" link to both records.
7. **Scatter plot** — previous arrival delay (x) against next departure delay (y), with threshold lines and the diagonal reference. Label points only on hover; do not crowd the chart.
8. **Summary tables** — propagation rate by airport and by aircraft, with `n` and a minimum-sample note.

#### Suggested wording

- Page title: **Delay Propagation**
- Page subtitle: "Possible carry-over of delay between consecutive flights on the same aircraft."
- Section headings: **Eligible connections**, **Connection explorer**, **Connection detail**, **Patterns by airport**, **Patterns by aircraft**
- KPI labels: **Eligible connections**, **Previous flight arrived late**, **Potentially affected connections**, **Delay-propagation rate**, **Average next-flight departure delay for potentially affected connections** (median may be shown as an additional measure)
- Assessment values: **Potentially affected**, **Late arrival, on-time departure**, **On-time arrival**, **Not assessable — missing times**
- Callout (required, visually distinct but not alarming):
  > **Association, not proof of causation.** A late arrival followed by a late departure on the same aircraft may indicate delay propagation. Crew, maintenance, air traffic control, weather, boarding, and other operational factors may also contribute.
- Eligibility copy:
  > **What counts as an eligible connection?** Two consecutive flights on the same aircraft where the previous actual arrival and the next departure time are both available, the ground time is plausible, and the aircraft link is confirmed (or explicitly included). Connections with missing times or unconfirmed links are excluded from the rate. Delay-propagation rate = potentially affected connections ÷ eligible connections.
- "Connection" clarification (required):
  > In this app, a connection means two consecutive flights operated by the same aircraft. It is not a passenger connection.
- Threshold help: "A connection is potentially affected only when the previous arrival is at least the arrival threshold late **and** the next departure is at least the departure threshold late."
- Rate help: "Share of eligible connections that are potentially affected. The rate changes when thresholds or link-confidence filters change."
- Empty state: "No eligible connections for these filters. Lower the thresholds, widen the date range, or include unconfirmed links."
- Footer: "Potentially affected does not mean caused."

#### Caveats

- **Association, not causation**, stated in the callout and again in any summary or export.
- The rate depends on thresholds, minimum ground time, and link confidence. Always display the active settings next to the figure.
- Small denominators: show `n`; do not rank airports or aircraft with very few eligible connections (suggested minimum: 20).
- Only flights with both required times are eligible. Missing times are excluded, not counted as zero delay.
- Unconfirmed aircraft links must not be presented as confirmed rotations. If included, show them as a separate count or clearly labelled rows.
- A late departure after a late arrival may reflect schedule buffer, a different cause, or a new delay. The dataset does not contain a cause field unless explicitly stated.
- Cancellations and diversions break the sequence. State how they were handled.
- Ground time is not the same as slack: a connection can be "eligible" yet have enough scheduled buffer to absorb the arrival delay.

#### User actions

- Adjust arrival/departure thresholds, minimum ground time, and link confidence.
- Filter by date range, aircraft, and airport.
- Select a connection to inspect both flights.
- Switch between confirmed-only and included-unconfirmed views.
- Export the eligible-connection list and the potentially affected list, with definitions and settings in the file header.
- Open the same aircraft in Aircraft Turnaround.

---

### 5.5 Weather Analysis

#### Purpose

Add weather context to delay patterns: under which recorded conditions did delays occur, and how complete is the weather coverage? The page supports exploration, not attribution.

#### Key content

1. **Weather coverage banner** — matched flights, total flights, percentage, and count without weather records. Example: "Weather records matched to 9,840 of 12,480 flights (78.8%). 2,640 flights have no weather record and are excluded from weather comparisons."
2. **Condition summary** — KPIs:
   - Weather-matched flights — `{x} of {y} flights`
   - Weather-associated delayed flights — `{n}` (describe as overlap, not cause)
   - Share of all delayed flights with matched weather records — `{p}% ({n} of {total delayed flights})`
   - Average delay among flights with matched weather — `{n} min ({x} flights with computable delay)`; label by condition where applicable and describe it as overlap, not weather-caused delay
   - Delay rate by condition group — `{p}% ({n} delayed of {m} flights)` for each group
   - Missing weather records — `{n}`
3. **Filters** — date range, airport, weather condition (multi-select), visibility band, precipitation, and a toggle **Include flights without weather records** (default off, with an explanatory tooltip: "Including these flights shows missingness but does not assign them a weather condition.").
4. **Weather delay distribution** — retain a clear distribution view of delay minutes by recorded weather condition, with counts and units.
5. **Delay rate by condition** — bar chart with counts on hover or in a companion table. Conditions: Clear, Cloudy, Rain, Snow, Fog, Thunderstorm, Other, Unknown.
6. **Airport weather summary** — table: airport, flights with weather data, most common condition, delay rate by condition group, coverage percentage.
7. **Flight-level weather records** — table of flights with observation time, condition, temperature, wind, visibility, and precipitation, linking to the flight record.
8. **Missing-data treatment** — visibly separate group labelled **No weather record**, never folded into "Clear".

#### Suggested wording

- Page title: **Weather Analysis**
- Page subtitle: "Recorded weather conditions and how delays lined up with them."
- Section headings: **Weather coverage**, **Conditions in the selected period**, **Delay patterns by condition**, **Airport weather summary**, **Flight weather records**
- Labels: **Weather condition**, **Observation time**, **Temperature (°C)**, **Wind speed (kt)**, **Visibility (km)**, **Precipitation (mm)**, **Matched to flight**, **No weather record**
- Help text: "Weather is matched to each flight using the airport and the observation nearest the flight event. Matching rules and time tolerance are listed in Dataset Management."
- Required callout:
  > **Weather overlap does not prove weather caused a delay.** Delays during rain, fog, or high winds may also reflect airport capacity, air traffic control, crew, maintenance, or other factors.
- Missing-value copy: "No weather record — this flight is excluded from weather comparisons. It does not mean conditions were clear."
- Condition help: "Conditions are grouped from the recorded weather observation. 'Unknown' means a record exists but the condition could not be classified."
- Empty state: "No weather records match these filters."

#### Caveats

- Coverage is rarely complete. Always show the matched count and percentage above any weather comparison.
- Missing weather is not "clear weather" and must not be treated as a condition category with zero delay.
- The weather station may not be the airport itself. State the matching basis and any distance/time tolerance.
- Observation time is not the same as the time of the delay. Nearest-observation matching introduces uncertainty.
- Sample sizes per condition can be small; show `n` on every bar and suppress comparisons below a minimum (suggested: 20 flights).
- Weather can be seasonal and correlated with traffic volume. Do not present a condition comparison as a controlled analysis.
- If weather data is synthetic, label it as synthetic alongside the flight data.

#### User actions

- Filter by date range, airport, condition, and visibility/precipitation bands.
- Toggle display of flights without weather records.
- Select a flight to view its weather record and open the flight record.
- Export the weather summary and flight-level records as CSV.
- Open Dataset Management to review weather matching and missingness.

---

### 5.6 Dataset Management

#### Purpose

Load a dataset and judge whether it is fit for analysis. The page must make the data source, record counts, missingness, duplicates, invalid records, and cleaning results fully visible before the analyst trusts any other page.

#### Key content

1. **Data source card**
   - Current source: **Synthetic sample data** or **Uploaded data — {filename}**
   - File name, upload time, date coverage, row count
   - Actions: **Upload data**, **Use sample data**, **Remove uploaded data**
   - Persistence statement: state plainly whether the upload is kept only for the session or saved (developer to confirm; see Section 9).
2. **Upload panel**
   - Drop zone: "Drag and drop a CSV file here, or browse."
   - Short requirements: "Required: flight identifier, date, origin, destination, scheduled and actual times, aircraft identifier."
   - **Download CSV template** and **View required fields**.
3. **Summary cards**
   - Rows received
   - Valid flights
   - Records corrected
   - Records rejected
   - Records removed (including duplicates, with reason)
   - Records excluded from specific measures
   - Fields with missing values
   - Date coverage
4. **Original and cleaned previews** — allow the analyst to switch between the uploaded original rows and the cleaned rows, preserving source-row references. Show the first 20 rows, column names, inferred types (Text, Date, Time, Number), and the note "Preview only — analysis uses the cleaned dataset." Do not silently reorder columns.
5. **Validation summary** — table with Check, Result (`Passed`, `Warning`, `Failed`), Records affected, and What happens. Checks to include:
   - Missing flight identifier
   - Unreadable date or time values
   - Invalid time sequence (arrival before departure)
   - Duplicate flight records
   - Missing aircraft identifier
   - Unknown or malformed airport codes
   - Aircraft sequence gaps
   - Negative turnaround
   - Missing weather records
6. **Cleaning results** — ordered log with counts and plain-language rules, for example: "Trimmed whitespace in 214 values", "Standardised 38 airport codes", "Removed 96 exact duplicates", "Excluded 41 records with an arrival before departure". End with the explicit statement: **"No missing value was replaced with zero."**
7. **Issues table and export** — filter by severity and field; export all issues with record references and reasons.
8. **Impact note** — "Cleaning changes the record counts used across the app. Figures on other pages reflect the cleaned dataset."

#### Suggested wording

- Page title: **Dataset Management**
- Page subtitle: "Load flight data and check its quality before relying on the analysis."
- Section headings: **Data source**, **Upload data**, **Summary**, **Preview**, **Validation summary**, **Cleaning results**, **Records with issues**
- Labels: **Rows received**, **Valid flights**, **Records corrected**, **Records rejected**, **Records removed**, **Records excluded from measures**, **Duplicates removed**, **Missing values**, **Date coverage**, **Original data**, **Cleaned data**, **Field**, **Check**, **Result**, **Records affected**, **What happens**
- Source help:
  - Synthetic: "Sample records generated for demonstration. They do not represent real flights or airlines. Do not use them for operational decisions."
  - Uploaded: "Your file, cleaned using the rules below. It has not been verified against an airline source."
- Validation status help:
  - **Passed** — "No records affected by this check."
  - **Warning** — "Records were affected but are usable with the stated limitation."
  - **Failed** — "Affected records were excluded from analysis."
- Cleaning log intro: "These rules were applied in order. Counts show affected records or values."
- Upload error: "This file could not be read. Check that it is a CSV with a header row and try again."
- Remove confirmation: "Remove this uploaded dataset? The app will return to the synthetic sample data. This cannot be undone."
- Privacy note for uploaded operational data: "Treat uploaded operational data as confidential. Do not upload data you are not authorised to use."

#### Caveats

- Synthetic sample data must be labelled on this page and everywhere it flows.
- Cleaning changes totals. Show before/after counts so the analyst can reconcile pages.
- Corrected records are listed with the rule applied; invalid records are excluded, not silently fixed. Every exclusion needs a reason and a record reference.
- Missing values are reported per field and never filled with zero or an average unless a rule is explicitly listed.
- Duplicate detection uses a stated rule (for example, same flight number, date, origin, and scheduled departure). State the rule; do not imply duplicates are always identical rows.
- Uploaded data may not cover the date range or airports the analyst expects. Show coverage explicitly.
- Weather matching coverage belongs here as well as on Weather Analysis; a flight can be valid for delay analysis but unmatched for weather.

#### User actions

- Upload a CSV, download the template, and review required fields.
- Switch to synthetic sample data or remove the uploaded dataset.
- Preview columns and types; filter the preview.
- Filter validation issues by severity and field; export issues as CSV.
- Open affected records in Flight Operations.
- Confirm cleaning results before moving to analysis pages.

---

### 5.7 Reports & Insights

#### Purpose

Bring the analysis together into a reviewable summary with its scope and limitations attached, so findings can be shared without losing context.

#### Key content

1. **Report scope block** — data source, date range, active filters, flights analysed, eligible connections, weather coverage, generated timestamp. This block repeats in every export.
2. **Summary** — 3–5 short bullets generated from the current filters, each with a numerator and denominator. Example structure, not fixed copy:
   - "On-time performance was 68.7% (8,568 of 12,480 eligible flights departed no more than 15 minutes after schedule)."
   - "The delay-propagation rate was 18.2% (402 of 2,209 eligible connections)."
   - "Weather records were available for 78.8% of flights (9,840 of 12,480)."
3. **Performance summary** — KPIs and the delay trend, with threshold stated.
4. **Airport patterns** — highest and lowest on-time performance, highest average departure delay, highest propagation rate. Always show `n` and a minimum-sample note; label "Ranked among airports with at least 30 flights."
5. **Aircraft patterns** — aircraft with the most turnarounds below the minimum, largest median turnaround variance, and highest propagation rate — with `n`, and a caution that rankings are descriptive.
6. **Delay summary** — delays by code/category, departure vs arrival, and the share of flights with no delay code. If delay codes are unavailable, say so rather than showing an empty chart.
7. **Propagation summary** — eligible connections, potentially affected count, rate, active thresholds, and the association caveat.
8. **Weather summary** — coverage and delay rates by condition group, with the overlap caveat.
9. **Limitations and interpretation** — the reusable limitations block (Section 4.2), plus page-specific notes on ranking thresholds and excluded records.
10. **Export** — **Download report (PDF)**, **Download data (CSV)**, **Print**. Exports include scope, definitions, caveats, and the data-source badge.

#### Suggested wording

- Page title: **Reports & Insights**
- Page subtitle: "A summary of the current selection, with scope and limitations included."
- Section headings: **Report scope**, **Summary**, **Performance summary**, **Airport patterns**, **Aircraft patterns**, **Delay summary**, **Propagation summary**, **Weather summary**, **Limitations and interpretation**, **Export**
- Scope labels: **Data source**, **Date range**, **Filters applied**, **Flights analysed**, **Eligible connections**, **Weather coverage**, **Generated**
- Ranking note: "Ranked among airports with at least 30 flights. Small samples are excluded."
- Empty ranking: "Not enough data to rank airports for this selection."
- Export note: "Exports include the data source, filters, definitions, and limitations."
- Synthetic-data export line: "Synthetic sample data — not for operational decisions."

#### Caveats

- Auto-generated sentences must include denominators and must not assert causation. Review templates for phrases such as "driven by", "due to", "caused by", and "worst".
- Rankings are descriptive, not performance judgements. Use "highest" and "lowest", not "best" and "worst".
- Suppress or flag rankings below the minimum sample; show the threshold used.
- Every export carries the data-source badge and generation timestamp; a report must not look like a live operational snapshot.
- If sections have no data (for example, no delay codes), say so explicitly instead of hiding the section silently.
- The report reflects the filters at generation time. State that changing filters requires regenerating the report.

#### User actions

- Set report scope: date range, filters, and data source.
- Include or exclude optional sections.
- Preview the report before export.
- Download PDF, download underlying tables as CSV, or print.
- Copy summary text for use in an email or ticket.

---

## 6. Cross-page terminology

| Use | Avoid | Reason |
|---|---|---|
| flight, flight leg | segment, journey | Avoid confusion with passenger itineraries. |
| aircraft (tail number) | plane, tail | Plain and unambiguous on first use. |
| delayed | late (as a general synonym) | Use "delayed" for flight status and counts. Reserve "late arrival" and "late departure" for the two conditions in a connection. |
| departure delay / arrival delay | delay (unqualified) | The two measures differ and have different denominators. |
| possible delay propagation | delay cascade, knock-on effect | "Cascade" and "knock-on" imply causation. |
| aircraft-linked connection | connection | In aviation, "connection" usually means a passenger connection. Always qualify it. |
| weather overlapped with delays | weather-related delays, weather delays | The data shows overlap, not attribution. |
| no data / not available | 0, N/A, blank | Missing must not read as zero. |
| unconfirmed aircraft link | linked flight, same aircraft | Only confirmed links should be stated as fact. |
| synthetic sample data | demo data, test data, sample live data | Must be unmistakably non-operational. |
| uploaded data | live data, real data | Uploaded data is unverified. |

### 6.1 Status and quality vocabulary

| Group | Values | Meaning |
|---|---|---|
| Operational status | On time, Delayed, Cancelled, Diverted, Unknown | Punctuality of an individual flight. "Unknown" is not on time. |
| Validation result | Passed, Warning, Failed | Dataset check outcome; Failed records are excluded. |
| Aircraft link | Confirmed, Unconfirmed, Not linked | Confidence that two legs belong to the same aircraft sequence. |
| Delay-propagation assessment | Potentially affected, Late arrival with on-time departure, On-time arrival, Not assessable — missing times | Deliberately cautious labels; none asserts cause. |
| Data source | Synthetic sample data, Uploaded data, Public reference data | Provenance; shown on every page and export. |

---

## 7. Content acceptance checklist

Before a page is considered ready:

- [ ] Page title, subtitle, and section headings match this brief.
- [ ] Every KPI has a definition tooltip with its denominator.
- [ ] Every rate shows `n of N`, and the eligible population is stated.
- [ ] OTP uses the project-required departure-based definition (≤15 minutes after scheduled departure).
- [ ] Required charts are present: departure vs arrival delay trend, average delay by airport, flight status distribution, hourly departures vs delays, and turnaround time by airport.
- [ ] Required KPIs include average turnaround, on-time/delayed turnaround percentages, average propagated departure delay, and weather-associated delayed-flight count/share/average delay.
- [ ] Dataset Management previews both original and cleaned data and reports valid, corrected, rejected, and removed record counts.
- [ ] The data-source badge is visible, and synthetic data is not described as real or live.
- [ ] Missing values read "No data" / "Not available", never `0`.
- [ ] Unconfirmed aircraft links are labelled and not presented as confirmed rotations.
- [ ] Propagation and weather pages include the association-not-causation callout.
- [ ] The active delay threshold is visible wherever "delayed" is used.
- [ ] Filtered views state their scope, and reset/remove filter actions exist.
- [ ] Empty, loading, and error states use the copy in Section 3.5.
- [ ] Exports include source, filters, definitions, and caveats.
- [ ] Status is conveyed by text as well as colour.
- [ ] No decorative illustrations, animation, or generic dashboard filler.
- [ ] No sentence gives operational advice or implies causation.

---

## 8. Suggested page-level copy summary

| Page | Title | One-line subtitle |
|---|---|---|
| 1 | Overview | Flight volume, punctuality, and possible delay carry-over for the current selection. |
| 2 | Flight Operations | Search, filter, and inspect individual flight legs. |
| 3 | Aircraft Turnaround | Scheduled and actual ground time between consecutive flights on the same aircraft. |
| 4 | Delay Propagation | Possible carry-over of delay between consecutive flights on the same aircraft. |
| 5 | Weather Analysis | Recorded weather conditions and how delays lined up with them. |
| 6 | Dataset Management | Load flight data and check its quality before relying on the analysis. |
| 7 | Reports & Insights | A summary of the current selection, with scope and limitations included. |

---

## 9. Open questions for the developer

These require a product or implementation decision. The brief avoids deciding them, but the UI must state the answer once chosen.

1. **Time basis** — Are times stored and displayed in airport local time, UTC, or a mix? If no conversion is applied, the UI must say so.
2. **OTP definition** — The project requirement defines OTP as eligible flights departing no more than 15 minutes after scheduled departure. Confirm this departure-based measure and the treatment of cancelled flights and records without actual departure times.
3. **Delayed-flight definition** — Confirm "departure or arrival at or above threshold" and the default threshold of 15 minutes.
4. **Upload persistence** — Are uploaded files kept only for the session or stored between sessions? The Dataset Management page must state which.
5. **Weather matching** — Which station and time tolerance are used to match observations to flights? The Weather Analysis page must state it.
6. **Duplicate rule** — Which fields define a duplicate flight record? The Dataset Management page must state the rule.
7. **Minimum sample thresholds** — Confirm the minimum `n` for ranking airports, aircraft, and weather conditions (suggested: 30 flights, 20 connections, 20 flights per condition).
8. **Turnaround tolerance** — Confirm the minutes-over-schedule threshold used to classify on-time versus delayed turnarounds; show it beside both rates.
9. **Export formats** — Confirm PDF and CSV as the supported exports.
10. **Delay-code coverage** — Are delay codes available in the initial synthetic data? If not, the Reports page should say so rather than showing an empty category chart.
