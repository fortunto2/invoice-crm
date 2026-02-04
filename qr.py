"""QR code generation for different payment types."""

import base64
import io
from typing import Optional

import segno


def generate_qr_data_uri(data: str, scale: int = 3, border: int = 1) -> str:
    """Generate QR code as base64 data URI for embedding in HTML."""
    qr = segno.make(data, error="M")
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale, border=border)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def epc_qr(
    iban: str,
    holder: str,
    amount: float,
    bic: Optional[str] = None,
    reference: str = "",
    text: str = "",
) -> str:
    """
    Generate EPC QR code data for SEPA payments (EUR only).

    Standard: EPC069-12 (European Payments Council)
    Used by: All EU banks, works with most banking apps.

    Format:
        BCD - Service Tag
        002 - Version
        1 - Character set (UTF-8)
        SCT - SEPA Credit Transfer
        BIC - Bank Identifier (optional since 2016)
        Beneficiary name (max 70 chars)
        IBAN
        EUR + Amount (EUR12.50 format)
        Purpose code (optional)
        Reference (max 35 chars, Creditor Reference or empty)
        Text (max 140 chars, remittance info)
    """
    lines = [
        "BCD",
        "002",
        "1",
        "SCT",
        bic or "",
        holder[:70],
        iban.replace(" ", ""),
        f"EUR{amount:.2f}",
        "",  # purpose code
        reference[:35] if reference else "",
        text[:140] if text else "",
    ]
    return "\n".join(lines)


def swift_qr(
    account: str,
    holder: str,
    amount: float,
    currency: str,
    swift: str,
    bank_name: str,
    routing: Optional[str] = None,
    reference: str = "",
) -> str:
    """
    Generate text-based QR for SWIFT/wire transfers.

    No standard format - just readable payment details.
    Useful for manual entry or screenshot sharing.
    """
    lines = [
        f"Beneficiary: {holder}",
        f"Account: {account}",
    ]
    if routing:
        lines.append(f"Routing: {routing}")
    lines.extend([
        f"SWIFT/BIC: {swift}",
        f"Bank: {bank_name}",
        f"Amount: {currency} {amount:.2f}",
    ])
    if reference:
        lines.append(f"Reference: {reference}")
    return "\n".join(lines)


def crypto_qr(
    address: str,
    amount: Optional[float] = None,
    currency: str = "USDT",
    network: str = "TRC20",
) -> str:
    """
    Generate crypto payment QR.

    For USDT/TRC20: just the address (wallets scan it directly)
    For Bitcoin: BIP21 URI format (bitcoin:address?amount=X)
    """
    if currency.upper() == "BTC":
        uri = f"bitcoin:{address}"
        if amount:
            uri += f"?amount={amount}"
        return uri
    elif currency.upper() in ("ETH", "USDT", "USDC"):
        # For ERC20/TRC20 tokens, just return address
        # Some wallets support ethereum: URI but it's not universal
        return address
    else:
        return address


