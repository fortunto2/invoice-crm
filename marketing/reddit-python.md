# Post for r/Python

## Title
I built a CLI invoice generator with Python, Pydantic, Jinja2, and WeasyPrint — open source

## Post

Hey r/Python!

Sharing a project I've been working on: a file-based invoice generator that uses some great Python libraries.

**The stack:**
- **Pydantic** — for data validation and schema definitions
- **Jinja2** — HTML templates for invoices/letters
- **WeasyPrint** — converts HTML/CSS to professional PDFs
- **Click** — clean CLI interface
- **uv** — fast package management

**Architecture decisions:**
- No database — everything is YAML files (easy to version control, backup, edit)
- Single-file main script (~600 lines) — readable and hackable
- Modular QR code generation supporting EPC/SEPA, EMVCo, SWIFT, and crypto addresses
- Optional PDF signing using pyHanko
- Optional encryption using age

**Code highlights:**

Config validation with Pydantic:
```python
class Provider(BaseModel):
    name: str
    type: Literal["corporation", "limited", "individual"]
    address: Address
    banks: dict[str, BankAccount]
    
class Invoice(BaseModel):
    number: str
    date: date
    items: list[LineItem]
    
    @computed_field
    def total(self) -> Decimal:
        return sum(item.amount for item in self.items)
```

PDF generation:
```python
html = template.render(invoice=invoice, provider=provider, client=client)
pdf = weasyprint.HTML(string=html).write_pdf()
```

**Why file-based:**
- Git-friendly: track changes, branch for different businesses
- No migrations, no backups to manage
- Easy to script and automate
- Works perfectly with AI coding assistants

**Links:**
- GitHub: https://github.com/fortunto2/invoice-crm
- MIT License

Looking for feedback on the code structure and Python best practices. PRs welcome!
