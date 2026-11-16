from typing import Any


def track(event: str, props: dict[str, Any] | None = None) -> None:
    del event, props


def identify(user_id: str, props: dict[str, Any] | None = None) -> None:
    del user_id, props
