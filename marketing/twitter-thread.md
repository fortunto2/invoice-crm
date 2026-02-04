# Twitter/X Thread

## Tweet 1 (Hook)
I got tired of paying $20/month for invoice software.

So I built my own: file-based, git-friendly, works with AI agents.

Open source, MIT license. Here's the thread 🧵

## Tweet 2 (The problem)
The problem with invoice SaaS:

• Monthly fees for something I use 2-3 times a month
• My financial data on someone else's servers
• No way to automate without paying for API access
• Can't version control my invoice history

## Tweet 3 (The solution)
My solution: everything in plain text files.

• Clients and providers → YAML
• Templates → HTML/Jinja2
• Counters → JSON
• Output → PDF

One command generates a professional invoice with QR codes for payment.

## Tweet 4 (AI angle)
The killer feature: it's AI-agent friendly.

Tell Claude Code "invoice ACME for 40 hours" and it just works.

• Reads client config from YAML
• Runs the CLI command
• Outputs PDF

No OAuth, no API keys, no web UI to navigate.

## Tweet 5 (CTA)
Try it yourself:

```
git clone https://github.com/fortunto2/invoice-crm
cd invoice-crm && make install
uv run python crm.py invoice acme-corp
```

MIT license. Free forever.

Would love your feedback → github.com/fortunto2/invoice-crm

---

## Alt versions for individual tweets

### Hook alternatives:
- "Every freelancer tool eventually becomes a SaaS with monthly fees. I built one that can't."
- "Your invoicing tool doesn't need a database. Hear me out."
- "Built an invoice generator that AI agents can use. Here's why that matters."

### Image suggestions:
- Tweet 1: Screenshot of generated invoice
- Tweet 3: Terminal showing the command
- Tweet 4: Side-by-side of YAML config + generated PDF
