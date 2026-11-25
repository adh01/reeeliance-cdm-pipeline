"""Run the whole pipeline: extract -> transform -> load -> manifest."""
import logging
import os
from pathlib import Path

from extract import read_csv
from load import write_entity, write_rejected
from manifest import build_manifest, columns, write_manifest
from transform import to_contacts, to_sales_orders

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = Path("data") / "raw"
LAKEHOUSE_DIR = Path("cdm_lakehouse")
LOG_FILE = Path("pipeline.log")


def main():
    os.chdir(ROOT)  # all paths are relative to the project folder
    if (LAKEHOUSE_DIR / "_rejected").exists():
        for old in (LAKEHOUSE_DIR / "_rejected").glob("*.csv"):
            old.unlink()  # start each run with a clean quarantine

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="w")],
    )

    # 1. Extract
    raw_customers = read_csv(RAW_DIR / "raw_customers.csv")
    raw_orders = read_csv(RAW_DIR / "raw_orders.csv")

    # 2. Transform
    contacts, rejected_contacts = to_contacts(raw_customers)
    orders, rejected_orders = to_sales_orders(raw_orders, contacts)

    # 3. Load
    locations = {
        "Contact": write_entity(contacts, columns("Contact"), LAKEHOUSE_DIR, "Contact"),
        "SalesOrder": write_entity(orders, columns("SalesOrder"), LAKEHOUSE_DIR, "SalesOrder"),
    }

    # Quarantine: rejected records are kept, not thrown away
    write_rejected(rejected_contacts, LAKEHOUSE_DIR, "Contact")
    write_rejected(rejected_orders, LAKEHOUSE_DIR, "SalesOrder")

    # 4. Manifest
    write_manifest(build_manifest(locations), LAKEHOUSE_DIR)


if __name__ == "__main__":
    main()
