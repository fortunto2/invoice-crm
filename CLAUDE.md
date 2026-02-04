# Invoice CRM

File-based mini CRM for generating invoices, letters, and company cards using Python + Jinja2 + Pydantic + WeasyPrint.

## Quick Start

```bash
make install    # Install dependencies
make validate   # Validate YAML files
make list       # Show providers and clients

# Generate invoice
uv run python crm.py invoice acme-corp
```

## Structure

```
invoice-crm/
├── crm.py              # CLI tool
├── qr.py               # QR code generator (EPC, EMVCo, SWIFT, Crypto)
├── signing.py          # PDF digital signatures
├── crypto.py           # Optional age encryption
├── schemas.py          # Pydantic schemas
├── providers/          # Your companies (YAML)
├── clients/            # Your clients (YAML)
├── templates/          # Jinja2 + CSS templates
├── assets/             # Logos, signatures
├── archive/            # Generated invoices (by client)
└── cards/              # Generated company cards
```

## Commands

```bash
# Invoice
uv run python crm.py invoice CLIENT [-p PROVIDER] [--currency USD] [--qty 40] [--rate 100]

# Letter
uv run python crm.py letter CLIENT -p PROVIDER [-s "Subject"] [-b "Body HTML"]

# Company card
uv run python crm.py card PROVIDER [-b bank1,bank2]

# Other
uv run python crm.py list providers|clients
uv run python crm.py validate
uv run python crm.py history CLIENT
```

## PDF Signing

```bash
uv run python crm.py cert-setup -p example-llc
uv run python crm.py cert-info
```

## File Naming

- Invoices: `archive/{client}/YYYY-MM-DD_Invoice_INV-XXXXX.pdf`
- Letters: `archive/{client}/YYYY-MM-DD_LTR-XXXXX_{subject}.pdf`
- Cards: `cards/{provider}-details.pdf`
