# Ported from appevidence/evidence-capture-app at commit 416ea2fb5549fc936cb3f001e82a11161dce6179
from __future__ import annotations

import pytest

from app.signing import (
    generate_keypair,
    private_key_to_public_pem,
    sign_bytes,
    verify_signature,
)


def test_generate_keypair():
    priv_pem, pub_pem = generate_keypair()
    assert b"PRIVATE KEY" in priv_pem
    assert b"PUBLIC KEY" in pub_pem


def test_generate_keypair_with_passphrase():
    priv_pem, pub_pem = generate_keypair(passphrase=b"secret")
    assert b"PRIVATE KEY" in priv_pem
    assert b"PUBLIC KEY" in pub_pem


def test_sign_and_verify():
    priv_pem, pub_pem = generate_keypair()
    data = b"hello, world"
    sig = sign_bytes(data, priv_pem)
    assert verify_signature(data, sig, pub_pem) is True


def test_verify_tampered_data():
    priv_pem, pub_pem = generate_keypair()
    data = b"original data"
    sig = sign_bytes(data, priv_pem)
    with pytest.raises(ValueError):
        verify_signature(b"tampered data", sig, pub_pem)


def test_verify_tampered_signature():
    priv_pem, pub_pem = generate_keypair()
    data = b"original data"
    sig = sign_bytes(data, priv_pem)
    tampered_sig = bytes([sig[0] ^ 0xFF]) + sig[1:]
    with pytest.raises(ValueError):
        verify_signature(data, tampered_sig, pub_pem)


def test_private_key_to_public_pem():
    priv_pem, pub_pem = generate_keypair()
    derived_pub_pem = private_key_to_public_pem(priv_pem)
    assert derived_pub_pem == pub_pem


def test_sign_with_passphrase():
    priv_pem, pub_pem = generate_keypair(passphrase=b"mypass")
    data = b"secure data"
    sig = sign_bytes(data, priv_pem, passphrase=b"mypass")
    assert verify_signature(data, sig, pub_pem) is True
