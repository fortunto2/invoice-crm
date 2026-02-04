#!/usr/bin/env python3
"""
Invoice CRM - File-based mini CRM for invoices and documents.

Usage:
    uv run python crm.py invoice acme-corp                  # Auto-increment number
    uv run python crm.py invoice acme-corp -n INV-00005     # Specific number
    uv run python crm.py letter startup-inc --subject "Inquiry"
    uv run python crm.py list providers
    uv run python crm.py list clients
    uv run python crm.py history acme-corp                  # Show client history
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Set library paths for WeasyPrint on macOS (Homebrew)
if sys.platform == "darwin" and not os.environ.get("DYLD_FALLBACK_LIBRARY_PATH"):
    try:
        prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{prefix}/lib"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from weasyprint import HTML

from schemas import Provider, Client, Invoice, Document
from qr import generate_payment_qr
from crypto import encrypt_file, decrypt_file, encrypt_dir, decrypt_dir, setup_age_key, is_age_available
from signing import sign_pdf, create_self_signed_cert, get_cert_info, is_signing_available, list_certificates

ROOT = Path(__file__).parent
PROVIDERS_DIR = ROOT / "providers"
CLIENTS_DIR = ROOT / "clients"
PEOPLE_DIR = ROOT / "people"
TEMPLATES_DIR = ROOT / "templates"
ARCHIVE_DIR = ROOT / "archive"
COUNTER_FILE = ROOT / ".counters.json"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_counters() -> dict:
    """Load document counters."""
    if COUNTER_FILE.exists():
        return json.loads(COUNTER_FILE.read_text())
    return {"invoice": 0, "letter": 0}


def save_counters(counters: dict) -> None:
    """Save document counters."""
    COUNTER_FILE.write_text(json.dumps(counters, indent=2))


def get_next_number(doc_type: str, prefix: str = "INV") -> str:
    """Get next auto-increment number."""
    counters = load_counters()
    counters[doc_type] = counters.get(doc_type, 0) + 1
    save_counters(counters)
    return f"{prefix}-{counters[doc_type]:05d}"


def get_client_archive_dir(client_name: str) -> Path:
    """Get or create client archive directory."""
    # Sanitize client name for directory
    safe_name = client_name.lower().replace(" ", "-").replace(",", "").replace(".", "")
    client_dir = ARCHIVE_DIR / safe_name
    client_dir.mkdir(parents=True, exist_ok=True)
    return client_dir


def list_entities(entity_type: str) -> list[str]:
    """List available providers or clients."""
    dir_path = PROVIDERS_DIR if entity_type == "providers" else CLIENTS_DIR
    return [f.stem for f in dir_path.glob("*.yaml")]


def load_provider(name: str, validate: bool = True) -> dict:
    """Load provider by name."""
    path = PROVIDERS_DIR / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"Provider not found: {name}\nAvailable: {list_entities('providers')}")
    data = load_yaml(path)
    if validate:
        try:
            Provider.model_validate(data)
        except ValidationError as e:
            print(f"Warning: Provider '{name}' has validation errors:\n{e}", file=sys.stderr)
    # Convert relative paths to absolute
    if data.get("signer", {}).get("signature"):
        sig_path = ROOT / data["signer"]["signature"]
        if sig_path.exists():
            data["signer"]["signature"] = str(sig_path)
    if data.get("logo"):
        logo_path = ROOT / data["logo"]
        if logo_path.exists():
            data["logo"] = str(logo_path)
    return data


def load_client(name: str, validate: bool = True) -> dict:
    """Load client by name."""
    path = CLIENTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"Client not found: {name}\nAvailable: {list_entities('clients')}")
    data = load_yaml(path)
    if validate:
        try:
            Client.model_validate(data)
        except ValidationError as e:
            print(f"Warning: Client '{name}' has validation errors:\n{e}", file=sys.stderr)
    return data


def load_person(name: str) -> dict:
    """Load person by name."""
    path = PEOPLE_DIR / f"{name}.yaml"
    if not path.exists():
        available = [f.stem for f in PEOPLE_DIR.glob("*.yaml")] if PEOPLE_DIR.exists() else []
        raise ValueError(f"Person not found: {name}\nAvailable: {available}")
    return load_yaml(path)


def select_bank(provider: dict, currency: str, bank_name: str | None = None) -> dict:
    """Select bank from provider by name or currency.

    Priority:
    1. Explicit bank_name if provided
    2. Bank with default=True for the currency
    3. First bank matching the currency
    """
    banks = provider.get("banks", {})
    if not banks:
        raise ValueError(f"Provider '{provider['name']}' has no banks configured")

    # Explicit bank selection
    if bank_name:
        if bank_name not in banks:
            available = list(banks.keys())
            raise ValueError(f"Bank '{bank_name}' not found. Available: {available}")
        return {"name": bank_name, **banks[bank_name]}

    # Find by currency: prefer default, then first match
    matches = [(k, v) for k, v in banks.items() if v.get("currency") == currency]
    if not matches:
        available = {v.get("currency") for v in banks.values()}
        raise ValueError(f"No bank for currency '{currency}'. Available: {available}")

    # Prefer default
    for name, bank in matches:
        if bank.get("default"):
            return {"name": name, **bank}

    # First match
    name, bank = matches[0]
    return {"name": name, **bank}


def format_number(value: float, european: bool = True) -> str:
    """Format number: 4000.00 -> 4.000,00 (European) or 4,000.00 (US)."""
    if european:
        return f"{value:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"{value:,.2f}"


def render_template(template_name: str, context: dict) -> str:
    """Render Jinja2 template with context."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters["format_number"] = format_number

    css_path = TEMPLATES_DIR / "base.css"
    if css_path.exists():
        context["base_css"] = css_path.read_text()

    template = env.get_template(template_name)
    return template.render(**context)


