# Bill Bolt

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blue?logo=anthropic&logoColor=white)](https://claude.ai/code)


> Lightning-fast invoicing CLI for freelancers. Generate professional PDF invoices in seconds.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Stop paying $20/month for invoicing SaaS.** Bill Bolt generates professional invoices from your terminal, tracks clients and payments, and keeps everything in a local SQLite database.

## Features

- **Professional invoices** with 2 template styles (clean, modern)
- **Client management** with default rates and contact info
- **Auto-increment** invoice numbers
- **Tax calculation** built-in
- **Payment tracking** and overdue detection
- **Financial reports**: monthly revenue, client totals, outstanding invoices, yearly tax summary
- **PDF output** (with weasyprint) or standalone HTML
- **Zero subscriptions** - everything local in `~/.bill-bolt/`

## Install

```bash
pip install bill-bolt

# For PDF generation (optional):
pip install bill-bolt[pdf]
```

## Quick Start

```bash
# Set up your business info
bill-bolt setup

# Add a client
bill-bolt clients --add

# Create an invoice
bill-bolt create --client "Acme Corp" \
  -i "Web Development|40|100" \
  -i "UI Design|10|120" \
  --tax 10 \
  --style modern

# List invoices
bill-bolt list

# Send an invoice (marks as sent + generates document)
bill-bolt send INV-0001 --pdf

# View reports
bill-bolt report --type all
```

## Invoice Styles

**Clean** - Traditional, professional look with dark headers and clear typography.

**Modern** - Contemporary design with gradient accents, badges, and rounded elements.

## Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new invoice |
| `list` | List all invoices |
| `send <number>` | Mark as sent and generate document |
| `clients` | Manage clients |
| `report` | Financial reports |
| `setup` | Configure business details |
| `template` | Preview template styles |

## Reports

- **Summary**: Yearly totals at a glance
- **Monthly**: Month-by-month revenue breakdown
- **Clients**: Per-client billing totals
- **Outstanding**: All unpaid/overdue invoices

## License

MIT
