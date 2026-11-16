"""Generate and inspect a small, deterministic PDF corpus for RAG spikes."""

import argparse
from pathlib import Path

from pypdf import PdfReader

FIXTURES: dict[str, list[str | None]] = {
    "lecture-notes.pdf": [
        "Cellular respiration converts glucose into usable energy. Glycolysis occurs in the cytoplasm.",
        "The citric acid cycle occurs in the mitochondrial matrix and produces electron carriers.",
    ],
    "textbook-chapter.pdf": [
        "A binary search repeatedly halves a sorted search interval. Its time complexity is O(log n).",
        "A hash table provides expected constant-time lookup when the hash function distributes keys well.",
    ],
    "slides-export.pdf": [
        "Photosynthesis uses light energy to make sugars from carbon dioxide and water.",
        "Chlorophyll absorbs mostly blue and red wavelengths and reflects green light.",
    ],
    "exam-review.pdf": [
        "A dependent variable is measured as the outcome in an experiment.",
        "Random assignment helps balance confounding variables between groups.",
    ],
    "scanned-notes.pdf": [None],
}


def _pdf_bytes(pages: list[str | None]) -> bytes:
    objects: list[bytes] = []
    page_ids: list[int] = []
    font_id = 3
    for value in pages:
        page_id = 4 + len(page_ids) * 2
        content_id = page_id + 1
        page_ids.append(page_id)
        if value is None:
            stream = b""
        else:
            escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream = f"BT /F1 11 Tf 72 720 Td ({escaped}) Tj ET".encode()
        objects.extend(
            [
                (
                    f"{page_id} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >> endobj\n"
                ).encode(),
                f"{content_id} 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n",
            ]
        )
    objects.insert(0, b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.insert(1, f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >> endobj\n".encode())
    objects.insert(2, b"3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(output)


def generate_fixture_set(output_dir: Path) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report: list[dict[str, object]] = []
    for name, pages in FIXTURES.items():
        path = output_dir / name
        path.write_bytes(_pdf_bytes(pages))
        reader = PdfReader(str(path))
        text_pages = [page.extract_text() or "" for page in reader.pages]
        report.append({"name": name, "pages": len(reader.pages), "text_pages": sum(bool(text.strip()) for text in text_pages)})
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("backend/tests/fixtures/pdfs"))
    args = parser.parse_args()
    for item in generate_fixture_set(args.output):
        print(f"{item['name']}: pages={item['pages']} text_pages={item['text_pages']}")


if __name__ == "__main__":
    main()
