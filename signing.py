"""PDF digital signatures using pyHanko."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from pyhanko.sign import signers, fields
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

ROOT = Path(__file__).parent
CERT_DIR = ROOT / ".certs"

# Check if signing is available
SIGNING_ENABLED = os.environ.get("PDF_SIGN", "1") != "0"


def get_cert_paths(provider_id: str) -> tuple[Path, Path]:
    """Get certificate and key paths for a provider."""
    return (
        CERT_DIR / f"{provider_id}.pem",
        CERT_DIR / f"{provider_id}.key",
    )


def is_signing_available(provider_id: Optional[str] = None) -> bool:
    """Check if certificate exists for signing."""
    if provider_id:
        cert, key = get_cert_paths(provider_id)
        return cert.exists() and key.exists()
    # Check if any certificate exists
    return any(CERT_DIR.glob("*.pem")) if CERT_DIR.exists() else False


def create_self_signed_cert(
    provider_id: str,
    common_name: str,
    organization: Optional[str] = None,
    country: str = "TR",
    email: Optional[str] = None,
    valid_years: int = 10,
) -> tuple[Path, Path]:
    """
    Create a self-signed certificate for PDF signing.

    Args:
        provider_id: Provider ID for filename (e.g., "rustam-personal")
        common_name: Your name (e.g., "Rustam Salavatov")
        organization: Company name (optional)
        country: 2-letter country code
        email: Email address (optional)
        valid_years: Certificate validity period

    Returns:
        Tuple of (cert_path, key_path)
    """
    CERT_DIR.mkdir(exist_ok=True)
    cert_path, key_path = get_cert_paths(provider_id)

    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Build subject
    name_attrs = [
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
    ]
    if organization:
        name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
    if email:
        name_attrs.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))

    subject = issuer = x509.Name(name_attrs)

    # Create certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=valid_years * 365))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,  # Non-repudiation
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    # Save key
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    # Save certificate
    cert_path.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )

    print(f"Certificate created: {cert_path}")
    print(f"Private key: {key_path}")
    print(f"Valid until: {cert.not_valid_after_utc.strftime('%Y-%m-%d')}")
    print(f"\nSubject: {common_name}")
    if organization:
        print(f"Organization: {organization}")

    return cert_path, key_path


def sign_pdf(
    pdf_path: Path,
    provider_id: str,
    reason: str = "Document signed digitally",
    location: Optional[str] = None,
) -> Path:
    """
    Sign a PDF file with the provider's certificate.

    Args:
        pdf_path: Path to PDF file
        provider_id: Provider ID to use certificate for
        reason: Reason for signing
        location: Location of signing (optional)

    Returns:
        Path to signed PDF (overwrites original)
    """
    if not SIGNING_ENABLED:
        return pdf_path

    cert_path, key_path = get_cert_paths(provider_id)
    if not cert_path.exists() or not key_path.exists():
        return pdf_path

    # Load certificate and key
    signer = signers.SimpleSigner.load(
        str(key_path),
        str(cert_path),
        key_passphrase=None,
    )

    # Read PDF
    with open(pdf_path, 'rb') as f:
        w = IncrementalPdfFileWriter(f)

        # Create signature field
        sig_field_spec = fields.SigFieldSpec(
            sig_field_name="Signature",
            on_page=0,  # First page
            box=(400, 50, 550, 100),  # Bottom right, small
        )

        # Sign
        meta = signers.PdfSignatureMetadata(
            field_name="Signature",
            reason=reason,
            location=location,
        )

        # Write signed PDF to temp file then replace
        signed_path = pdf_path.with_suffix('.signed.pdf')
        with open(signed_path, 'wb') as out:
            signers.sign_pdf(
                w,
                meta,
                signer=signer,
                output=out,
                new_field_spec=sig_field_spec,
            )

    # Replace original with signed
    signed_path.replace(pdf_path)

    return pdf_path


def get_cert_info(provider_id: str) -> Optional[dict]:
    """Get information about a provider's certificate."""
    cert_path, _ = get_cert_paths(provider_id)
    if not cert_path.exists():
        return None

    cert = load_cert_from_pemder(str(cert_path))

    return {
        "provider": provider_id,
        "subject": cert.subject.human_friendly,
        "issuer": cert.issuer.human_friendly,
        "valid_from": cert.not_valid_before.strftime("%Y-%m-%d"),
        "valid_until": cert.not_valid_after.strftime("%Y-%m-%d"),
        "serial": cert.serial_number,
    }


def list_certificates() -> list[dict]:
    """List all available certificates."""
    if not CERT_DIR.exists():
        return []

    certs = []
    for cert_file in CERT_DIR.glob("*.pem"):
        provider_id = cert_file.stem
        info = get_cert_info(provider_id)
        if info:
            certs.append(info)
    return certs
