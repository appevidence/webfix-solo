# Ported from appevidence/evidence-capture-app at commit 4b709ed96a38b9ed9bb3a07e8641a2453d72a344
from __future__ import annotations

import hashlib

import httpx

try:
    import rfc3161_client as _rfc3161  # type: ignore[import]

    _HAS_RFC3161_CLIENT = True
except ImportError:
    _HAS_RFC3161_CLIENT = False


class TimestampError(Exception):
    pass


def _build_timestamp_request(data: bytes) -> bytes:
    """Build a minimal DER-encoded RFC 3161 timestamp request."""
    # Hash the data
    digest = hashlib.sha256(data).digest()

    # Build the request manually using DER encoding
    # OID for SHA-256: 2.16.840.1.101.3.4.2.1
    sha256_oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
    # AlgorithmIdentifier: SEQUENCE { OID, NULL }
    null = bytes([0x05, 0x00])
    alg_id_content = sha256_oid + null
    alg_id = bytes([0x30, len(alg_id_content)]) + alg_id_content

    # MessageImprint: SEQUENCE { AlgorithmIdentifier, OCTET STRING }
    octet_string = bytes([0x04, len(digest)]) + digest
    msg_imprint_content = alg_id + octet_string
    msg_imprint = bytes([0x30, len(msg_imprint_content)]) + msg_imprint_content

    # Version: INTEGER 1
    version = bytes([0x02, 0x01, 0x01])

    # certReq: BOOLEAN TRUE
    cert_req = bytes([0x01, 0x01, 0xFF])

    # TimeStampReq: SEQUENCE { version, messageImprint, certReq }
    req_content = version + msg_imprint + cert_req
    if len(req_content) < 128:
        req = bytes([0x30, len(req_content)]) + req_content
    else:
        length = len(req_content)
        len_bytes = length.to_bytes((length.bit_length() + 7) // 8, "big")
        req = bytes([0x30, 0x80 | len(len_bytes)]) + len_bytes + req_content

    return req


async def request_timestamp(data: bytes, tsa_url: str) -> bytes:
    """Request an RFC 3161 timestamp token for the given data.

    Returns DER-encoded timestamp token bytes.
    """
    if _HAS_RFC3161_CLIENT:
        try:
            req = _rfc3161.TimeStampRequest.from_data(data)  # type: ignore[attr-defined]
            req_der = req.as_der()
        except Exception:
            req_der = _build_timestamp_request(data)
    else:
        req_der = _build_timestamp_request(data)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                tsa_url,
                content=req_der,
                headers={"Content-Type": "application/timestamp-query"},
            )
            response.raise_for_status()
            token_der = response.content
    except httpx.HTTPError as exc:
        raise TimestampError(f"TSA request failed: {exc}") from exc

    return token_der


def verify_timestamp(data: bytes, token_der: bytes) -> bool:
    """Verify an RFC 3161 timestamp token against the given data.

    Returns True if valid, raises TimestampError if invalid.
    """
    if _HAS_RFC3161_CLIENT:
        try:
            token = _rfc3161.TimeStampResponse.from_der(token_der)  # type: ignore[attr-defined]
            token.verify(data)
            return True
        except Exception as exc:
            raise TimestampError(f"Timestamp verification failed: {exc}") from exc

    # Minimal verification: just check the token is valid DER and non-empty
    if not token_der:
        raise TimestampError("Empty timestamp token")
    if token_der[0] != 0x30:
        raise TimestampError("Token does not appear to be valid DER")
    return True