def html_to_pdf(html_content: str, output_path: Path, provider_id: str | None = None) -> None:
    """Convert HTML to PDF/A-3b using WeasyPrint, sign with provider cert if available."""
    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(
        output_path,
        pdf_variant="pdf/a-3b",
    )
    # Sign PDF if provider certificate exists
    if provider_id and is_signing_available(provider_id):
        sign_pdf(output_path, provider_id)


def cmd_list(args):
    """List providers or clients."""
    entities = list_entities(args.type)
    print(f"\n{args.type.title()}:")
    for name in sorted(entities):
        data = load_yaml((PROVIDERS_DIR if args.type == "providers" else CLIENTS_DIR) / f"{name}.yaml")
        print(f"  {name:20} - {data.get('name', 'N/A')}")
    print()


def cmd_show(args):
    """Show provider or client details."""
    if args.type == "provider":
        data = load_provider(args.name, validate=False)
    else:
        data = load_client(args.name, validate=False)

    print(f"\n{args.type.title()}: {args.name}")
    print("-" * 40)
    print(yaml.dump(data, default_flow_style=False, allow_unicode=True))


def cmd_history(args):
    """Show client document history."""
    client = load_client(args.client)
    client_dir = get_client_archive_dir(args.client)

    print(f"\nHistory for {client['name']}:")
    print("-" * 50)

    files = sorted(client_dir.glob("*.pdf"), reverse=True)
    if not files:
        print("  No documents yet")
    else:
        for f in files[:20]:  # Last 20
            size = f.stat().st_size / 1024
            print(f"  {f.name:45} {size:6.1f} KB")
    print()


def cmd_invoice(args):
    """Generate invoice PDF."""
    client = load_client(args.client)
    client_id = args.client

    # Auto-increment or use provided number
    if args.number:
        inv_number = args.number
    else:
        inv_number = get_next_number("invoice", "INV")

    # Use provider from args or client defaults
    provider_name = args.provider or client.get("defaults", {}).get("provider")
    if not provider_name:
        raise ValueError("Provider required: use --provider or set client defaults.provider")
    provider = load_provider(provider_name)

    # Build invoice data
    defaults = client.get("defaults", {})
    currency = args.currency or defaults.get("currency", "USD")
    rate = args.rate or defaults.get("rate", 50.00)
    qty = args.qty or defaults.get("hours", 80)
    total = rate * qty
    invoice_date = args.date or datetime.now().strftime("%d.%m.%Y")

    # Select bank
    bank = select_bank(provider, currency, getattr(args, 'bank', None))

    invoice_data = {
        "number": inv_number,
        "date": invoice_date,
        "currency": currency,
        "payment_terms": defaults.get("payment_terms", "NET 7 days"),
        "line_items": [{
            "description": args.description or "Software development services",
            "qty": qty,
            "unit": "item",
            "price": format_number(rate),
            "amount": format_number(total),
            "vat_rate": 0,
        }],
        "subtotal": format_number(total),
        "total": format_number(total),
    }

    invoice = Invoice.model_validate(invoice_data)

    # Generate payment QR code
    qr_data_uri = generate_payment_qr(bank, total, inv_number)

    context = {
        "provider": provider,
        "client": client,
        "invoice": invoice.model_dump(),
        "bank": bank,
        "qr_code": qr_data_uri,
    }

    html = render_template("invoice.html", context)

    # Save to client archive
    client_dir = get_client_archive_dir(client_id)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_Invoice_{inv_number}.pdf"
    output_path = client_dir / filename

    html_to_pdf(html, output_path, provider_name)
    print(f"Created: {output_path}")
    print(f"Invoice: {inv_number}")


