"""PDF generator: create professional invoice PDF using HTML template."""

import os
from typing import Optional

from bill_bolt.templates import render_invoice
from bill_bolt.storage import get_setting


def generate_invoice_html(invoice: dict, style: str = "clean") -> str:
    """Generate invoice HTML from invoice data."""
    from_name = get_setting("business_name", "Your Business")
    from_email = get_setting("business_email", "your@email.com")
    from_address = get_setting("business_address", "Your Address")

    return render_invoice(
        invoice,
        style=style,
        from_name=from_name,
        from_email=from_email,
        from_address=from_address,
    )


def save_invoice_html(invoice: dict, output_path: str = None, style: str = "clean") -> str:
    """Save invoice as HTML file."""
    html = generate_invoice_html(invoice, style)

    if not output_path:
        output_path = f"invoice-{invoice['invoice_number']}.html"

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return os.path.abspath(output_path)


def save_invoice_pdf(invoice: dict, output_path: str = None, style: str = "clean") -> Optional[str]:
    """Save invoice as PDF using weasyprint (if available, otherwise falls back to HTML).

    Returns the path to the generated file.
    """
    html = generate_invoice_html(invoice, style)

    if not output_path:
        output_path = f"invoice-{invoice['invoice_number']}.pdf"

    try:
        from weasyprint import HTML
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        HTML(string=html).write_pdf(output_path)
        return os.path.abspath(output_path)
    except ImportError:
        # Fall back to HTML
        html_path = output_path.replace(".pdf", ".html")
        return save_invoice_html(invoice, html_path, style)
