import asyncio
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.ai.factory import create_provider
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.workers.runner import IngestionJobRunner


def process_one(session_factory: Callable[[], Session], embed_text: Callable[[str], list[float]] | None = None) -> bool:
    with session_factory() as db:
        return IngestionJobRunner().process_next(db, embed_text=embed_text)


def create_sync_embedder(provider: Any, runner: asyncio.Runner) -> Callable[[str], list[float]]:
    return lambda text: runner.run(provider.embed(text))


def main() -> None:
    with asyncio.Runner() as runner:
        provider = create_provider(get_settings())
        embed_text = create_sync_embedder(provider, runner)

        while True:
            processed = process_one(SessionLocal, embed_text=embed_text)
            time.sleep(0.1 if processed else 1.0)


if __name__ == "__main__":
    main()