def cmd_letter(args):
    """Generate letter/document PDF."""
    client = load_client(args.client)
    client_id = args.client

    # Auto-increment letter number
    if args.number:
        letter_number = args.number
    else:
        letter_number = get_next_number("letter", "LTR")

    provider_name = args.provider or client.get("defaults", {}).get("provider")
    if not provider_name:
        raise ValueError("Provider required: use --provider or set client defaults")
    provider = load_provider(provider_name)

    # Select bank (for --show-bank)
    defaults = client.get("defaults", {})
    currency = args.tx_currency or defaults.get("currency", "USD")
    bank = select_bank(provider, currency, getattr(args, 'bank', None))

    doc_data = {
        "date": args.date or datetime.now().strftime("%B %d, %Y"),
        "subject": args.subject or "Letter",
        "body": args.body or "",
        "show_bank": args.show_bank,
    }

    if args.tx_amount:
        doc_data["transaction"] = {
            "date": args.tx_date,
            "id": args.tx_id,
            "transfer_id": args.tx_transfer_id,
            "amount": args.tx_amount,
            "currency": args.tx_currency or "USD",
        }

    doc = Document.model_validate(doc_data)

    context = {
        "provider": provider,
        "client": client,
        "doc": doc.model_dump(),
        "bank": bank,
    }

    html = render_template("letter.html", context)

    # Save to client archive
    client_dir = get_client_archive_dir(client_id)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Sanitize subject for filename
    subject_slug = (args.subject or "letter")[:30].lower().replace(" ", "-").replace("/", "-")
    filename = args.output or f"{date_str}_{letter_number}_{subject_slug}.pdf"
    output_path = client_dir / filename

    html_to_pdf(html, output_path, provider_name)
    print(f"Created: {output_path}")
    print(f"Letter: {letter_number}")


CARDS_DIR = ROOT / "cards"


def cmd_card(args):
    """Generate company details card PDF."""
    provider = load_provider(args.provider)
    provider_id = args.provider

    # Get banks to include (default or specified)
    all_banks = provider.get("banks", {})
    if args.banks:
        bank_names = [b.strip() for b in args.banks.split(",")]
    else:
        # Include default banks for each currency, or first 4
        seen_currencies = set()
        bank_names = []
        for name, bank in all_banks.items():
            currency = bank.get("currency", "USD")
            if bank.get("default") or currency not in seen_currencies:
                bank_names.append(name)
                seen_currencies.add(currency)
            if len(bank_names) >= 4:
                break

    # Build bank list with QR codes
    banks = []
    for name in bank_names:
        if name not in all_banks:
            continue
        bank = {"name": name, **all_banks[name]}
        # Generate QR for a sample amount (1000)
        qr = generate_payment_qr(bank, 1000.0, "")
        bank["qr_code"] = qr
        banks.append(bank)

    context = {
        "provider": provider,
        "banks": banks,
        "date": datetime.now().strftime("%B %d, %Y"),
    }

    html = render_template("card.html", context)

    # Save to cards directory
    CARDS_DIR.mkdir(exist_ok=True)
    filename = args.output if args.output else f"{provider_id}-details.pdf"
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    output_path = CARDS_DIR / filename

    html_to_pdf(html, output_path, args.provider)
    print(f"Created: {output_path}")


CV_DIR = ROOT / "cv"


def cmd_cv(args):
    """Generate CV/resume PDF."""
    person = load_person(args.person)

    context = {
        "person": person,
        "date": datetime.now().strftime("%B %Y"),
    }

    html = render_template("cv.html", context)

    # Save to cv directory
    CV_DIR.mkdir(exist_ok=True)
    filename = args.output if args.output else f"{args.person}-cv.pdf"
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    output_path = CV_DIR / filename

    html_to_pdf(html, output_path, None)  # No signature for CV
    print(f"Created: {output_path}")


