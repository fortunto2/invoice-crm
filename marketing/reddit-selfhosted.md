# Post for r/selfhosted

## Title
Invoice CRM — self-hosted, file-based invoice generator (Python, no DB, git-friendly)

## Post

Hey r/selfhosted!

I built a simple invoice generator for freelancers that I've been using for a while and decided to open-source it.

**What it is:**
- CLI tool that generates professional PDF invoices from YAML files
- Zero dependencies on external services — runs entirely locally
- No database — all data is plain YAML/JSON files you can version control
- Supports multiple currencies, bank accounts, and automatic QR code generation for payments

**Why I built it:**
I was tired of SaaS invoice tools that:
- Charge monthly fees for something that should be simple
- Store my financial data on their servers
- Don't integrate well with my workflow (I wanted something I could script)

**Key features:**
- Invoice, letter, and company card generation
- QR codes: EPC/SEPA (EU), EMVCo (Turkey), SWIFT, and crypto
- Optional PDF digital signatures
- Optional age encryption for sensitive docs
- Works great with AI coding assistants (Claude Code, Cursor, etc.)

**Tech stack:**
- Python 3.11+ with uv package manager
- Jinja2 templates + WeasyPrint for PDF
- Pydantic for validation
- Plain YAML for all data

**Self-hosting:**
Just clone and run. No Docker required, no database, no Redis. All your data stays in plain text files.

```bash
git clone https://github.com/fortunto2/invoice-crm.git
cd invoice-crm
make install
uv run python crm.py invoice my-client
```

GitHub: https://github.com/fortunto2/invoice-crm

Would love feedback from the community! What features would you add?
