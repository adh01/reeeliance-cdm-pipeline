"""Map raw records to the CDM entities Contact and SalesOrder."""
import logging

from cleaning import clean_email, split_name, to_decimal, to_iso8601, to_statecode

log = logging.getLogger(__name__)


def _reject(rejected, row, record_id, reason):
    """Log a bad record and keep it in the quarantine list with the reason."""
    log.warning("%s: %s -> quarantine", record_id or "<no id>", reason)
    rejected.append({**row, "reject_reason": reason})


def to_contacts(raw_customers):
    """raw_customers.csv -> CDM Contact. Returns (contacts, rejected)."""
    contacts = []
    rejected = []
    seen_ids = set()
    for row in raw_customers:
        contact_id = row["cust_id"].strip()
        if not contact_id:
            _reject(rejected, row, contact_id, "missing cust_id")
            continue
        if contact_id in seen_ids:
            _reject(rejected, row, contact_id, "duplicate id")
            continue
        seen_ids.add(contact_id)

        firstname, lastname = split_name(row["full_name"])

        email = clean_email(row["email_addr"])
        if email is None:
            log.warning("Invalid email for %s: %r -> set to empty", contact_id, row["email_addr"])

        createdon = to_iso8601(row["signup_date"])
        if createdon is None:
            log.warning("Unknown date for %s: %r", contact_id, row["signup_date"])

        statecode = to_statecode(row["user_status"])
        if statecode is None:
            log.warning("Unknown status for %s: %r", contact_id, row["user_status"])

        contacts.append({
            "contactid": contact_id,
            "firstname": firstname,
            "lastname": lastname,
            "emailaddress1": email,
            "createdon": createdon,
            "statecode": statecode,
        })
    log.info("Transformed %d contacts, %d rejected", len(contacts), len(rejected))
    return contacts, rejected


def to_sales_orders(raw_orders, contacts):
    """raw_orders.csv -> CDM SalesOrder. Returns (orders, rejected).

    Orders with a duplicate id, an unknown customer (orphan), an invalid amount
    or an invalid timestamp are not loaded but kept in quarantine with the reason.
    """
    known_ids = {c["contactid"] for c in contacts}
    orders = []
    rejected = []
    seen_ids = set()
    for row in raw_orders:
        order_id = row["tx_id"].strip()
        customer_id = row["customer_id"].strip()

        if order_id in seen_ids:
            _reject(rejected, row, order_id, "duplicate id")
            continue
        if customer_id not in known_ids:
            _reject(rejected, row, order_id, f"orphan: customer {customer_id} not found")
            continue

        amount = to_decimal(row["amount_usd"])
        if amount is None:
            _reject(rejected, row, order_id, "invalid amount")
            continue

        createdon = to_iso8601(row["tx_timestamp"])
        if createdon is None:
            _reject(rejected, row, order_id, "invalid timestamp")
            continue

        seen_ids.add(order_id)
        orders.append({
            "salesorderid": order_id,
            "customerid": customer_id,
            "totalamount": amount,
            "createdon": createdon,
        })
    log.info("Transformed %d sales orders, %d rejected", len(orders), len(rejected))
    return orders, rejected
