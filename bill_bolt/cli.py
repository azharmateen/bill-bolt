"""Bill Bolt CLI - Lightning-fast invoicing for freelancers."""

import click

from bill_bolt.clients import create_client, list_clients, get_client_by_name, get_client_summary
from bill_bolt.invoice import create_invoice, get_invoice, list_invoices, update_invoice_status, get_invoice_by_number
from bill_bolt.generator import save_invoice_html, save_invoice_pdf
from bill_bolt.reporter import format_report, outstanding_invoices
from bill_bolt.storage import set_setting, get_setting


@click.group()
@click.version_option(version="1.0.0", prog_name="bill-bolt")
def cli():
    """Bill Bolt - Lightning-fast invoicing CLI for freelancers.

    Generate professional invoices, track payments, and manage clients.
    """
    pass


@cli.command()
@click.option("--client", "-c", required=True, help="Client name")
@click.option("--item", "-i", multiple=True, help="Line item: 'description|hours|rate' (can specify multiple)")
@click.option("--tax", "-t", default=0.0, type=float, help="Tax rate percentage")
@click.option("--notes", "-n", default="", help="Invoice notes")
@click.option("--terms", default="Net 30", help="Payment terms")
@click.option("--due-days", default=30, type=int, help="Days until due")
@click.option("--style", type=click.Choice(["clean", "modern"]), default="clean", help="Template style")
@click.option("--pdf", is_flag=True, help="Generate PDF (requires weasyprint)")
def create(client, item, tax, notes, terms, due_days, style, pdf):
    """Create a new invoice.

    Example: bill-bolt create --client "Acme Corp" -i "Web Development|40|100" -i "Design|10|120" --tax 10
    """
    # Find or prompt for client
    client_obj = get_client_by_name(client)
    if not client_obj:
        click.echo(f"Client '{client}' not found. Creating...")
        email = click.prompt("  Client email", default="")
        address = click.prompt("  Client address", default="")
        rate = click.prompt("  Default hourly rate", default=0.0, type=float)
        client_obj = create_client(client, email=email, address=address, default_rate=rate)
        click.echo(f"  Client created (ID: {client_obj['id']})")

    if not item:
        click.echo("Adding line items (enter empty description to finish):")
        items = []
        while True:
            desc = click.prompt("  Description", default="")
            if not desc:
                break
            hours = click.prompt("  Hours/Qty", type=float, default=1.0)
            rate_val = click.prompt("  Rate", type=float, default=client_obj.get("default_rate", 0))
            items.append({"description": desc, "quantity": hours, "rate": rate_val})
    else:
        items = []
        for i in item:
            parts = i.split("|")
            if len(parts) != 3:
                click.echo(f"Invalid item format: {i}. Use 'description|hours|rate'", err=True)
                return
            items.append({
                "description": parts[0].strip(),
                "quantity": float(parts[1].strip()),
                "rate": float(parts[2].strip()),
            })

    if not items:
        click.echo("No items. Invoice not created.", err=True)
        return

    invoice = create_invoice(
        client_id=client_obj["id"],
        items=items,
        tax_rate=tax,
        notes=notes,
        payment_terms=terms,
        due_days=due_days,
    )

    click.echo(f"\nInvoice {invoice['invoice_number']} created!")
    click.echo(f"  Client: {invoice['client_name']}")
    click.echo(f"  Items: {len(invoice['items'])}")
    click.echo(f"  Subtotal: ${invoice['subtotal']:,.2f}")
    if tax > 0:
        click.echo(f"  Tax ({tax}%): ${invoice['tax_amount']:,.2f}")
    click.echo(f"  Total: ${invoice['total']:,.2f}")
    click.echo(f"  Due: {invoice['due_date']}")

    # Generate file
    if pdf:
        path = save_invoice_pdf(invoice, style=style)
        click.echo(f"\n  Saved to: {path}")
    else:
        path = save_invoice_html(invoice, style=style)
        click.echo(f"\n  Saved to: {path}")


@cli.command(name="list")
@click.option("--status", "-s", type=click.Choice(["draft", "sent", "paid", "overdue", "cancelled", "all"]), default="all")
def list_cmd(status):
    """List all invoices."""
    status_filter = None if status == "all" else status
    invoices = list_invoices(status_filter)

    if not invoices:
        click.echo("No invoices found.")
        return

    click.echo()
    click.echo(f"  {'Invoice':<12} {'Client':<20} {'Date':<12} {'Total':>10} {'Status':<10}")
    click.echo("  " + "-" * 68)

    for inv in invoices:
        click.echo(
            f"  {inv['invoice_number']:<12} {inv['client_name'][:18]:<20} "
            f"{inv['issue_date']:<12} ${inv['total']:>8,.2f} {inv['status']:<10}"
        )

    total = sum(inv["total"] for inv in invoices)
    click.echo("  " + "-" * 68)
    click.echo(f"  {'Total':<44} ${total:>8,.2f}")
    click.echo(f"\n  {len(invoices)} invoice(s)")


