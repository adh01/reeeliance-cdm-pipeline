"""Build the CDM model.json manifest from one schema definition."""
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# One place that defines the target schema. The CSV writer and model.json both use it.
ENTITIES = {
    "Contact": {
        "description": "Standard CDM Contact entity for individual customers",
        "attributes": [
            ("contactid", "string", "Unique primary key for the contact"),
            ("firstname", "string", "First name of the contact"),
            ("lastname", "string", "Last name of the contact"),
            ("emailaddress1", "string", "Primary email address"),
            ("createdon", "dateTime", "ISO 8601 creation timestamp"),
            ("statecode", "int64", "Status code: 0 for Active, 1 for Inactive"),
        ],
    },
    "SalesOrder": {
        "description": "Standard CDM SalesOrder entity for transactions",
        "attributes": [
            ("salesorderid", "string", "Unique order identifier"),
            ("customerid", "string", "Foreign key reference to Contact"),
            ("totalamount", "decimal", "Total order amount in USD"),
            ("createdon", "dateTime", "ISO 8601 transaction timestamp"),
        ],
    },
}


def columns(entity_name):
    return [name for name, _, _ in ENTITIES[entity_name]["attributes"]]


def build_manifest(locations):
    """locations: {'Contact': 'Contact/Contact.csv', ...}"""
    entities = []
    for name, spec in ENTITIES.items():
        entities.append({
            "$type": "LocalEntity",
            "name": name,
            "description": spec["description"],
            "attributes": [
                {"name": a, "dataType": t, "description": d} for a, t, d in spec["attributes"]
            ],
            "partitions": [{
                "name": f"{name}Partitions",
                "location": locations[name],
                "fileFormatSettings": {
                    "$type": "CsvFormatSettings",
                    "columnHeaders": True,
                    "delimiter": ",",
                },
            }],
        })

    return {
        "name": "EnterpriseDataLake",
        "description": "CDM Manifest for Ingested Customer and Sales Data",
        "version": "1.0",
        "entities": entities,
        "relationships": [{
            "$type": "SingleKeyRelationship",
            "name": "Contact_SalesOrder_Relationship",
            "fromAttribute": {"entityName": "SalesOrder", "attributeName": "customerid"},
            "toAttribute": {"entityName": "Contact", "attributeName": "contactid"},
        }],
    }


def write_manifest(manifest, lakehouse_dir):
    path = Path(lakehouse_dir) / "model.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest to %s", path)
