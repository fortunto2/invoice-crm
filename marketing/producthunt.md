# Product Hunt Launch

## Product Name
Invoice CRM

## Tagline (60 chars max)
File-based invoice generator for freelancers. No SaaS, no fees.

## Description

**Invoice CRM is a free, open-source CLI tool that generates professional PDF invoices from simple YAML files.**

### Why we built this

Every invoice tool eventually wants $20/month for features most freelancers don't need. We wanted something simpler:

- **No database** — all data in plain text files you can version control
- **No SaaS** — runs locally on your machine
- **No monthly fees** — MIT license, free forever

### Key Features

🧾 **Professional PDFs** — Clean, modern invoice templates with your logo and signature

📱 **Smart QR Codes** — Auto-generated payment QR codes:
- EPC/SEPA for EUR (scans in any EU banking app)
- EMVCo for TRY (Turkish banks)
- SWIFT for USD
- Crypto addresses for USDT/BTC

🔐 **Optional Security** — PDF digital signatures and age encryption

🤖 **AI-Agent Friendly** — Designed to work with Claude Code, Cursor, and other AI coding tools. Your AI assistant can read configs and generate invoices without any web UI.

📁 **Git-Friendly** — Everything is YAML, JSON, and Markdown. Branch for different businesses, track changes, revert mistakes.

### Tech Stack

Python 3.11+, Pydantic, Jinja2, WeasyPrint, Click, uv

### Who is this for?

- Freelance developers, designers, consultants
- Small agencies without dedicated accounting software
- Anyone who wants to version control their invoices
- AI enthusiasts who want their tools to be agent-compatible

## First Comment (Maker's comment)

Hey Product Hunt! 👋

I'm the maker of Invoice CRM. I built this out of frustration with paying for invoice software I barely used.

The philosophy is simple: **if it can be a text file, it should be a text file.**

Your clients, providers, and bank details are YAML. Your templates are HTML. Your invoice history is a folder of PDFs. Everything goes in git.

A nice side effect: AI coding assistants (Claude Code, Cursor, etc.) can work with it directly. Tell your AI "create invoice for ClientX" and it just works — no APIs, no auth, no clicking through UIs.

I'd love your feedback:
- What features would make this more useful for you?
- What's missing for your invoicing workflow?

The repo is MIT licensed and I'm actively maintaining it. PRs and issues welcome!

GitHub: https://github.com/fortunto2/invoice-crm

## Topics/Tags
- Invoicing
- Open Source
- Developer Tools
- Freelance
- Productivity
- CLI Tools
- Python

## Gallery images needed
1. Hero: Invoice screenshot with QR code
2. Terminal showing generation command
3. YAML config example
4. Before/after: YAML → PDF

## Scheduled launch
Consider launching on a Tuesday-Thursday for best visibility.