@cli.command()
@click.argument("invoice_number")
@click.option("--style", type=click.Choice(["clean", "modern"]), default="clean")
@click.option("--pdf", is_flag=True, help="Generate PDF")
def send(invoice_number, style, pdf):
    """Mark invoice as sent and generate the document."""
    invoice = get_invoice_by_number(invoice_number)
    if not invoice:
        click.echo(f"Invoice {invoice_number} not found.", err=True)
        return

    # Update status to sent
    updated = update_invoice_status(invoice["id"], "sent")

    if pdf:
        path = save_invoice_pdf(updated, style=style)
    else:
        path = save_invoice_html(updated, style=style)

    click.echo(f"Invoice {invoice_number} marked as SENT")
    click.echo(f"  Document saved to: {path}")
    click.echo(f"  Send to: {updated.get('client_email', 'no email on file')}")


@cli.command()
@click.option("--style", type=click.Choice(["clean", "modern"]), default="clean")
def template(style):
    """Preview invoice template styles."""
    click.echo(f"Available styles: clean, modern")
    click.echo(f"  Use --style with 'create' or 'send' commands.")
    click.echo(f"  Example: bill-bolt create --client 'Acme' -i 'Work|10|100' --style {style}")


@cli.command()
@click.option("--add", "-a", is_flag=True, help="Add a new client")
@click.option("--name", "-n", default=None, help="Client name to show details")
def clients(add, name):
    """Manage clients."""
    if add:
        cname = click.prompt("Client name")
        email = click.prompt("Email", default="")
        address = click.prompt("Address", default="")
        phone = click.prompt("Phone", default="")
        rate = click.prompt("Default hourly rate", default=0.0, type=float)
        currency = click.prompt("Currency", default="USD")

        client = create_client(cname, email=email, address=address, phone=phone,
                               default_rate=rate, currency=currency)
        click.echo(f"\nClient '{client['name']}' created (ID: {client['id']})")
        return

    if name:
        client = get_client_by_name(name)
        if not client:
            click.echo(f"Client '{name}' not found.", err=True)
            return
        summary = get_client_summary(client["id"])
        click.echo(f"\n  Client: {summary['name']}")
        click.echo(f"  Email: {summary.get('email', '-')}")
        click.echo(f"  Address: {summary.get('address', '-')}")
        click.echo(f"  Default Rate: ${summary.get('default_rate', 0):.2f}/hr")
        click.echo(f"  Invoices: {summary['invoice_count']}")
        click.echo(f"  Total Billed: ${summary['total_billed']:,.2f}")
        click.echo(f"  Total Paid: ${summary['total_paid']:,.2f}")
        click.echo(f"  Outstanding: ${summary['total_outstanding']:,.2f}")
        return

    all_clients = list_clients()
    if not all_clients:
        click.echo("No clients yet. Add one with: bill-bolt clients --add")
        return

    click.echo()
    click.echo(f"  {'ID':<5} {'Name':<20} {'Email':<25} {'Rate':>8}")
    click.echo("  " + "-" * 60)
    for c in all_clients:
        click.echo(f"  {c['id']:<5} {c['name'][:18]:<20} {c.get('email', '')[:23]:<25} ${c.get('default_rate', 0):>6.2f}")
    click.echo(f"\n  {len(all_clients)} client(s)")


@cli.command()
@click.option("--type", "-t", "report_type",
              type=click.Choice(["summary", "monthly", "clients", "outstanding", "all"]),
              default="all", help="Report type")
def report(report_type):
    """Generate financial reports."""
    click.echo(format_report(report_type))


@cli.command()
@click.option("--name", prompt="Business name", help="Your business name")
@click.option("--email", prompt="Business email", help="Your email")
@click.option("--address", prompt="Business address", help="Your address")
def setup(name, email, address):
    """Configure your business details for invoices."""
    set_setting("business_name", name)
    set_setting("business_email", email)
    set_setting("business_address", address)
    click.echo("\nBusiness details saved!")
    click.echo(f"  Name: {name}")
    click.echo(f"  Email: {email}")
    click.echo(f"  Address: {address}")


if __name__ == "__main__":
    cli()
