import secrets
from pathlib import Path
from typing import Protocol


class PathTraversalError(ValueError):
    pass


class FileStore(Protocol):
    def save(self, filename: str, content: bytes) -> Path: ...


class LocalFileStore:
    def __init__(self, root: str | Path, max_size: int = 10 * 1024 * 1024) -> None:
        self.root = Path(root).resolve()
        self.max_size = max_size
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> Path:
        candidate = (self.root / filename).resolve()
        if self.root not in candidate.parents:
            raise PathTraversalError("file path escapes storage directory")
        if len(content) > self.max_size:
            raise ValueError("file exceeds storage limit")
        path = self.root / f"{secrets.token_urlsafe(24)}.bin"
        path.write_bytes(content)
        return path
