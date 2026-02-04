# Invoice CRM

A file-based mini CRM for generating professional invoices, letters, and company detail cards using Python, Jinja2, Pydantic, and WeasyPrint.

## Features

- **Invoice Generation** - Professional PDF invoices with QR codes for payments
- **Letter Generation** - Business letters with customizable templates
- **Company Cards** - Bank details cards with payment QR codes
- **Digital Signatures** - Optional PDF signing with self-signed certificates
- **File Encryption** - Optional encryption using [age](https://age-encryption.org)
- **Multiple Banks** - Support for multiple bank accounts per provider
- **QR Payment Codes**:
  - EUR: EPC/SEPA format (European banking apps)
  - TRY: EMVCo format (Turkish banking apps)
  - USD: SWIFT text format
  - Crypto: USDT/BTC addresses

## Examples

See the `examples/` directory for sample generated PDFs:
- `invoice-acme-corp.pdf` - Invoice for US client
- `invoice-startup-inc.pdf` - Invoice for EU client (EUR)
- `example-llc-details.pdf` - Company card with bank details
- `freelancer-details.pdf` - Individual freelancer card

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourname/invoice-crm.git
cd invoice-crm
make install

# Validate example data
make validate

# Generate an invoice
uv run python crm.py invoice acme-corp

# Generate a company card
uv run python crm.py card example-llc
```

## Project Structure

```
invoice-crm/
├── crm.py              # Main CLI tool
├── qr.py               # QR code generator (EPC, EMVCo, SWIFT, Crypto)
├── signing.py          # PDF digital signatures (pyHanko)
├── crypto.py           # Optional age encryption
├── schemas.py          # Pydantic schemas
├── Makefile            # Common commands
├── providers/          # Your companies (YAML)
│   └── example-llc.yaml
├── clients/            # Your clients (YAML)
│   └── acme-corp.yaml
├── templates/          # Jinja2 + CSS templates
│   ├── base.css
│   ├── invoice.html
│   ├── letter.html
│   └── card.html
├── assets/             # Logos, signatures (PNG)
├── .certs/             # PDF signing certificates (gitignored)
├── archive/            # Generated invoices (by client)
└── cards/              # Generated company cards
```

## Commands

### Invoice

```bash
uv run python crm.py invoice CLIENT [options]

Options:
  -n, --number        Invoice number (auto-increment if omitted)
  -d, --date          Issue date (DD.MM.YYYY)
  -p, --provider      Override default provider
  -b, --bank          Bank name (e.g., payoneer-usd, wise-eur)
  --currency          Currency (USD, EUR, GBP, etc.)
  --qty               Quantity/hours (default from client)
  --rate              Rate per unit (default from client)
  --description       Service description
```

### Letter

```bash
uv run python crm.py letter CLIENT [options]

Options:
  -n, --number        Letter number (auto-increment)
  -p, --provider      Provider name (required)
  -s, --subject       Subject line
  -b, --body          Letter body (HTML supported)
  -o, --output        Output filename
  --show-bank         Include bank details
  --bank              Bank for --show-bank
  --tx-date/id/amount Transaction details (for refunds)
```

### Company Card

```bash
uv run python crm.py card PROVIDER [options]

Options:
  -b, --banks         Comma-separated bank names
  -o, --output        Output filename

# Examples:
uv run python crm.py card example-llc
uv run python crm.py card example-llc -b wise-usd,wise-eur -o llc-wise
```

### Other Commands

```bash
uv run python crm.py list providers|clients
uv run python crm.py show provider|client NAME
uv run python crm.py history CLIENT
uv run python crm.py validate
```

## Configuration

### Provider (Your Company)

```yaml
# providers/example-llc.yaml
name: Example LLC
type: corporation  # corporation, limited, individual

address:
  street: 123 Business Ave
  suite: Suite 100
  city: New York
  state: NY
  zip: "10001"
  country: USA

contact:
  email: billing@example.com
  phone: "+1 555 123 4567"
  website: https://example.com

tax:
  tin: "12-3456789"
  vat: null  # or VAT number if applicable

banks:
  wise-usd:
    currency: USD
    country: USA
    default: true
    holder: Example LLC
    account: "123456789"
    routing: "084009519"
    swift: TRWIUS33
    bank_name: Wise (TransferWise)
    bank_address: 30 W. 26th Street, New York, NY 10010

signer:
  name: John Smith
  title: CEO
  signature: assets/signature.png  # optional

logo: assets/logo.png  # optional
disclaimer: "Thank you for your business!"
```

### Client

```yaml
# clients/acme-corp.yaml
name: ACME Corporation
type: corporation

address:
  street: 456 Client Street
  city: Los Angeles
  state: CA
  zip: "90001"
  country: USA

contact:
  name: Jane Doe
  email: billing@acme.com

defaults:
  provider: example-llc
  currency: USD
  rate: 100.00
  hours: 40
  payment_terms: NET 30 days
```

## Banks & QR Codes

Each provider can have multiple bank accounts. QR codes are auto-generated based on currency:

| Currency | QR Format | Compatibility |
|----------|-----------|---------------|
| EUR | EPC/SEPA | All EU banking apps |
| TRY | EMVCo (TR.TCMB.FAST) | Turkish banking apps |
| USD | SWIFT text | Manual entry |
| USDT/BTC | Crypto address | Wallet apps |

## PDF Digital Signatures

All PDFs can be digitally signed with self-signed certificates.

```bash
# Create certificate for a provider (one-time)
uv run python crm.py cert-setup -p example-llc

# View certificates
uv run python crm.py cert-info
```

Recipients see signature info in Adobe Reader's Signatures panel.

## Encryption (Optional)

Encrypt sensitive PDFs using [age](https://age-encryption.org).

```bash
# Install age
brew install age  # macOS
apt install age   # Linux

# Generate encryption key
uv run python crm.py encrypt --setup

# Encrypt/decrypt
uv run python crm.py encrypt archive/
uv run python crm.py decrypt archive/
```

## File Naming

- Invoices: `archive/{client}/YYYY-MM-DD_Invoice_INV-XXXXX.pdf`
- Letters: `archive/{client}/YYYY-MM-DD_LTR-XXXXX_{subject}.pdf`
- Cards: `cards/{provider}-details.pdf`

Document numbers are auto-incremented in `.counters.json`.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — fast Python package manager
- macOS: `brew install pango`
- Linux: `apt install libpango-1.0-0 libpangocairo-1.0-0`
- Optional: `brew install age` (encryption)

### Installing uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS (Homebrew)
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for more options (pip, pipx, Docker, etc.)

## License

MIT License - see [LICENSE](LICENSE)
