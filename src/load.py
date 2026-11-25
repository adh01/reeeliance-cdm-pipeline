"""Write the clean entities into the CDM folder structure."""
import csv
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def write_entity(records, columns, lakehouse_dir, entity_name):
    """Write records to <lakehouse>/<Entity>/<Entity>.csv. None becomes an empty field."""
    folder = Path(lakehouse_dir) / entity_name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entity_name}.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow({col: "" if record[col] is None else record[col] for col in columns})

    log.info("Wrote %d rows to %s", len(records), path)
    return f"{entity_name}/{entity_name}.csv"
