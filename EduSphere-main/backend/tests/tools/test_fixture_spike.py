from pathlib import Path

from pypdf import PdfReader

from tools.fixture_spike import generate_fixture_set


def test_fixture_spike_covers_text_and_scanned_pdf(tmp_path: Path) -> None:
    report = generate_fixture_set(tmp_path)

    assert len(report) == 5
    assert any(item["text_pages"] > 0 for item in report)
    scanned = next(item for item in report if item["name"] == "scanned-notes.pdf")
    assert scanned["pages"] == 1
    assert scanned["text_pages"] == 0


def test_generated_pdf_is_readable(tmp_path: Path) -> None:
    generate_fixture_set(tmp_path)

    reader = PdfReader(str(tmp_path / "lecture-notes.pdf"))
    assert "Cellular respiration" in (reader.pages[0].extract_text() or "")
