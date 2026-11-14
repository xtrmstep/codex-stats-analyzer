"""Stable UTF-8 CSV exports of already-rendered analytics tables."""

import csv
import io

RUN_COLUMNS = {"Run ID": "run_id", "Run": "run_name", "Session": "session_id", "Tokens": "total_tokens", "Coverage": "coverage", "Attribution": "attribution", "Outcome": "outcome", "Task type": "task_type", "Explicit labels": "explicit_labels", "Inherited labels": "inherited_labels", "Full run elapsed seconds": "elapsed_seconds", "Elapsed provenance": "elapsed_provenance", "Diagnostics": "diagnostics"}
COMPARISON_COLUMNS = {"Group": "group", "Runs": "run_count", "Metric": "metric", "Unit": "unit", "Value": "value", "Eligible": "eligible_runs", "Total": "total_runs", "Provenance": "provenance", "Difference from baseline": "difference_from_baseline", "Difference %": "difference_percent"}


def csv_bytes(rows, columns):
    """Export table rows with stable headers, empty unknowns and UTF-8 BOM."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(columns.values()), lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({destination: "" if row.get(source) is None else row.get(source, "")
                         for source, destination in columns.items()})
    return buffer.getvalue().encode("utf-8-sig")

