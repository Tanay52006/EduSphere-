from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

ItemId = Annotated[str, Field(pattern=r"^n[1-8]$", max_length=2)]
BucketId = Annotated[str, Field(pattern=r"^b[1-3]$", max_length=2)]


class ActivityItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(pattern=r"^n[1-8]$")
    label: str = Field(min_length=1, max_length=90)
    source_chunk_id: str = Field(default="", max_length=36)
    source_quote: str = Field(default="", max_length=600)


class ActivityBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(pattern=r"^b[1-3]$")
    label: str = Field(min_length=1, max_length=40)
    rule: str = Field(min_length=5, max_length=180)


class ActivityBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    mechanic: Literal["sequence", "sort", "connections"]
    subject: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=3, max_length=70)
    goal: str = Field(min_length=8, max_length=220)
    why_fit: str = Field(min_length=10, max_length=240)
    explanation: str = Field(min_length=10, max_length=900)
    items: list[ActivityItem] = Field(min_length=4, max_length=8)
    buckets: list[ActivityBucket] = Field(default_factory=list, max_length=3)
    order: list[str] = Field(default_factory=list, max_length=8)
    assignments: dict[str, str] = Field(default_factory=dict, max_length=8)
    links: list[tuple[str, str]] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def playable(self) -> Self:
        ids = {item.id for item in self.items}
        if len(ids) != len(self.items) or len({i.label.casefold() for i in self.items}) != len(ids):
            raise ValueError("Distinct cards required")
        if self.mechanic == "sequence":
            if len(self.order) != len(ids) or set(self.order) != ids or self.links or self.buckets or self.assignments:
                raise ValueError("A sequence must order every card exactly once")
        elif self.mechanic == "sort":
            buckets = {b.id for b in self.buckets}
            if len(buckets) != len(self.buckets) or len(buckets) < 2 or set(self.assignments) != ids:
                raise ValueError("Every card needs one of two or three distinct groups")
            if set(self.assignments.values()) != buckets or self.order or self.links:
                raise ValueError("All groups must be used")
        else:
            edges = set(self.links)
            if len(edges) != len(self.links) or len(edges) < 3 or self.order or self.assignments or self.buckets:
                raise ValueError("A system needs distinct connections")
            if any(a not in ids or b not in ids or a == b for a, b in edges) or {i for e in edges for i in e} != ids:
                raise ValueError("Connections must use every station")
            reached = {next(iter(ids))}
            for _ in ids:
                reached |= {b for a, b in edges if a in reached} | {a for a, b in edges if b in reached}
            remaining = set(ids)
            for _ in ids:
                remaining -= {n for n in remaining if not any(b == n and a in remaining for a, b in edges)}
            if reached != ids or remaining:
                raise ValueError("Use one connected acyclic system")
        return self


class ActivityProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity: ActivityBlueprint | None


class ActivityVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supported: StrictBool
    unambiguous: StrictBool
    appropriate: StrictBool


class GenerateActivity(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    document_id: str = Field(min_length=1, max_length=36)
    focus: str = Field(default="", max_length=160)


class StartActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity_id: str = Field(min_length=1, max_length=64)


class RunActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order: list[ItemId] = Field(default_factory=list, max_length=8)
    assignments: dict[ItemId, BucketId] = Field(default_factory=dict, max_length=8)
    links: list[tuple[ItemId, ItemId]] = Field(default_factory=list, max_length=10)
