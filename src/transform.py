"""Map raw records to the CDM entities Contact and SalesOrder."""
import logging

from cleaning import clean_email, split_name, to_decimal, to_iso8601, to_statecode

log = logging.getLogger(__name__)


def to_contacts(raw_customers):
    """raw_customers.csv -> CDM Contact. Returns (contacts, rejected)."""
    contacts = []
    rejected = []
    for row in raw_customers:
        contact_id = row["cust_id"].strip()
        if not contact_id:
            log.warning("Contact without cust_id -> quarantine: %s", row)
            rejected.append({**row, "reject_reason": "missing cust_id"})
            continue
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

    Orders without a known customer (orphans) or with an invalid amount
    are not loaded but kept in quarantine with the reason.
    """
    known_ids = {c["contactid"] for c in contacts}
    orders = []
    rejected = []
    for row in raw_orders:
        order_id = row["tx_id"].strip()
        customer_id = row["customer_id"].strip()

        if customer_id not in known_ids:
            log.warning("Orphan order %s: customer %s does not exist -> quarantine", order_id, customer_id)
            rejected.append({**row, "reject_reason": f"orphan: customer {customer_id} not found"})
            continue

        amount = to_decimal(row["amount_usd"])
        if amount is None:
            log.warning("Invalid amount for %s: %r -> quarantine", order_id, row["amount_usd"])
            rejected.append({**row, "reject_reason": "invalid amount"})
            continue

        orders.append({
            "salesorderid": order_id,
            "customerid": customer_id,
            "totalamount": amount,
            "createdon": to_iso8601(row["tx_timestamp"]),
        })
    log.info("Transformed %d sales orders, %d rejected", len(orders), len(rejected))
    return orders, rejected