def cmd_validate(args):
    """Validate all YAML files against schemas."""
    print("\nValidating providers...")
    for name in list_entities("providers"):
        try:
            data = load_yaml(PROVIDERS_DIR / f"{name}.yaml")
            Provider.model_validate(data)
            print(f"  {name}: OK")
        except ValidationError as e:
            print(f"  {name}: FAILED")
            for err in e.errors():
                print(f"    - {err['loc']}: {err['msg']}")

    print("\nValidating clients...")
    for name in list_entities("clients"):
        try:
            data = load_yaml(CLIENTS_DIR / f"{name}.yaml")
            Client.model_validate(data)
            print(f"  {name}: OK")
        except ValidationError as e:
            print(f"  {name}: FAILED")
            for err in e.errors():
                print(f"    - {err['loc']}: {err['msg']}")
    print()


def cmd_cert_setup(args):
    """Create self-signed certificate for PDF signing."""
    if not args.provider:
        print("Error: --provider required", file=sys.stderr)
        print("Usage: crm.py cert-setup -p example-llc")
        sys.exit(1)

    provider = load_provider(args.provider)
    name = args.name or provider.get("signer", {}).get("name") or provider["name"]
    org = provider["name"] if provider.get("type") != "individual" else None
    email = provider.get("contact", {}).get("email")
    country = provider.get("address", {}).get("country", "TR")

    # Map country names to codes
    country_codes = {"Turkey": "TR", "Türkiye": "TR", "USA": "US", "United States": "US"}
    country = country_codes.get(country, country[:2].upper())

    create_self_signed_cert(
        provider_id=args.provider,
        common_name=name,
        organization=org,
        country=country,
        email=email,
        valid_years=args.years or 10,
    )


def cmd_cert_info(args):
    """Show certificate information."""
    certs = list_certificates()
    if not certs:
        print("No certificates found. Run: crm.py cert-setup -p PROVIDER")
        return

    print("\nCertificates:")
    for info in certs:
        print(f"\n  [{info['provider']}]")
        print(f"    Subject: {info['subject']}")
        print(f"    Valid: {info['valid_from']} to {info['valid_until']}")


def cmd_encrypt(args):
    """Encrypt files or directories."""
    if args.setup:
        setup_age_key()
        return

    if not is_age_available():
        print("Error: age not installed. Run: brew install age", file=sys.stderr)
        sys.exit(1)

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        sys.exit(1)

    if path.is_dir():
        pattern = args.pattern or "*.pdf"
        encrypted = encrypt_dir(path, pattern)
        print(f"Encrypted {len(encrypted)} files in {path}")
        for f in encrypted:
            print(f"  {f.name}")
    else:
        result = encrypt_file(path, remove_original=not args.keep)
        if result:
            print(f"Encrypted: {result}")
        else:
            print("Encryption failed", file=sys.stderr)
            sys.exit(1)


