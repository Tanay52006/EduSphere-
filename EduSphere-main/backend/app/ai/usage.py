from typing import Protocol


class UsageBudget(Protocol):
    def allow(self, user_id: str, estimated_tokens: int) -> bool: ...


class NoopUsageBudget:
    def allow(self, user_id: str, estimated_tokens: int) -> bool:
        return True
