# Ported from appevidence/evidence-capture-app at commit f4f2dcfbec88a55cdb0ae25531ac9787065827ea
from __future__ import annotations

from pathlib import Path

from app.audit import AuditEntry, AuditLog


def list_audit_entries(data_dir: Path, limit: int = 50) -> list[AuditEntry]:
    """Return the most recent audit log entries from the given data directory."""
    log_path = data_dir / "audit.log"
    log = AuditLog(log_path)
    return log.get_entries(limit=limit)


def verify_audit_entry(data_dir: Path, entry_id: str) -> tuple[bool, str]:
    """Verify a single audit log entry by ID."""
    log_path = data_dir / "audit.log"
    log = AuditLog(log_path)
    return log.verify_entry(entry_id)


def verify_audit_chain(data_dir: Path) -> tuple[bool, list[str]]:
    """Verify the entire audit log hash chain."""
    log_path = data_dir / "audit.log"
    log = AuditLog(log_path)
    return log.verify_chain()
