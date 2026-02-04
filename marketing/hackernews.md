# Hacker News Post

## Title
Show HN: Invoice CRM – File-based invoice generator (Python, YAML, no SaaS)

## URL
https://github.com/fortunto2/invoice-crm

## Text (if self-post)

I built a simple invoice generator for my freelance work and decided to open source it.

The philosophy: all data in plain YAML files, no database, no SaaS, no monthly fees. Just a Python CLI that generates professional PDFs.

Key design decisions:

- File-based: providers and clients are YAML files, counters are JSON, templates are Jinja2/HTML. Everything goes in git.

- QR codes: auto-generated for the invoice currency. EPC/SEPA for EUR (scans in EU banking apps), EMVCo for TRY, SWIFT text for USD, crypto addresses for USDT/BTC.

- Single script: ~600 lines of Python. Easy to audit, modify, and extend.

- AI-friendly: designed to work with Claude Code, Cursor, etc. An agent can read client configs, run commands, and generate invoices without any web UI or API.

Tech stack: Python 3.11+, uv, Pydantic, Jinja2, WeasyPrint.

Optional: PDF digital signatures (pyHanko), file encryption (age).

---

## Expected HN comments to prepare for:

1. "Why not just use Excel/Google Sheets?" — Valid for simple cases. This is for people who want version control, automation, and AI integration.

2. "There's already invoice-ninja, crater, etc." — Those are full web apps with databases. This is intentionally minimal and file-based.

3. "No multi-user support?" — Correct, this is designed for solo freelancers or small shops. Use git branches for multiple entities.
