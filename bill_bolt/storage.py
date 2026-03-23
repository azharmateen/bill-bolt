"""SQLite storage: invoices, clients, line items, payments."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_DIR = os.path.join(str(Path.home()), ".bill-bolt")
DB_PATH = os.path.join(DB_DIR, "billing.db")


def get_db() -> sqlite3.Connection:
    """Get database connection, creating schema if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    """Create all tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            default_rate REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'USD',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            subtotal REAL DEFAULT 0.0,
            tax_rate REAL DEFAULT 0.0,
            tax_amount REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            notes TEXT DEFAULT '',
            payment_terms TEXT DEFAULT 'Net 30',
            created_at TEXT NOT NULL,
            paid_at TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            quantity REAL DEFAULT 1.0,
            rate REAL DEFAULT 0.0,
            amount REAL DEFAULT 0.0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT DEFAULT '',
            reference TEXT DEFAULT '',
            paid_at TEXT NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()


def get_next_invoice_number() -> str:
    """Generate the next invoice number."""
    conn = get_db()
    row = conn.execute(
        "SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if row:
        # Try to increment numeric part
        num = row["invoice_number"]
        prefix = ""
        suffix = num
        for i, c in enumerate(num):
            if c.isdigit():
                prefix = num[:i]
                suffix = num[i:]
                break
        try:
            next_num = int(suffix) + 1
            return f"{prefix}{next_num:04d}"
        except ValueError:
            pass

    # Default first invoice
    return "INV-0001"


def get_setting(key: str, default: str = "") -> str:
    """Get a setting value."""
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """Set a setting value."""
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()
