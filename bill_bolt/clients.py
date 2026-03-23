"""Client manager: store client info, reuse across invoices."""

from datetime import datetime
from typing import Optional

from bill_bolt.storage import get_db


def create_client(
    name: str,
    email: str = "",
    address: str = "",
    phone: str = "",
    default_rate: float = 0.0,
    currency: str = "USD",
    notes: str = "",
) -> dict:
    """Create a new client."""
    conn = get_db()
    now = datetime.now().isoformat()
    cursor = conn.execute(
        """INSERT INTO clients (name, email, address, phone, default_rate, currency, notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, email, address, phone, default_rate, currency, notes, now)
    )
    conn.commit()
    client = get_client(cursor.lastrowid)
    conn.close()
    return client


def get_client(client_id: int) -> Optional[dict]:
    """Get a client by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_client_by_name(name: str) -> Optional[dict]:
    """Get a client by name (case-insensitive)."""
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_clients() -> list:
    """List all clients."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_client(client_id: int, **kwargs) -> dict:
    """Update client fields."""
    conn = get_db()
    allowed = {"name", "email", "address", "phone", "default_rate", "currency", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}

    if not updates:
        conn.close()
        return get_client(client_id)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [client_id]
    conn.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)
    conn.commit()
    result = get_client(client_id)
    conn.close()
    return result


def delete_client(client_id: int) -> bool:
    """Delete a client (fails if they have invoices)."""
    conn = get_db()
    # Check for existing invoices
    inv_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM invoices WHERE client_id = ?", (client_id,)
    ).fetchone()["cnt"]
    if inv_count > 0:
        conn.close()
        raise ValueError(f"Cannot delete client with {inv_count} invoice(s). Delete invoices first.")

    cursor = conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def get_client_summary(client_id: int) -> dict:
    """Get client with invoice summary."""
    client = get_client(client_id)
    if not client:
        return None

    conn = get_db()
    stats = conn.execute(
        """SELECT
           COUNT(*) as invoice_count,
           COALESCE(SUM(total), 0) as total_billed,
           COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as total_paid,
           COALESCE(SUM(CASE WHEN status IN ('sent', 'overdue') THEN total ELSE 0 END), 0) as total_outstanding
           FROM invoices WHERE client_id = ?""",
        (client_id,)
    ).fetchone()
    conn.close()

    return {
        **client,
        "invoice_count": stats["invoice_count"],
        "total_billed": stats["total_billed"],
        "total_paid": stats["total_paid"],
        "total_outstanding": stats["total_outstanding"],
    }
