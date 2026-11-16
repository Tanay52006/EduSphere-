from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator


class QuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kind: Literal["MCQ", "MATCH"]
    prompt: str = Field(min_length=8, max_length=600)
    options: list[str] = Field(default_factory=list, max_length=4)
    answer: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=8, max_length=1200)
    term: str | None = Field(default=None, max_length=100)
    definition: str | None = Field(default=None, max_length=300)
    source_chunk_id: str = Field(min_length=1, max_length=36)
    source_quote: str = Field(min_length=12, max_length=1200)
    difficulty: int = Field(default=1, ge=1, le=3)

    @model_validator(mode="after")
    def check_shape(self) -> Self:
        if self.kind == "MCQ":
            if len(self.options) != 4 or len(set(o.casefold().strip() for o in self.options)) != 4:
                raise ValueError("Four distinct options required")
            if any(not o.strip() or len(o) > 500 for o in self.options) or self.answer not in self.options:
                raise ValueError("Answer must be an option")
        elif not self.term or not self.definition or self.term.casefold() == self.definition.casefold():
            raise ValueError("Distinct term and definition required")
        return self


class GeneratedQuestions(BaseModel):
    questions: list[QuestionDraft] = Field(min_length=1, max_length=24)


class ValidationVerdict(BaseModel):
    index: int = Field(ge=0, le=23)
    supported: StrictBool


class ValidatedQuestions(BaseModel):
    verdicts: list[ValidationVerdict] = Field(max_length=24)


class QuestionEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    prompt: str = Field(min_length=8, max_length=600)


class StartGame(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1, max_length=36)
    game: Literal["quiz_blitz", "memory_match"]


class AnswerQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1, max_length=36)
    choice: str = Field(max_length=500)


class FlipCard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_id: str = Field(min_length=1, max_length=36)


class SubmitGame(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PauseClock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paused: bool
