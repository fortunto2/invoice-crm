# Post for r/ClaudeAI

## Title
Built an "agent-first" invoice generator — designed to work with Claude Code and AI assistants

## Post

I've been using Claude Code (and similar AI coding tools) for a while, and I noticed that most invoice/billing software is terrible for AI agents to work with — SaaS dashboards, complex APIs, OAuth flows.

So I built something different: a file-based invoice generator that's specifically designed to be AI-friendly.

**Why it's agent-compatible:**

1. **Plain text everything** — YAML configs, JSON state, Markdown docs. Claude can read and edit everything directly.

2. **Single CLI** — One command generates an invoice. No clicking through UIs.
   ```bash
   uv run python crm.py invoice acme-corp --qty 40 --rate 150
   ```

3. **No auth, no API keys** — It's a local Python script. Your AI assistant just runs it.

4. **Self-documenting** — Each client/provider YAML file contains all the context the agent needs.

**Real workflow with Claude Code:**

Me: "Generate invoice for ACME, 40 hours at $150, due in 30 days"

Claude: *reads clients/acme-corp.yaml, runs the command, outputs PDF*

Me: "Add a new client — BigCorp, contact john@bigcorp.com, same terms as ACME"

Claude: *creates new YAML file based on existing template*

**The design philosophy:**
- Everything an AI agent needs should be in plain text files
- No hidden state in databases or cloud services
- Commands should be simple and composable
- The codebase should be small enough for the agent to understand (~600 lines main script)

**Features:**
- Professional PDF invoices with QR payment codes
- Multiple currencies (USD, EUR, GBP, TRY)
- Digital signatures and encryption (optional)
- Letter and company card generation

GitHub: https://github.com/fortunto2/invoice-crm

Anyone else building tools with AI agents in mind? Would love to hear about other "agent-first" design patterns.