def cmd_decrypt(args):
    """Decrypt files or directories."""
    if not is_age_available():
        print("Error: age not installed. Run: brew install age", file=sys.stderr)
        sys.exit(1)

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        sys.exit(1)

    if path.is_dir():
        decrypted = decrypt_dir(path, "*.age")
        print(f"Decrypted {len(decrypted)} files in {path}")
        for f in decrypted:
            print(f"  {f.name}")
    else:
        result = decrypt_file(path, remove_encrypted=not args.keep)
        if result:
            print(f"Decrypted: {result}")
        else:
            print("Decryption failed", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Mini CRM for invoices")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    list_parser = subparsers.add_parser("list", help="List providers or clients")
    list_parser.add_argument("type", choices=["providers", "clients"])
    list_parser.set_defaults(func=cmd_list)

    # show command
    show_parser = subparsers.add_parser("show", help="Show entity details")
    show_parser.add_argument("type", choices=["provider", "client"])
    show_parser.add_argument("name")
    show_parser.set_defaults(func=cmd_show)

    # history command
    hist_parser = subparsers.add_parser("history", help="Show client document history")
    hist_parser.add_argument("client", help="Client name")
    hist_parser.set_defaults(func=cmd_history)

    # validate command
    val_parser = subparsers.add_parser("validate", help="Validate all YAML files")
    val_parser.set_defaults(func=cmd_validate)

    # card command
    card_parser = subparsers.add_parser("card", help="Generate company details card")
    card_parser.add_argument("provider", help="Provider name (e.g., superduperai-us)")
    card_parser.add_argument("--banks", "-b", help="Comma-separated bank names (default: auto-select)")
    card_parser.add_argument("--output", "-o", help="Output filename (default: {provider}-details.pdf)")
    card_parser.set_defaults(func=cmd_card)

    # cv command
    cv_parser = subparsers.add_parser("cv", help="Generate CV/resume")
    cv_parser.add_argument("person", help="Person name (e.g., rustam)")
    cv_parser.add_argument("--output", "-o", help="Output filename")
    cv_parser.set_defaults(func=cmd_cv)

    # invoice command
    inv_parser = subparsers.add_parser("invoice", help="Generate invoice")
    inv_parser.add_argument("client", help="Client name (e.g., epiphan)")
    inv_parser.add_argument("--number", "-n", help="Invoice number (auto if omitted)")
    inv_parser.add_argument("--date", "-d", help="Issue date (DD.MM.YYYY)")
    inv_parser.add_argument("--provider", "-p", help="Provider name")
    inv_parser.add_argument("--description", help="Service description")
    inv_parser.add_argument("--qty", type=int, help="Quantity/hours")
    inv_parser.add_argument("--rate", type=float, help="Rate per unit")
    inv_parser.add_argument("--currency", help="Currency (USD, EUR, TRY)")
    inv_parser.add_argument("--bank", "-b", help="Bank name (e.g., pioneer, ziraat-usd)")
    inv_parser.set_defaults(func=cmd_invoice)

    # letter command
    let_parser = subparsers.add_parser("letter", help="Generate letter")
    let_parser.add_argument("client", help="Client name")
    let_parser.add_argument("--number", "-n", help="Letter number (auto if omitted)")
    let_parser.add_argument("--provider", "-p", help="Provider name")
    let_parser.add_argument("--date", "-d", help="Letter date")
    let_parser.add_argument("--subject", "-s", help="Subject line")
    let_parser.add_argument("--body", "-b", help="Letter body (HTML allowed)")
    let_parser.add_argument("--output", "-o", help="Output filename")
    let_parser.add_argument("--show-bank", action="store_true", help="Show bank details")
    let_parser.add_argument("--tx-date", help="Transaction date")
    let_parser.add_argument("--tx-id", help="Transaction ID")
    let_parser.add_argument("--tx-transfer-id", help="Transfer ID")
    let_parser.add_argument("--tx-amount", help="Transaction amount")
    let_parser.add_argument("--tx-currency", help="Transaction currency")
    let_parser.add_argument("--bank", help="Bank name (e.g., pioneer, ziraat-usd)")
    let_parser.set_defaults(func=cmd_letter)

    # encrypt command
    enc_parser = subparsers.add_parser("encrypt", help="Encrypt files with age")
    enc_parser.add_argument("path", nargs="?", default=".", help="File or directory to encrypt")
    enc_parser.add_argument("--pattern", "-p", help="Glob pattern for directory (default: *.pdf)")
    enc_parser.add_argument("--keep", "-k", action="store_true", help="Keep original files")
    enc_parser.add_argument("--setup", action="store_true", help="Generate new age key")
    enc_parser.set_defaults(func=cmd_encrypt)

    # decrypt command
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt .age files")
    dec_parser.add_argument("path", nargs="?", default=".", help="File or directory to decrypt")
    dec_parser.add_argument("--keep", "-k", action="store_true", help="Keep encrypted files")
    dec_parser.set_defaults(func=cmd_decrypt)

    # cert-setup command
    cert_parser = subparsers.add_parser("cert-setup", help="Create certificate for PDF signing")
    cert_parser.add_argument("--provider", "-p", help="Use provider info for certificate")
    cert_parser.add_argument("--name", "-n", help="Signer name")
    cert_parser.add_argument("--org", "-o", help="Organization name")
    cert_parser.add_argument("--email", "-e", help="Email address")
    cert_parser.add_argument("--country", "-c", help="Country code (e.g., TR, US)")
    cert_parser.add_argument("--years", "-y", type=int, default=10, help="Validity in years")
    cert_parser.set_defaults(func=cmd_cert_setup)

    # cert-info command
    cert_info_parser = subparsers.add_parser("cert-info", help="Show certificate info")
    cert_info_parser.set_defaults(func=cmd_cert_info)

    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
