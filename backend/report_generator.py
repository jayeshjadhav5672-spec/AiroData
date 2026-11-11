from __future__ import annotations

from io import BytesIO
from datetime import datetime, timezone
from html import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether


NAVY = colors.HexColor("#0F2742")
BLUE = colors.HexColor("#3E6E9E")


def build_analytical_pdf(flights: pd.DataFrame, rotations: pd.DataFrame, source: str, date_range: str, filters: str = "None") -> bytes:
    """Build a compact PDF summary that carries scope and analytical caveats."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=17 * mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AeroTitle", parent=styles["Title"], textColor=NAVY, alignment=0, fontSize=20, leading=24, spaceAfter=4))
    styles.add(ParagraphStyle(name="AeroSection", parent=styles["Heading2"], textColor=NAVY, fontSize=12, leading=15, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="AeroBody", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#1F2937")))
    styles.add(ParagraphStyle(name="AeroSmall", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569")))
    story = [Paragraph("AeroData — Airline Operations &amp; Delay Analytics", styles["AeroTitle"]),
             Paragraph("Analytical summary", styles["AeroSection"])]
    story.append(Paragraph(f"Data source: {escape(source)}<br/>Date range: {escape(date_range)}<br/>Filters: {escape(filters)}<br/>Generated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}<br/>Flights in scope: {len(flights):,}", styles["AeroBody"]))
    story.append(Spacer(1, 5 * mm))

    dep = pd.to_numeric(flights.get("departure_delay_min", pd.Series(dtype=float)), errors="coerce")
    arr = pd.to_numeric(flights.get("arrival_delay_min", pd.Series(dtype=float)), errors="coerce")
    otp_mask = flights.get("otp_eligible", pd.Series(False, index=flights.index)).fillna(False).astype(bool)
    otp = flights.loc[otp_mask, "on_time_departure"].fillna(False).mean() * 100 if otp_mask.any() and "on_time_departure" in flights else None
    delayed = flights.get("delayed", pd.Series(False, index=flights.index)).fillna(False).astype(bool)
    eligible = rotations.get("eligible", pd.Series(False, index=rotations.index)).fillna(False).astype(bool)
    affected = rotations.get("potentially_affected", pd.Series(False, index=rotations.index)).fillna(False).astype(bool)
    prop_rate = affected[eligible].mean() * 100 if eligible.any() else None
    potentially_affected = eligible & affected
    avg_propagated_dep = pd.to_numeric(rotations.loc[potentially_affected, "next_departure_delay_min"], errors="coerce").mean() if potentially_affected.any() and "next_departure_delay_min" in rotations else None

    metric_rows = [["Measure", "Result", "Basis"]]
    metric_rows.append(["Flights analysed", f"{len(flights):,}", "Records in the selected scope"])
    metric_rows.append(["Delayed flights", f"{int(delayed.sum()):,}", "Departure or arrival delay ≥ 15 min"])
    metric_rows.append(["Departure OTP", f"{otp:.1f}%" if otp is not None else "Not available", f"{int(otp_mask.sum()):,} eligible flights; departure delay ≤ 15 min"])
    metric_rows.append(["Average departure delay", f"{dep.mean():+.1f} min" if dep.notna().any() else "Not available", f"{int(dep.notna().sum()):,} flights with valid times"])
    metric_rows.append(["Average arrival delay", f"{arr.mean():+.1f} min" if arr.notna().any() else "Not available", f"{int(arr.notna().sum()):,} flights with valid times"])
    metric_rows.append(["Delay-propagation rate", f"{prop_rate:.1f}%" if prop_rate is not None else "Not available", f"{int(eligible.sum()):,} eligible aircraft-linked connections; {int(affected.sum()):,} potentially affected"])
    metric_rows.append(["Average next departure delay for potentially affected connections", f"{avg_propagated_dep:+.1f} min" if avg_propagated_dep is not None and pd.notna(avg_propagated_dep) else "Not available", f"{int(potentially_affected.sum()):,} potentially affected connections with valid departure delay"])
    table = Table(metric_rows, colWidths=[42 * mm, 30 * mm, 100 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, BLUE), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([Paragraph("Summary measures", styles["AeroSection"]), table])
    story.append(Paragraph("Interpretation", styles["AeroSection"]))
    if len(flights):
        story.append(Paragraph(f"{int(delayed.sum()):,} of {len(flights):,} flights meet the configured delayed-flight definition. Departure OTP is {otp:.1f}% across eligible flights." if otp is not None else f"{int(delayed.sum()):,} of {len(flights):,} flights meet the configured delayed-flight definition. Departure OTP is not available for this selection.", styles["AeroBody"]))
        story.append(Paragraph("Aircraft-linked delay patterns are associations, not proof that an earlier flight caused a later delay. Other operational factors may contribute.", styles["AeroBody"]))
    else:
        story.append(Paragraph("No flights are available for this scope, so summary measures cannot be calculated.", styles["AeroBody"]))
    story.append(Paragraph("Limitations and data source", styles["AeroSection"]))
    source_note = "Synthetic sample figures are for demonstration and not operational decisions." if "Synthetic" in source else "Uploaded data has not been verified against an airline or airport source."
    caveats = [
        f"Data source: {source}. {source_note}",
        "Missing values are not treated as zero; each measure uses only records with the required fields.",
        "Delay propagation is an association between aircraft-linked flights, not evidence of causation.",
        "Weather overlap does not establish that weather caused a delay.",
        "This report reflects only the stated date range and filters at generation time.",
    ]
    story.append(Paragraph("<br/>".join("• " + item for item in caveats), styles["AeroSmall"]))
    doc.build(story)
    return buffer.getvalue()
