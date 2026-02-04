.PHONY: install validate list cards clean help
.DEFAULT_GOAL := help

# Install dependencies
install:
	@which brew > /dev/null && brew install pango 2>/dev/null || true
	uv sync

# Validate all YAML files
validate:
	@uv run python crm.py validate

# List providers and clients
list:
	@uv run python crm.py list providers
	@uv run python crm.py list clients

# Generate all company cards
cards:
	@uv run python crm.py card example-llc
	@uv run python crm.py card freelancer

# Invoice examples
invoice-acme:
	uv run python crm.py invoice acme-corp

invoice-startup:
	uv run python crm.py invoice startup-inc

# Letter example
letter-example:
	uv run python crm.py letter acme-corp -p example-llc \
		--subject "Business Inquiry" \
		--body "<p>Thank you for your interest in our services.</p>"

# PDF Digital Signatures
cert-all:
	@uv run python crm.py cert-setup -p example-llc
	@uv run python crm.py cert-setup -p freelancer

cert-info:
	@uv run python crm.py cert-info

# Encryption (optional, requires: brew install age)
encrypt-setup:
	@uv run python crm.py encrypt --setup

encrypt-archive:
	@uv run python crm.py encrypt archive/

encrypt-cards:
	@uv run python crm.py encrypt cards/

decrypt-archive:
	@uv run python crm.py decrypt archive/

decrypt-cards:
	@uv run python crm.py decrypt cards/

# Clean generated files
clean:
	rm -f archive/*/*.pdf archive/*/*.age cards/*.pdf cards/*.age

# Show client history
history-%:
	@uv run python crm.py history $*

help:
	@echo "Invoice CRM - File-based invoice generator"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make validate         Validate YAML files"
	@echo "  make cert-all         Create PDF signing certificates"
	@echo ""
	@echo "Generate:"
	@echo "  make cards            Generate all company cards"
	@echo "  make invoice-acme     Invoice for ACME Corp"
	@echo "  make invoice-startup  Invoice for Startup Inc"
	@echo ""
	@echo "Security (optional):"
	@echo "  make cert-info        Show PDF signing certificates"
	@echo "  make encrypt-setup    Generate age encryption key"
	@echo "  make encrypt-archive  Encrypt PDFs in archive/"
	@echo ""
	@echo "Info:"
	@echo "  make list             List providers and clients"
	@echo "  make history-CLIENT   Show client history"
	@echo ""
	@echo "CLI: uv run python crm.py --help"
