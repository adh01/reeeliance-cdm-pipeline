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


def write_rejected(records, lakehouse_dir, entity_name):
    """Write rejected raw records with their reason to <lakehouse>/_rejected/<Entity>_rejected.csv."""
    if not records:
        return None
    folder = Path(lakehouse_dir) / "_rejected"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entity_name}_rejected.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        # Malformed rows have other keys than mapped rows, so collect all keys in order.
        fieldnames = list(dict.fromkeys(key for record in records for key in record))
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    log.warning("Wrote %d rejected rows to %s", len(records), path)
    return path
