"""Reports: monthly revenue summary, outstanding invoices, per-client totals, yearly tax summary."""

from collections import defaultdict
from datetime import datetime

from bill_bolt.storage import get_db


def monthly_revenue(year: int = None) -> list:
    """Get monthly revenue summary."""
    if not year:
        year = datetime.now().year

    conn = get_db()
    rows = conn.execute(
        """SELECT
           strftime('%Y-%m', issue_date) as month,
           COUNT(*) as invoice_count,
           SUM(subtotal) as revenue,
           SUM(tax_amount) as tax_collected,
           SUM(total) as total,
           SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END) as collected
           FROM invoices
           WHERE strftime('%Y', issue_date) = ?
           GROUP BY month
           ORDER BY month""",
        (str(year),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def outstanding_invoices() -> list:
    """Get all unpaid invoices."""
    conn = get_db()
    rows = conn.execute(
        """SELECT i.*, c.name as client_name
           FROM invoices i JOIN clients c ON i.client_id = c.id
           WHERE i.status IN ('sent', 'overdue', 'draft')
           ORDER BY i.due_date ASC"""
    ).fetchall()
    conn.close()

    result = []
    now = datetime.now().strftime("%Y-%m-%d")
    for r in rows:
        invoice = dict(r)
        invoice["is_overdue"] = invoice["due_date"] < now and invoice["status"] != "draft"
        if invoice["is_overdue"] and invoice["status"] == "sent":
            # Auto-update status
            _conn = get_db()
            _conn.execute("UPDATE invoices SET status = 'overdue' WHERE id = ?", (invoice["id"],))
            _conn.commit()
            _conn.close()
            invoice["status"] = "overdue"
        result.append(invoice)

    return result


def client_totals() -> list:
    """Get per-client billing totals."""
    conn = get_db()
    rows = conn.execute(
        """SELECT
           c.name,
           c.email,
           COUNT(i.id) as invoice_count,
           COALESCE(SUM(i.total), 0) as total_billed,
           COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.total ELSE 0 END), 0) as total_paid,
           COALESCE(SUM(CASE WHEN i.status IN ('sent', 'overdue') THEN i.total ELSE 0 END), 0) as outstanding
           FROM clients c
           LEFT JOIN invoices i ON c.id = i.client_id
           GROUP BY c.id
           ORDER BY total_billed DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def yearly_tax_summary(year: int = None) -> dict:
    """Get yearly tax summary for tax reporting."""
    if not year:
        year = datetime.now().year

    conn = get_db()
    row = conn.execute(
        """SELECT
           COUNT(*) as total_invoices,
           COALESCE(SUM(subtotal), 0) as total_revenue,
           COALESCE(SUM(tax_amount), 0) as total_tax_collected,
           COALESCE(SUM(total), 0) as total_with_tax,
           COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as collected,
           COALESCE(SUM(CASE WHEN status = 'paid' THEN subtotal ELSE 0 END), 0) as collected_revenue,
           COALESCE(SUM(CASE WHEN status = 'paid' THEN tax_amount ELSE 0 END), 0) as collected_tax,
           COALESCE(SUM(CASE WHEN status IN ('sent', 'overdue') THEN total ELSE 0 END), 0) as outstanding
           FROM invoices
           WHERE strftime('%Y', issue_date) = ?""",
        (str(year),)
    ).fetchone()
    conn.close()

    return {
        "year": year,
        **dict(row),
    }


def format_report(report_type: str = "summary") -> str:
    """Format a report for terminal output."""
    lines = []

    if report_type == "summary" or report_type == "all":
        year = datetime.now().year
        tax = yearly_tax_summary(year)
        lines.append("=" * 60)
        lines.append(f"  YEARLY SUMMARY - {year}")
        lines.append("=" * 60)
        lines.append(f"  Total Invoices:    {tax['total_invoices']}")
        lines.append(f"  Total Revenue:     ${tax['total_revenue']:,.2f}")
        lines.append(f"  Tax Collected:     ${tax['total_tax_collected']:,.2f}")
        lines.append(f"  Total Billed:      ${tax['total_with_tax']:,.2f}")
        lines.append(f"  Collected:         ${tax['collected']:,.2f}")
        lines.append(f"  Outstanding:       ${tax['outstanding']:,.2f}")

    if report_type == "monthly" or report_type == "all":
        monthly = monthly_revenue()
        lines.append("")
        lines.append("  MONTHLY BREAKDOWN")
        lines.append("  " + "-" * 56)
        lines.append(f"  {'Month':<10} {'Invoices':>8} {'Revenue':>12} {'Collected':>12}")
        lines.append("  " + "-" * 56)
        for m in monthly:
            lines.append(
                f"  {m['month']:<10} {m['invoice_count']:>8} "
                f"${m['revenue']:>10,.2f} ${m['collected']:>10,.2f}"
            )

    if report_type == "clients" or report_type == "all":
        clients = client_totals()
        lines.append("")
        lines.append("  CLIENT TOTALS")
        lines.append("  " + "-" * 56)
        lines.append(f"  {'Client':<20} {'Invoices':>8} {'Billed':>12} {'Outstanding':>12}")
        lines.append("  " + "-" * 56)
        for c in clients:
            lines.append(
                f"  {c['name'][:18]:<20} {c['invoice_count']:>8} "
                f"${c['total_billed']:>10,.2f} ${c['outstanding']:>10,.2f}"
            )

    if report_type == "outstanding" or report_type == "all":
        outstanding = outstanding_invoices()
        lines.append("")
        lines.append("  OUTSTANDING INVOICES")
        lines.append("  " + "-" * 56)
        if outstanding:
            lines.append(f"  {'Invoice':<12} {'Client':<18} {'Due Date':<12} {'Amount':>10}")
            lines.append("  " + "-" * 56)
            for inv in outstanding:
                overdue_mark = " [OVERDUE]" if inv.get("is_overdue") else ""
                lines.append(
                    f"  {inv['invoice_number']:<12} {inv['client_name'][:16]:<18} "
                    f"{inv['due_date']:<12} ${inv['total']:>8,.2f}{overdue_mark}"
                )
        else:
            lines.append("  No outstanding invoices!")

    lines.append("")
    return "\n".join(lines)
