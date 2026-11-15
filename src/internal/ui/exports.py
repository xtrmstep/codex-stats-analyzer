"""Stable UTF-8 CSV exports of already-rendered analytics tables."""

import csv
import io

def csv_bytes(rows, columns):
    """Export table rows with stable headers, empty unknowns and UTF-8 BOM."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(columns.values()), lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({destination: "" if row.get(source) is None else row.get(source, "")
                         for source, destination in columns.items()})
    return buffer.getvalue().encode("utf-8-sig")

