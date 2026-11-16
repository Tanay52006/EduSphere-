from typing import Any, Protocol


class AnalyticsBackend(Protocol):
    def track(self, event: str, props: dict[str, Any]) -> None: ...
    def identify(self, user_id: str, props: dict[str, Any]) -> None: ...


class NoopAnalytics:
    def track(self, event: str, props: dict[str, Any]) -> None:
        return None

    def identify(self, user_id: str, props: dict[str, Any]) -> None:
        return None


_backend: AnalyticsBackend = NoopAnalytics()


def track(event: str, props: dict[str, Any]) -> None:
    _backend.track(event, props)


def identify(user_id: str, props: dict[str, Any]) -> None:
    _backend.identify(user_id, props)
