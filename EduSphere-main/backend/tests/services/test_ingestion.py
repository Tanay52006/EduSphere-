from pathlib import Path

import pytest

from app.services.ingestion import IngestionError, chunk_pages, extract_pages, validate_pdf
from tools.fixture_spike import generate_fixture_set


def test_pdf_validation_checks_magic_size_and_user_quota() -> None:
    with pytest.raises(IngestionError, match="invalid_pdf_type"):
        validate_pdf(b"not a pdf", "notes.pdf")

    with pytest.raises(IngestionError, match="document_too_large"):
        validate_pdf(b"%PDF-" + b"x" * (25 * 1024 * 1024), "notes.pdf")

    with pytest.raises(IngestionError, match="user_quota_exceeded"):
        validate_pdf(b"%PDF-1.4", "notes.pdf", user_bytes=100 * 1024 * 1024)


def test_extraction_reports_scanned_pages_without_claiming_success(tmp_path: Path) -> None:
    generate_fixture_set(tmp_path)

    pages, ocr_required = extract_pages((tmp_path / "lecture-notes.pdf").read_bytes())
    assert len(pages) == 2
    assert "Cellular respiration" in pages[0].text
    assert ocr_required is False

    scanned_pages, scanned_ocr_required = extract_pages((tmp_path / "scanned-notes.pdf").read_bytes())
    assert len(scanned_pages) == 1
    assert scanned_ocr_required is True


def test_chunking_keeps_page_provenance_and_overlap() -> None:
    long_text = " ".join(f"word-{index}" for index in range(700))
    chunks = chunk_pages([
        type("Page", (), {"page_number": 1, "text": long_text})(),
    ])

    assert len(chunks) == 2
    assert chunks[0].page_start == chunks[0].page_end == 1
    assert chunks[1].text.split()[0] == "word-520"
    assert chunks[0].token_count == 600
