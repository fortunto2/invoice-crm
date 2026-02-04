"""Pydantic schemas for CRM entities."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class Address(BaseModel):
    """Address information."""
    street: str
    suite: Optional[str] = None
    building: Optional[str] = None
    city: str
    state: Optional[str] = None
    region: Optional[str] = None
    zip: str
    country: str


class BankAccount(BaseModel):
    """Bank account details."""
    currency: str = "USD"
    country: Optional[str] = None
    holder: str
    account: Optional[str] = None
    routing: Optional[str] = None
    swift: Optional[str] = None
    iban: Optional[str] = None
    bank_name: str
    bank_address: Optional[str] = None
    default: bool = False


class Signer(BaseModel):
    """Authorized signer."""
    name: str
    title: Optional[str] = None
    authority: Optional[str] = None
    foreign_id: Optional[str] = None
    citizenship: Optional[str] = None
    signature: Optional[str] = None  # path to signature image


class TaxInfo(BaseModel):
    """Tax information."""
    tin: Optional[str] = None
    vat: Optional[str] = None


class Registration(BaseModel):
    """Company registration details."""
    state: Optional[str] = None
    file_number: Optional[str] = None
    ein: Optional[str] = None  # US EIN
    trade_registry: Optional[str] = None
    mersis: Optional[str] = None
    vkn: Optional[str] = None
    reg_number: Optional[str] = None
    date: Optional[str] = None
    activity: Optional[str] = None
    tax_office: Optional[str] = None
    tax_number: Optional[str] = None


class Contact(BaseModel):
    """Contact information."""
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    phone2: Optional[str] = None  # second contact
    website: Optional[str] = None


class Platform(BaseModel):
    """Platform-specific details."""
    client_no: Optional[str] = None


class ClientDefaults(BaseModel):
    """Default invoice settings for a client."""
    provider: Optional[str] = None
    currency: str = "USD"
    rate: float = 50.00
    hours: int = 80
    payment_terms: str = "NET 7 days"


class Provider(BaseModel):
    """Provider (our company) schema."""
    name: str
    name_local: Optional[str] = None  # local language name (e.g., Turkish)
    short_name: Optional[str] = None
    legal_form: Optional[str] = None
    type: str  # corporation, limited, individual
    country_code: Optional[str] = None

    address: Address
    contact: Contact
    banks: dict[str, BankAccount]

    registration: Optional[Registration] = None
    tax: Optional[TaxInfo] = None
    signer: Optional[Signer] = None
    logo: Optional[str] = None
    disclaimer: Optional[str] = None  # footer text for invoices


class Client(BaseModel):
    """Client schema."""
    name: str
    type: str  # corporation, individual

    address: Address
    contact: Contact

    registration: Optional[Registration] = None
    platform: Optional[Platform] = None
    defaults: Optional[ClientDefaults] = None


class InvoiceItem(BaseModel):
    """Invoice line item."""
    description: str
    qty: int
    unit: str = "item"
    price: str  # formatted string
    amount: str  # formatted string
    discount: Optional[str] = None
    vat_rate: int = 0
    vat_amount: Optional[str] = None


class Invoice(BaseModel):
    """Invoice data."""
    number: str
    date: str  # DD.MM.YYYY
    currency: str = "USD"
    payment_terms: str = "NET 7 days"

    line_items: list[InvoiceItem]

    subtotal: str
    vat_rate: int = 0
    vat_total: str = "0,00"
    total: str


class Transaction(BaseModel):
    """Transaction details for refund requests."""
    date: Optional[str] = None
    id: Optional[str] = None
    transfer_id: Optional[str] = None
    amount: Optional[str] = None
    currency: str = "USD"


class Document(BaseModel):
    """Generic document (letter, request, etc)."""
    date: str
    subject: str
    body: str = ""
    show_bank: bool = False
    transaction: Optional[Transaction] = None
