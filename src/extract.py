"""Read raw CSV files, including rows that are broken over two lines."""
import csv
import logging

log = logging.getLogger(__name__)


def read_csv(path):
    """Read a CSV file into a list of dicts.

    If a row has fewer fields than the header, it was broken by a line break
    inside a value (like 'CST-005, Charlie Brown' in raw_customers.csv).
    We glue it together with the next line.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    header = [h.strip() for h in rows[0]]
    records = []
    current = None

    for row in rows[1:]:
        if not row:
            continue
        if current is None:
            current = row
        else:
            # Glue: last value of the broken row + first value of the next line.
            current = current[:-1] + [current[-1] + row[0]] + row[1:]
            log.warning("Repaired a row that was split over two lines: %s", current[0])

        if len(current) >= len(header):
            records.append(dict(zip(header, current)))
            current = None

    if current is not None:
        log.error("Incomplete last row skipped: %s", current)

    log.info("Read %d rows from %s", len(records), path)
    return records
