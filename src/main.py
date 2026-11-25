"""Run the whole pipeline: extract -> transform -> load -> manifest."""
import logging
from pathlib import Path

from extract import read_csv
from load import write_entity
from manifest import build_manifest, columns, write_manifest
from transform import to_contacts, to_sales_orders

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
LAKEHOUSE_DIR = ROOT / "cdm_lakehouse"
LOG_FILE = ROOT / "pipeline.log"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="w")],
    )

    # 1. Extract
    raw_customers = read_csv(RAW_DIR / "raw_customers.csv")
    raw_orders = read_csv(RAW_DIR / "raw_orders.csv")

    # 2. Transform
    contacts = to_contacts(raw_customers)
    orders = to_sales_orders(raw_orders, contacts)

    # 3. Load
    locations = {
        "Contact": write_entity(contacts, columns("Contact"), LAKEHOUSE_DIR, "Contact"),
        "SalesOrder": write_entity(orders, columns("SalesOrder"), LAKEHOUSE_DIR, "SalesOrder"),
    }

    # 4. Manifest
    write_manifest(build_manifest(locations), LAKEHOUSE_DIR)


if __name__ == "__main__":
    main()
