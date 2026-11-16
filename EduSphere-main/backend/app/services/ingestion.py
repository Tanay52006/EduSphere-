import hashlib
import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
MAX_DOCUMENT_PAGES = 100
MAX_USER_BYTES = 100 * 1024 * 1024
CHUNK_WORDS = 600
CHUNK_OVERLAP_WORDS = 80
_WHITESPACE = re.compile(r"\s+")


class IngestionError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ValidatedPdf:
    content: bytes
    content_hash: str
    size_bytes: int


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    ordinal: int
    text: str
    page_start: int
    page_end: int
    token_count: int


def validate_pdf(content: bytes, filename: str, user_bytes: int = 0) -> ValidatedPdf:
    if not filename or len(filename) > 255:
        raise IngestionError("invalid_filename")
    if not content.startswith(b"%PDF-"):
        raise IngestionError("invalid_pdf_type")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise IngestionError("document_too_large")
    if user_bytes + len(content) > MAX_USER_BYTES:
        raise IngestionError("user_quota_exceeded")
    return ValidatedPdf(content, hashlib.sha256(content).hexdigest(), len(content))


def extract_pages(content: bytes) -> tuple[list[ExtractedPage], bool]:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        page_count = len(reader.pages)
        if page_count == 0 or page_count > MAX_DOCUMENT_PAGES:
            raise IngestionError("page_limit_exceeded")
        pages = [ExtractedPage(index + 1, _normalise(reader.pages[index].extract_text() or "")) for index in range(page_count)]
    except IngestionError:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise IngestionError("invalid_pdf") from exc
    return pages, any(not page.text for page in pages)


def chunk_pages(pages: list[ExtractedPage]) -> list[TextChunk]:
    words: list[tuple[str, int]] = []
    for page in pages:
        words.extend((word, page.page_number) for word in page.text.split())
    if not words:
        return []
    chunks: list[TextChunk] = []
    start = 0
    ordinal = 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        selected = words[start:end]
        chunks.append(
            TextChunk(
                ordinal=ordinal,
                text=" ".join(word for word, _ in selected),
                page_start=selected[0][1],
                page_end=selected[-1][1],
                token_count=len(selected),
            )
        )
        if end == len(words):
            break
        start = end - CHUNK_OVERLAP_WORDS
        ordinal += 1
    return chunks


def _normalise(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()
