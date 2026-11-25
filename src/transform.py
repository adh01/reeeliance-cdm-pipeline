"""Map raw records to the CDM entities Contact and SalesOrder."""
import logging

from cleaning import clean_email, split_name, to_decimal, to_iso8601, to_statecode

log = logging.getLogger(__name__)


def to_contacts(raw_customers):
    """raw_customers.csv -> CDM Contact."""
    contacts = []
    for row in raw_customers:
        contact_id = row["cust_id"].strip()
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
    log.info("Transformed %d contacts", len(contacts))
    return contacts


def to_sales_orders(raw_orders, contacts):
    """raw_orders.csv -> CDM SalesOrder. Orders without a known customer (orphans) are logged and left out."""
    known_ids = {c["contactid"] for c in contacts}
    orders = []
    for row in raw_orders:
        order_id = row["tx_id"].strip()
        customer_id = row["customer_id"].strip()

        if customer_id not in known_ids:
            log.warning("Orphan order %s: customer %s does not exist -> skipped", order_id, customer_id)
            continue

        amount = to_decimal(row["amount_usd"])
        if amount is None:
            log.warning("Invalid amount for %s: %r", order_id, row["amount_usd"])

        orders.append({
            "salesorderid": order_id,
            "customerid": customer_id,
            "totalamount": amount,
            "createdon": to_iso8601(row["tx_timestamp"]),
        })
    log.info("Transformed %d sales orders", len(orders))
    return orders
