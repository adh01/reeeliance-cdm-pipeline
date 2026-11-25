from extract import read_csv
from transform import to_contacts, to_sales_orders


def test_read_csv_repairs_row_split_over_two_lines(tmp_path):
    raw = tmp_path / "customers.csv"
    raw.write_text(
        "cust_id,full_name,email_addr,signup_date,user_status\n"
        "CST-005, Charlie Brown\n"
        ",charlie@peanuts.com,2023-05-01T12:00:00Z,inactive\n"
    )
    rows, malformed = read_csv(raw)
    assert malformed == []
    assert len(rows) == 1
    assert rows[0]["cust_id"] == "CST-005"
    assert rows[0]["email_addr"] == "charlie@peanuts.com"


def test_contact_mapping():
    raw = [{"cust_id": "CST-002", "full_name": "John Smith", "email_addr": "JOHN.SMITH@DOMAIN.COM",
            "signup_date": "2023-02-20 14:15:00", "user_status": "active"}]
    contacts, rejected = to_contacts(raw)
    assert rejected == []
    assert contacts[0] == {
        "contactid": "CST-002", "firstname": "John", "lastname": "Smith",
        "emailaddress1": "john.smith@domain.com", "createdon": "2023-02-20T14:15:00Z", "statecode": 0,
    }


def test_orphan_order_goes_to_quarantine():
    contacts = [{"contactid": "CST-001"}]
    raw_orders = [
        {"tx_id": "ORD-1001", "customer_id": "CST-001", "amount_usd": "250.50", "tx_timestamp": "2023-06-01T09:15:00Z"},
        {"tx_id": "ORD-1005", "customer_id": "CST-999", "amount_usd": "99.00", "tx_timestamp": "2023-06-06T10:00:00Z"},
    ]
    orders, rejected = to_sales_orders(raw_orders, contacts)
    assert [o["salesorderid"] for o in orders] == ["ORD-1001"]
    assert rejected[0]["tx_id"] == "ORD-1005"
    assert "orphan" in rejected[0]["reject_reason"]


def test_every_loaded_order_has_a_valid_customer():
    contacts = [{"contactid": "A"}, {"contactid": "B"}]
    raw_orders = [{"tx_id": str(i), "customer_id": c, "amount_usd": "1", "tx_timestamp": "2023-01-01"}
                  for i, c in enumerate(["A", "B", "X", "A"])]
    orders, _ = to_sales_orders(raw_orders, contacts)
    assert all(o["customerid"] in {"A", "B"} for o in orders)


def test_duplicate_contact_id_goes_to_quarantine():
    row = {"cust_id": "CST-001", "full_name": "Jane Doe", "email_addr": "jane@example.com",
           "signup_date": "2023-01-15", "user_status": "active"}
    contacts, rejected = to_contacts([row, dict(row)])
    assert len(contacts) == 1
    assert rejected[0]["reject_reason"] == "duplicate id"


def test_duplicate_and_invalid_orders_go_to_quarantine():
    contacts = [{"contactid": "CST-001"}]
    base = {"customer_id": "CST-001", "amount_usd": "10.00", "tx_timestamp": "2023-06-01T09:15:00Z"}
    raw_orders = [
        {"tx_id": "ORD-1", **base},
        {"tx_id": "ORD-1", **base},                                     # duplicate
        {"tx_id": "ORD-2", **base, "tx_timestamp": "not a date"},       # invalid timestamp
    ]
    orders, rejected = to_sales_orders(raw_orders, contacts)
    assert [o["salesorderid"] for o in orders] == ["ORD-1"]
    assert [r["reject_reason"] for r in rejected] == ["duplicate id", "invalid timestamp"]


def test_row_with_too_many_fields_goes_to_quarantine(tmp_path):
    raw = tmp_path / "orders.csv"
    raw.write_text(
        "tx_id,customer_id,amount_usd,tx_timestamp\n"
        "ORD-1,CST-001,1,200.00,2023-06-01T09:15:00Z\n"
        "ORD-2,CST-001,10.00,2023-06-01T09:15:00Z\n"
    )
    rows, malformed = read_csv(raw)
    assert [r["tx_id"] for r in rows] == ["ORD-2"]
    assert malformed[0]["reject_reason"] == "wrong number of fields"
