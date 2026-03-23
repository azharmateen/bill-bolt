"""Invoice model: create, update, manage invoices and line items."""

from datetime import datetime, timedelta
from typing import Optional

from bill_bolt.storage import get_db, get_next_invoice_number


def create_invoice(
    client_id: int,
    items: list,
    tax_rate: float = 0.0,
    notes: str = "",
    payment_terms: str = "Net 30",
    due_days: int = 30,
    invoice_number: str = None,
) -> dict:
    """Create a new invoice with line items.

    items: list of dicts with keys: description, quantity (hours), rate, amount (optional)
    """
    conn = get_db()

    if not invoice_number:
        invoice_number = get_next_invoice_number()

    now = datetime.now()
    issue_date = now.strftime("%Y-%m-%d")
    due_date = (now + timedelta(days=due_days)).strftime("%Y-%m-%d")

    # Calculate totals
    subtotal = 0.0
    for item in items:
        qty = float(item.get("quantity", item.get("hours", 1)))
        rate = float(item.get("rate", 0))
        amount = qty * rate
        item["amount"] = amount
        item["quantity"] = qty
        item["rate"] = rate
        subtotal += amount

    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount

    cursor = conn.execute(
        """INSERT INTO invoices (invoice_number, client_id, issue_date, due_date,
           subtotal, tax_rate, tax_amount, total, notes, payment_terms, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (invoice_number, client_id, issue_date, due_date,
         subtotal, tax_rate, tax_amount, total, notes, payment_terms, now.isoformat())
    )
    invoice_id = cursor.lastrowid

    # Insert line items
    for item in items:
        conn.execute(
            "INSERT INTO line_items (invoice_id, description, quantity, rate, amount) VALUES (?, ?, ?, ?, ?)",
            (invoice_id, item["description"], item["quantity"], item["rate"], item["amount"])
        )

    conn.commit()
    result = get_invoice(invoice_id)
    conn.close()
    return result


def get_invoice(invoice_id: int) -> Optional[dict]:
    """Get an invoice with its line items and client info."""
    conn = get_db()
    row = conn.execute(
        """SELECT i.*, c.name as client_name, c.email as client_email,
           c.address as client_address, c.phone as client_phone
           FROM invoices i JOIN clients c ON i.client_id = c.id
           WHERE i.id = ?""",
        (invoice_id,)
    ).fetchone()

    if not row:
        conn.close()
        return None

    invoice = dict(row)

    # Get line items
    items = conn.execute(
        "SELECT * FROM line_items WHERE invoice_id = ? ORDER BY id", (invoice_id,)
    ).fetchall()
    invoice["items"] = [dict(item) for item in items]

    # Get payments
    payments = conn.execute(
        "SELECT * FROM payments WHERE invoice_id = ? ORDER BY paid_at", (invoice_id,)
    ).fetchall()
    invoice["payments"] = [dict(p) for p in payments]
    invoice["amount_paid"] = sum(p["amount"] for p in payments)
    invoice["amount_due"] = invoice["total"] - invoice["amount_paid"]

    conn.close()
    return invoice


def get_invoice_by_number(invoice_number: str) -> Optional[dict]:
    """Get invoice by its invoice number."""
    conn = get_db()
    row = conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,)).fetchone()
    conn.close()
    if row:
        return get_invoice(row["id"])
    return None


def list_invoices(status: str = None, client_id: int = None) -> list:
    """List all invoices, optionally filtered."""
    conn = get_db()
    query = """SELECT i.*, c.name as client_name FROM invoices i
               JOIN clients c ON i.client_id = c.id"""
    params = []
    conditions = []

    if status:
        conditions.append("i.status = ?")
        params.append(status)
    if client_id:
        conditions.append("i.client_id = ?")
        params.append(client_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY i.created_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_invoice_status(invoice_id: int, status: str) -> dict:
    """Update invoice status."""
    conn = get_db()
    updates = {"status": status}
    if status == "paid":
        updates["paid_at"] = datetime.now().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [invoice_id]
    conn.execute(f"UPDATE invoices SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_invoice(invoice_id)


def record_payment(invoice_id: int, amount: float, method: str = "", reference: str = "") -> dict:
    """Record a payment against an invoice."""
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO payments (invoice_id, amount, method, reference, paid_at) VALUES (?, ?, ?, ?, ?)",
        (invoice_id, amount, method, reference, now)
    )

    # Check if fully paid
    invoice = get_invoice(invoice_id)
    if invoice and invoice["amount_due"] <= 0:
        conn.execute("UPDATE invoices SET status = 'paid', paid_at = ? WHERE id = ?", (now, invoice_id))

    conn.commit()
    conn.close()
    return get_invoice(invoice_id)


def delete_invoice(invoice_id: int) -> bool:
    """Delete an invoice."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