def emvco_qr(
    iban: str,
    holder: str,
    amount: float,
    currency: str,
    country_code: str = "TR",
    reference: str = "",
) -> str:
    """
    Generate simplified EMVCo-style QR for IBAN transfers.

    Based on EMVCo Merchant Presented QR specification.
    Supported by banking apps in Turkey, UAE, and other countries.

    TLV structure (Tag-Length-Value):
        00 - Payload Format Indicator
        01 - Point of Initiation (12 = dynamic)
        26-51 - Merchant Account Info (we use 26 for generic IBAN)
        52 - Merchant Category Code
        53 - Transaction Currency (ISO 4217 numeric)
        54 - Transaction Amount
        58 - Country Code
        59 - Merchant Name
        60 - Merchant City
        62 - Additional Data (reference)
        63 - CRC checksum
    """
    # ISO 4217 currency codes
    currency_codes = {
        "TRY": "949", "USD": "840", "EUR": "978", "GBP": "826",
        "AED": "784", "SAR": "682", "RUB": "643",
    }

    def tlv(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    # Build merchant account info (tag 26)
    # Sub-tags: 00=GUI, 01=IBAN
    gui = "TR.TCMB.FAST"  # Turkey FAST system identifier
    merchant_acct = tlv("00", gui) + tlv("01", iban.replace(" ", ""))

    parts = [
        tlv("00", "01"),  # Payload format indicator
        tlv("01", "12"),  # Dynamic QR (one-time use)
        tlv("26", merchant_acct),  # Merchant account info
        tlv("52", "0000"),  # MCC: generic
        tlv("53", currency_codes.get(currency, "949")),
        tlv("54", f"{amount:.2f}"),
        tlv("58", country_code),
        tlv("59", holder[:25]),  # Merchant name (max 25)
        tlv("60", "TURKIYE"),  # City
    ]

    if reference:
        # Additional data field 62, sub-tag 05 = reference
        parts.append(tlv("62", tlv("05", reference[:25])))

    # Add CRC placeholder
    payload = "".join(parts) + "6304"

    # Calculate CRC-16 CCITT
    crc = crc16_ccitt(payload)
    return payload + f"{crc:04X}"


def crc16_ccitt(data: str) -> int:
    """Calculate CRC-16 CCITT for EMVCo QR."""
    crc = 0xFFFF
    for char in data:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def iban_qr(
    iban: str,
    holder: str,
    amount: float,
    currency: str,
    swift: Optional[str] = None,
    bank_name: str = "",
    reference: str = "",
    country: Optional[str] = None,
) -> str:
    """
    Generate QR for IBAN-based transfers.

    For EUR: Use EPC format (European banking apps)
    For TRY: Use EMVCo format (Turkish banking apps)
    For other currencies: Text-based format
    """
    if currency == "EUR":
        return epc_qr(iban, holder, amount, swift, reference)

    # Turkish lira - use EMVCo format for Ziraat/other TR banks
    if currency == "TRY" or (country and country.upper() in ("TR", "TURKEY")):
        return emvco_qr(iban, holder, amount, currency, "TR", reference)

    # Text format for other IBAN transfers
    lines = [
        f"Beneficiary: {holder}",
        f"IBAN: {iban}",
    ]
    if swift:
        lines.append(f"SWIFT/BIC: {swift}")
    if bank_name:
        lines.append(f"Bank: {bank_name}")
    lines.append(f"Amount: {currency} {amount:.2f}")
    if reference:
        lines.append(f"Reference: {reference}")
    return "\n".join(lines)


def generate_payment_qr(
    bank: dict,
    amount: float,
    reference: str = "",
) -> Optional[str]:
    """
    Generate appropriate QR code based on bank type.

    Returns base64 data URI or None if QR not applicable.

    Args:
        bank: Bank dict with currency, iban/account, swift, holder, etc.
        amount: Payment amount
        reference: Invoice/reference number

    Returns:
        Data URI string for <img src="..."> or None
    """
    currency = bank.get("currency", "USD")
    holder = bank.get("holder", "")

    # Crypto payments
    if currency in ("USDT", "BTC", "ETH", "USDC"):
        address = bank.get("iban") or bank.get("account")  # We store TRC20 address in iban field
        if address:
            data = crypto_qr(address, amount, currency, bank.get("bank_address", ""))
            return generate_qr_data_uri(data)
        return None

    # IBAN-based payments (SEPA for EUR, EMVCo for TRY, text for others)
    if bank.get("iban"):
        data = iban_qr(
            iban=bank["iban"],
            holder=holder,
            amount=amount,
            currency=currency,
            swift=bank.get("swift"),
            bank_name=bank.get("bank_name", ""),
            reference=reference,
            country=bank.get("country"),
        )
        return generate_qr_data_uri(data)

    # SWIFT/wire transfer (US banks, etc.)
    if bank.get("account") and bank.get("swift"):
        data = swift_qr(
            account=bank["account"],
            holder=holder,
            amount=amount,
            currency=currency,
            swift=bank["swift"],
            bank_name=bank.get("bank_name", ""),
            routing=bank.get("routing"),
            reference=reference,
        )
        return generate_qr_data_uri(data)

    return None
