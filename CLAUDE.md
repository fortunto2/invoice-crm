# Invoice CRM

File-based mini CRM using Python + Jinja2 + Pydantic + WeasyPrint for generating invoices and documents.

## Quick Start

```bash
make install        # Install dependencies
make validate       # Validate YAML files
make list           # Show providers and clients
make invoice-acme   # Generate invoice for ACME Corp
make cards          # Generate all company cards
```

## Make Commands

```bash
# Setup
make install          # Install dependencies (uv sync + pango)
make validate         # Validate all YAML files
make cert-all         # Create PDF signing certificates

# Generate
make invoice-acme     # Invoice for ACME Corp
make invoice-startup  # Invoice for Startup Inc
make cards            # All company cards
make letter-example   # Example letter

# Security
make cert-info        # Show certificates
make encrypt-setup    # Generate age key
make encrypt-archive  # Encrypt archive/
make decrypt-archive  # Decrypt archive/

# Info
make list             # List providers and clients
make history-CLIENT   # Show client history (e.g., make history-acme-corp)
make clean            # Remove generated PDFs
make help             # Show all commands
```

## Structure

```
invoice-crm/
├── crm.py              # CLI tool
├── qr.py               # QR code generator (EPC, EMVCo, SWIFT, Crypto)
├── signing.py          # PDF digital signatures (pyHanko)
├── crypto.py           # Optional age encryption
├── schemas.py          # Pydantic schemas
├── Makefile            # Shortcuts
├── providers/          # Your companies (YAML)
├── clients/            # Your clients (YAML)
├── templates/          # Jinja2 + CSS templates
│   ├── base.css        # Common styles + @page
│   ├── invoice.html
│   ├── letter.html
│   └── card.html       # Bank details card
├── assets/             # Logos, signatures (PNG)
├── .certs/             # PDF signing certificates (gitignored)
├── archive/            # Generated PDFs (by client)
└── cards/              # Company detail cards
```

## Providers

| ID | Name | Country | Use For |
|----|------|---------|---------|
| `example-llc` | Example LLC | USA (Delaware) | B2B US contracts |
| `freelancer` | Jane Developer | USA | Freelance work |

## Clients

| ID | Name | Default Provider |
|----|------|------------------|
| `acme-corp` | ACME Corporation | example-llc |
| `startup-inc` | Startup Inc. | freelancer |

## CLI (for custom options)

Use CLI when you need custom parameters beyond what Make provides.

### Invoice
```bash
uv run python crm.py invoice CLIENT [options]

Options:
  -n, --number        Invoice number (auto if omitted)
  -d, --date          Issue date (DD.MM.YYYY)
  -p, --provider      Override provider
  -b, --bank          Bank name (e.g., wise-usd, payoneer-eur)
  --currency          Currency (USD, EUR, GBP)
  --qty               Quantity/hours (default: 80)
  --rate              Rate per unit (default: 50.00)
  --description       Service description
```

### Letter
```bash
uv run python crm.py letter CLIENT [options]

Options:
  -n, --number        Letter number (auto if omitted)
  -p, --provider      Provider name (required)
  -s, --subject       Subject line
  -b, --body          Letter body (HTML)
  -o, --output        Output filename
  --show-bank         Include bank details
  --bank              Bank name for --show-bank
  --tx-date/id/amount Transaction details (for refunds)
```

### Company Card (Bank Details)
```bash
uv run python crm.py card PROVIDER [options]

Options:
  -b, --banks         Comma-separated bank names (auto-select if omitted)
  -o, --output        Output filename

# Examples:
uv run python crm.py card example-llc
uv run python crm.py card freelancer -b payoneer-usd,payoneer-eur -o freelancer-payoneer
```

### Other
```bash
uv run python crm.py list providers|clients
uv run python crm.py show provider|client NAME
uv run python crm.py history CLIENT
uv run python crm.py validate
```

## Banks & QR Codes

Each provider can have multiple banks. QR codes are auto-generated:

| Currency | QR Format | Compatibility |
|----------|-----------|---------------|
| EUR | EPC/SEPA | All EU banking apps |
| TRY | EMVCo (TR.TCMB.FAST) | Turkish banking apps |
| USD | SWIFT text | Manual entry |
| USDT | Crypto address | Binance, Trust Wallet |

```yaml
banks:
  wise-usd:
    currency: USD
    country: USA
    default: true      # default for this currency
    holder: Company Name
    account: "..."
    routing: "..."
    swift: TRWIUS33
    bank_name: Wise (TransferWise)
  wise-eur:
    currency: EUR
    country: Belgium
    default: true
    holder: Company Name
    iban: BE...
    swift: TRWIBEB1XXX
    bank_name: Wise Europe SA
```

Bank selection: automatic by `--currency` or explicit `--bank wise-usd`.

## File Naming

- Invoices: `archive/{client}/YYYY-MM-DD_Invoice_INV-XXXXX.pdf`
- Letters: `archive/{client}/YYYY-MM-DD_LTR-XXXXX_{subject}.pdf`
- Cards: `cards/{provider}-details.pdf` or `cards/{custom-name}.pdf`

Numbers stored in `.counters.json`.

## Adding New Client

```yaml
# clients/newclient.yaml
name: New Client Inc.
type: corporation

address:
  street: 123 Main St
  city: New York
  zip: "10001"
  country: USA

contact:
  email: billing@newclient.com

defaults:
  provider: example-llc
  currency: USD
  rate: 100.00
  hours: 40
```

```bash
uv run python crm.py validate
uv run python crm.py invoice newclient
```

## PDF Digital Signatures

All PDFs are automatically signed if a certificate exists.

```bash
# Create certificate for provider (one-time)
uv run python crm.py cert-setup -p example-llc
uv run python crm.py cert-setup -p freelancer

# View certificates
uv run python crm.py cert-info

# Or via make
make cert-all
```

**What recipients see in Adobe Reader:**
- Signatures panel with signer info
- Signer name, organization, email
- "Signature Invalid" if PDF was modified

Certificates stored in `.certs/` (gitignored). Self-signed, 10 years validity.

## Encryption (Optional)

Optional encryption via [age](https://age-encryption.org) — simple and modern tool.

```bash
# Install
brew install age

# Generate key (one-time)
uv run python crm.py encrypt --setup
# -> ~/.age/key.txt (private)
# -> age1... (public, for AGE_RECIPIENT)

# Encrypt
uv run python crm.py encrypt archive/           # all PDFs in folder
uv run python crm.py encrypt cards/company.pdf  # single file

# Decrypt
uv run python crm.py decrypt archive/
uv run python crm.py decrypt cards/company.pdf.age

# Or via make
make encrypt-archive
make decrypt-archive
```

For auto-encryption: `export AGE_RECIPIENT=age1...`

## Requirements

- Python 3.11+
- uv
- macOS: `brew install pango`
- Linux: `apt install libpango-1.0-0 libpangocairo-1.0-0`
- Optional: `brew install age` (for encryption)
