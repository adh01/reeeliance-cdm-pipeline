"""Read raw CSV files, including rows that are broken over two lines."""
import csv
import logging

log = logging.getLogger(__name__)


def read_csv(path):
    """Read a CSV file. Returns (records, malformed).

    records:   list of dicts, one per row.
    malformed: rows that cannot be repaired, kept with the reason for the quarantine.

    If a row has fewer fields than the header, it was broken by a line break
    inside a value (like 'CST-005, Charlie Brown' in raw_customers.csv).
    We glue it together with the next line. A row with too many fields cannot
    be mapped safely and goes to the quarantine.
    """
    # utf-8-sig also reads files saved by Excel, which start with a hidden BOM character.
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [row for row in csv.reader(f) if row]

    if not rows:
        log.error("File is empty: %s", path)
        return [], []

    header = [h.strip() for h in rows[0]]
    records = []
    malformed = []
    current = None

    for row in rows[1:]:
        if current is None:
            current = row
        else:
            # Glue: last value of the broken row + first value of the next line.
            current = current[:-1] + [current[-1] + row[0]] + row[1:]
            log.warning("Repaired a row that was split over two lines: %s", current[0])

        if len(current) == len(header):
            records.append(dict(zip(header, current)))
            current = None
        elif len(current) > len(header):
            log.error("Row with %d fields instead of %d -> quarantine: %s", len(current), len(header), current)
            malformed.append({"raw_row": ",".join(current), "reject_reason": "wrong number of fields"})
            current = None

    if current is not None:
        log.error("Incomplete last row -> quarantine: %s", current)
        malformed.append({"raw_row": ",".join(current), "reject_reason": "incomplete row"})

    log.info("Read %d rows from %s (%d malformed)", len(records), path, len(malformed))
    return records, malformed
