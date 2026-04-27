# Ported from appevidence/evidence-capture-app at commit b343b4e8db30a7d620f22e857985ef2cc97fbd57
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select

from app.database import get_session, init_db
from app.db_models import CaptureRecord


def test_init_db_creates_tables(tmp_path: Path):
    db_path = tmp_path / "test.sqlite"
    engine = init_db(db_path)
    inspector = sa_inspect(engine)
    tables = inspector.get_table_names()
    assert "captures" in tables
    assert "audit_records" in tables


def test_capture_record_crud(tmp_path: Path):
    db_path = tmp_path / "test.sqlite"
    engine = init_db(db_path)
    now = datetime.now(UTC)

    # Create
    with get_session(engine) as session:
        record = CaptureRecord(
            url="https://example.com",
            captured_at=now,
            bundle_path="/some/path/bundle.zip",
            manifest_hash="abc123",
            verified=False,
        )
        session.add(record)

    # Read
    with get_session(engine) as session:
        stmt = select(CaptureRecord).where(CaptureRecord.url == "https://example.com")
        result = session.execute(stmt).scalar_one()
        assert result.url == "https://example.com"
        assert result.manifest_hash == "abc123"
        assert result.verified is False


def test_capture_record_update(tmp_path: Path):
    db_path = tmp_path / "test.sqlite"
    engine = init_db(db_path)
    now = datetime.now(UTC)

    with get_session(engine) as session:
        record = CaptureRecord(url="https://example.com", captured_at=now)
        session.add(record)

    with get_session(engine) as session:
        record = session.execute(
            select(CaptureRecord).where(CaptureRecord.url == "https://example.com")
        ).scalar_one()
        record.verified = True

    with get_session(engine) as session:
        record = session.execute(
            select(CaptureRecord).where(CaptureRecord.url == "https://example.com")
        ).scalar_one()
        assert record.verified is True
