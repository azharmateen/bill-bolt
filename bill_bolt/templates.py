"""Invoice HTML templates: clean and modern styles using Jinja2."""

from jinja2 import Template


CLEAN_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice {{ invoice.invoice_number }}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; padding: 40px; max-width: 800px; margin: 0 auto; background: #fff; }
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; border-bottom: 3px solid #2c3e50; padding-bottom: 20px; }
.header h1 { font-size: 28px; color: #2c3e50; }
.header .invoice-number { font-size: 14px; color: #7f8c8d; margin-top: 4px; }
.logo-placeholder { width: 120px; height: 60px; background: #ecf0f1; display: flex; align-items: center; justify-content: center; color: #95a5a6; font-size: 12px; border-radius: 4px; }
.parties { display: flex; justify-content: space-between; margin-bottom: 30px; }
.party { flex: 1; }
.party h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #95a5a6; margin-bottom: 8px; }
.party p { font-size: 14px; line-height: 1.6; }
.meta { display: flex; gap: 40px; margin-bottom: 30px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
.meta-item { }
.meta-item .label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #95a5a6; }
.meta-item .value { font-size: 16px; font-weight: 600; margin-top: 2px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
thead th { background: #2c3e50; color: #fff; padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
thead th:last-child { text-align: right; }
tbody td { padding: 12px; border-bottom: 1px solid #ecf0f1; font-size: 14px; }
tbody td:last-child { text-align: right; font-family: 'Courier New', monospace; }
tbody td.qty, tbody td.rate { text-align: center; }
.totals { display: flex; justify-content: flex-end; margin-bottom: 30px; }
.totals-table { width: 250px; }
.totals-table .row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 14px; }
.totals-table .row.total { border-top: 2px solid #2c3e50; font-size: 18px; font-weight: 700; padding-top: 10px; margin-top: 4px; }
.notes { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; color: #555; }
.notes h4 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #95a5a6; margin-bottom: 8px; }
.footer { text-align: center; font-size: 12px; color: #95a5a6; border-top: 1px solid #ecf0f1; padding-top: 15px; }
.status { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.status-draft { background: #f39c12; color: #fff; }
.status-sent { background: #3498db; color: #fff; }
.status-paid { background: #27ae60; color: #fff; }
.status-overdue { background: #e74c3c; color: #fff; }
@media print { body { padding: 0; } .no-print { display: none; } }
</style>
</head>
<body>
<div class="header">
    <div>
        <h1>INVOICE</h1>
        <div class="invoice-number">{{ invoice.invoice_number }}</div>
    </div>
    <div class="logo-placeholder">YOUR LOGO</div>
</div>

<div class="parties">
    <div class="party">
        <h3>From</h3>
        <p>{{ from_name }}<br>{{ from_address | default('Your Address', true) }}<br>{{ from_email | default('your@email.com', true) }}</p>
    </div>
    <div class="party">
        <h3>Bill To</h3>
        <p>{{ invoice.client_name }}<br>
        {% if invoice.client_address %}{{ invoice.client_address }}<br>{% endif %}
        {% if invoice.client_email %}{{ invoice.client_email }}{% endif %}
        {% if invoice.client_phone %}<br>{{ invoice.client_phone }}{% endif %}
        </p>
    </div>
</div>

<div class="meta">
    <div class="meta-item">
        <div class="label">Issue Date</div>
        <div class="value">{{ invoice.issue_date }}</div>
    </div>
    <div class="meta-item">
        <div class="label">Due Date</div>
        <div class="value">{{ invoice.due_date }}</div>
    </div>
    <div class="meta-item">
        <div class="label">Terms</div>
        <div class="value">{{ invoice.payment_terms }}</div>
    </div>
    <div class="meta-item">
        <div class="label">Status</div>
        <div class="value"><span class="status status-{{ invoice.status }}">{{ invoice.status }}</span></div>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th style="width:50%">Description</th>
            <th style="width:15%; text-align:center">Qty/Hours</th>
            <th style="width:15%; text-align:center">Rate</th>
            <th style="width:20%">Amount</th>
        </tr>
    </thead>
    <tbody>
        {% for item in line_items %}
        <tr>
            <td>{{ item.description }}</td>
            <td class="qty">{{ "%.1f"|format(item.quantity) }}</td>
            <td class="rate">${{ "%.2f"|format(item.rate) }}</td>
            <td>${{ "%.2f"|format(item.amount) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="totals">
    <div class="totals-table">
        <div class="row"><span>Subtotal</span><span>${{ "%.2f"|format(invoice.subtotal) }}</span></div>
        {% if invoice.tax_rate > 0 %}
        <div class="row"><span>Tax ({{ "%.1f"|format(invoice.tax_rate) }}%)</span><span>${{ "%.2f"|format(invoice.tax_amount) }}</span></div>
        {% endif %}
        <div class="row total"><span>Total</span><span>${{ "%.2f"|format(invoice.total) }}</span></div>
        {% if invoice.amount_paid > 0 %}
        <div class="row"><span>Paid</span><span>-${{ "%.2f"|format(invoice.amount_paid) }}</span></div>
        <div class="row" style="font-weight:600"><span>Balance Due</span><span>${{ "%.2f"|format(invoice.amount_due) }}</span></div>
        {% endif %}
    </div>
</div>

{% if invoice.notes %}
<div class="notes">
    <h4>Notes</h4>
    <p>{{ invoice.notes }}</p>
</div>
{% endif %}

<div class="footer">
    <p>Thank you for your business!</p>
</div>
</body>
</html>""")


MODERN_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice {{ invoice.invoice_number }}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; padding: 40px; max-width: 800px; margin: 0 auto; background: #fff; }
.accent { color: #6c5ce7; }
.header { margin-bottom: 40px; }
.header h1 { font-size: 36px; font-weight: 800; color: #6c5ce7; letter-spacing: -1px; }
.header .subtitle { font-size: 13px; color: #a0a0b0; margin-top: 4px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
.block h3 { font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: #a0a0b0; margin-bottom: 8px; }
.block p { font-size: 14px; line-height: 1.8; }
.badges { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 30px; }
.badge { background: #f0eeff; color: #6c5ce7; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.badge.date { background: #f5f5f5; color: #555; }
table { width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 24px; overflow: hidden; border-radius: 8px; border: 1px solid #eee; }
thead th { background: #6c5ce7; color: #fff; padding: 12px 16px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
thead th:last-child { text-align: right; }
tbody td { padding: 14px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
tbody td:last-child { text-align: right; font-weight: 600; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:nth-child(even) { background: #fafafe; }
.summary { display: flex; justify-content: flex-end; margin-bottom: 30px; }
.summary-box { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: #fff; padding: 24px; border-radius: 12px; min-width: 260px; }
.summary-box .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 14px; opacity: 0.9; }
.summary-box .row.total { font-size: 22px; font-weight: 800; opacity: 1; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 12px; margin-top: 8px; }
.notes { background: #f8f8fc; padding: 20px; border-radius: 8px; border-left: 4px solid #6c5ce7; margin-bottom: 24px; font-size: 13px; color: #555; }
.footer { text-align: center; font-size: 12px; color: #c0c0c0; margin-top: 40px; }
@media print { body { padding: 0; } }
</style>
</head>
<body>
<div class="header">
    <h1>Invoice</h1>
    <div class="subtitle">{{ invoice.invoice_number }} | {{ from_name | default('Your Business Name', true) }}</div>
</div>

<div class="grid">
    <div class="block">
        <h3>From</h3>
        <p><strong>{{ from_name | default('Your Business Name', true) }}</strong><br>
        {{ from_address | default('Your Address', true) }}<br>
        {{ from_email | default('your@email.com', true) }}</p>
    </div>
    <div class="block">
        <h3>Bill To</h3>
        <p><strong>{{ invoice.client_name }}</strong><br>
        {% if invoice.client_address %}{{ invoice.client_address }}<br>{% endif %}
        {% if invoice.client_email %}{{ invoice.client_email }}{% endif %}
        {% if invoice.client_phone %}<br>{{ invoice.client_phone }}{% endif %}
        </p>
    </div>
</div>

<div class="badges">
    <div class="badge date">Issued: {{ invoice.issue_date }}</div>
    <div class="badge date">Due: {{ invoice.due_date }}</div>
    <div class="badge">{{ invoice.payment_terms }}</div>
    <div class="badge" style="background: {% if invoice.status == 'paid' %}#d4edda; color:#27ae60{% elif invoice.status == 'overdue' %}#fde8e8; color:#e74c3c{% else %}#f0eeff; color:#6c5ce7{% endif %}">{{ invoice.status | upper }}</div>
</div>

<table>
    <thead>
        <tr>
            <th>Description</th>
            <th style="text-align:center">Qty</th>
            <th style="text-align:center">Rate</th>
            <th>Amount</th>
        </tr>
    </thead>
    <tbody>
        {% for item in line_items %}
        <tr>
            <td>{{ item.description }}</td>
            <td style="text-align:center">{{ "%.1f"|format(item.quantity) }}</td>
            <td style="text-align:center">${{ "%.2f"|format(item.rate) }}</td>
            <td>${{ "%.2f"|format(item.amount) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="summary">
    <div class="summary-box">
        <div class="row"><span>Subtotal</span><span>${{ "%.2f"|format(invoice.subtotal) }}</span></div>
        {% if invoice.tax_rate > 0 %}
        <div class="row"><span>Tax ({{ "%.1f"|format(invoice.tax_rate) }}%)</span><span>${{ "%.2f"|format(invoice.tax_amount) }}</span></div>
        {% endif %}
        <div class="row total"><span>Total</span><span>${{ "%.2f"|format(invoice.total) }}</span></div>
    </div>
</div>

{% if invoice.notes %}
<div class="notes">
    <strong>Notes:</strong> {{ invoice.notes }}
</div>
{% endif %}

<div class="footer">
    Thank you for your business! &middot; Generated with Bill Bolt
</div>
</body>
</html>""")


TEMPLATES = {
    "clean": CLEAN_TEMPLATE,
    "modern": MODERN_TEMPLATE,
}


def render_invoice(invoice: dict, style: str = "clean", **kwargs) -> str:
    """Render an invoice to HTML using the specified template."""
    template = TEMPLATES.get(style, CLEAN_TEMPLATE)
    # Pass line_items separately to avoid collision with dict.items() method
    line_items = invoice.get("items", [])
    return template.render(invoice=invoice, line_items=line_items, **kwargs)
