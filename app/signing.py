# Ported from appevidence/evidence-capture-app at commit 416ea2fb5549fc936cb3f001e82a11161dce6179
from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)


def generate_keypair(passphrase: bytes | None = None) -> tuple[bytes, bytes]:
    """Generate a new Ed25519 keypair.

    Returns (private_key_pem, public_key_pem).
    """
    private_key = Ed25519PrivateKey.generate()
    encryption = BestAvailableEncryption(passphrase) if passphrase else NoEncryption()
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def load_private_key(pem: bytes, passphrase: bytes | None = None) -> Ed25519PrivateKey:
    """Load an Ed25519 private key from PEM bytes."""
    key = load_pem_private_key(pem, password=passphrase)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("PEM does not contain an Ed25519 private key")
    return key


def load_public_key(pem: bytes) -> Ed25519PublicKey:
    """Load an Ed25519 public key from PEM bytes."""
    key = load_pem_public_key(pem)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("PEM does not contain an Ed25519 public key")
    return key


def sign_bytes(data: bytes, private_key_pem: bytes, passphrase: bytes | None = None) -> bytes:
    """Sign data with an Ed25519 private key. Returns raw signature bytes."""
    private_key = load_private_key(private_key_pem, passphrase)
    return private_key.sign(data)


def verify_signature(data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    """Verify an Ed25519 signature. Returns True or raises ValueError."""
    public_key = load_public_key(public_key_pem)
    try:
        public_key.verify(signature, data)
        return True
    except InvalidSignature as exc:
        raise ValueError("Signature verification failed") from exc


def private_key_to_public_pem(private_key_pem: bytes, passphrase: bytes | None = None) -> bytes:
    """Extract the public key PEM from a private key PEM."""
    private_key = load_private_key(private_key_pem, passphrase)
    return private_key.public_key().public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
