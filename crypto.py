"""Optional encryption using age (https://age-encryption.org)."""

import os
import subprocess
from pathlib import Path
from typing import Optional

# Config: key in project dir (.age-key.txt) or home (~/.age/key.txt)
ROOT = Path(__file__).parent
LOCAL_KEY = ROOT / ".age-key.txt"
HOME_KEY = Path.home() / ".age" / "key.txt"

AGE_RECIPIENT = os.environ.get("AGE_RECIPIENT")  # public key: age1...
AGE_KEY_FILE = os.environ.get("AGE_KEY_FILE") or (str(LOCAL_KEY) if LOCAL_KEY.exists() else str(HOME_KEY))


def is_age_available() -> bool:
    """Check if age is installed."""
    try:
        subprocess.run(["age", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_recipient() -> Optional[str]:
    """Get age recipient (public key) from env or key file."""
    if AGE_RECIPIENT:
        return AGE_RECIPIENT

    # Try to extract public key from key file
    key_path = Path(AGE_KEY_FILE)
    if key_path.exists():
        content = key_path.read_text()
        for line in content.splitlines():
            if line.startswith("# public key:"):
                return line.split(":")[-1].strip()
    return None


def encrypt_file(input_path: Path, output_path: Optional[Path] = None, remove_original: bool = False) -> Optional[Path]:
    """
    Encrypt file with age.

    Args:
        input_path: File to encrypt
        output_path: Output path (default: input_path + .age)
        remove_original: Delete original after encryption

    Returns:
        Path to encrypted file or None if encryption unavailable
    """
    recipient = get_recipient()
    if not recipient or not is_age_available():
        return None

    output_path = output_path or input_path.with_suffix(input_path.suffix + ".age")

    try:
        subprocess.run(
            ["age", "-r", recipient, "-o", str(output_path), str(input_path)],
            check=True,
            capture_output=True,
        )
        if remove_original:
            input_path.unlink()
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Encryption failed: {e.stderr.decode()}")
        return None


def decrypt_file(input_path: Path, output_path: Optional[Path] = None, remove_encrypted: bool = False) -> Optional[Path]:
    """
    Decrypt file with age.

    Args:
        input_path: Encrypted file (.age)
        output_path: Output path (default: remove .age suffix)
        remove_encrypted: Delete encrypted file after decryption

    Returns:
        Path to decrypted file or None if decryption failed
    """
    key_path = Path(AGE_KEY_FILE)
    if not key_path.exists() or not is_age_available():
        return None

    if output_path is None:
        # Remove .age suffix
        if input_path.suffix == ".age":
            output_path = input_path.with_suffix("")
        else:
            output_path = input_path.with_suffix(".decrypted")

    try:
        subprocess.run(
            ["age", "-d", "-i", str(key_path), "-o", str(output_path), str(input_path)],
            check=True,
            capture_output=True,
        )
        if remove_encrypted:
            input_path.unlink()
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Decryption failed: {e.stderr.decode()}")
        return None


def encrypt_dir(dir_path: Path, pattern: str = "*.pdf") -> list[Path]:
    """Encrypt all matching files in directory."""
    encrypted = []
    for file in dir_path.glob(pattern):
        if file.suffix == ".age":
            continue
        result = encrypt_file(file, remove_original=True)
        if result:
            encrypted.append(result)
    return encrypted


def decrypt_dir(dir_path: Path, pattern: str = "*.age") -> list[Path]:
    """Decrypt all .age files in directory."""
    decrypted = []
    for file in dir_path.glob(pattern):
        result = decrypt_file(file, remove_encrypted=True)
        if result:
            decrypted.append(result)
    return decrypted


def setup_age_key() -> Path:
    """Generate new age key pair in project directory."""
    key_path = LOCAL_KEY  # Always create in project dir

    if key_path.exists():
        print(f"Key already exists: {key_path}")
        # Show public key
        content = key_path.read_text()
        for line in content.splitlines():
            if line.startswith("# public key:"):
                print(f"Public key: {line.split(':')[-1].strip()}")
        return key_path

    if not is_age_available():
        raise RuntimeError("age not installed. Run: brew install age")

    result = subprocess.run(
        ["age-keygen", "-o", str(key_path)],
        capture_output=True,
        text=True,
    )

    # Extract public key from output
    for line in result.stderr.splitlines():
        if line.startswith("Public key:"):
            public_key = line.split(":")[-1].strip()
            print(f"Key generated: {key_path}")
            print(f"Public key: {public_key}")
            print(f"\nKey is in .gitignore, safe to use.")
            return key_path

    return key_path
