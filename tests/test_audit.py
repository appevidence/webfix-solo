# Ported from appevidence/evidence-capture-app at commit d6c1fb2d8cadb36607031916e2f577a416dfd420
from __future__ import annotations

import json
from pathlib import Path

from app.audit import AuditLog


def test_audit_log_append_creates_entry(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    entry = log.append(action="capture", url="https://example.com")
    assert entry.action == "capture"
    assert entry.url == "https://example.com"
    assert entry.entry_id is not None
    assert entry.entry_hash is not None
    assert log_path.exists()


def test_audit_log_get_entries(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    log.append(action="capture", url="https://example.com")
    log.append(action="verify", url="https://example.com")
    log.append(action="export", url="https://example.com")
    entries = log.get_entries()
    assert len(entries) == 3
    assert entries[0].action == "capture"
    assert entries[2].action == "export"


def test_audit_log_get_entries_limit(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    for i in range(10):
        log.append(action=f"action_{i}")
    entries = log.get_entries(limit=3)
    assert len(entries) == 3


def test_audit_log_verify_chain_valid(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    log.append(action="capture", url="https://example.com")
    log.append(action="verify")
    log.append(action="export", bundle_hash="abc123")
    ok, errors = log.verify_chain()
    assert ok, f"Expected valid chain, got errors: {errors}"
    assert errors == []


def test_audit_log_verify_chain_tampered(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    log.append(action="capture", url="https://example.com")
    log.append(action="verify")

    # Tamper with the first entry
    lines = log_path.read_text().splitlines()
    first = json.loads(lines[0])
    first["action"] = "TAMPERED"
    lines[0] = json.dumps(first)
    log_path.write_text("\n".join(lines) + "\n")

    ok, errors = log.verify_chain()
    assert not ok
    assert len(errors) > 0


def test_audit_log_verify_entry(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    entry = log.append(action="capture", url="https://example.com")
    ok, msg = log.verify_entry(entry.entry_id)
    assert ok
    assert "valid" in msg.lower()


def test_audit_log_verify_entry_not_found(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    ok, _msg = log.verify_entry("nonexistent-id")
    assert not ok


def test_audit_log_chain_links(tmp_path: Path):
    """Verify that each entry's prev_hash links to the previous entry_hash."""
    log_path = tmp_path / "audit.log"
    log = AuditLog(log_path)
    e1 = log.append(action="first")
    e2 = log.append(action="second")
    e3 = log.append(action="third")
    assert e1.prev_hash is None
    assert e2.prev_hash == e1.entry_hash
    assert e3.prev_hash == e2.entry_hash
