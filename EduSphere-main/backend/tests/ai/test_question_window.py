import pytest

from app.ai.mock import MockProvider
from app.ai.questions import generate_questions, source_window
from app.core.errors import AppError
from app.models.library import Chunk


def test_source_context_has_a_total_budget():
    chunks = [Chunk(id=str(i), user_id="u", document_id="d", ordinal=i, text="word " * 2000,
                    page_start=i + 1, page_end=i + 1, token_count=2000) for i in range(12)]
    sources = source_window(chunks)
    assert sum(len(s["text"]) for s in sources) <= 16_000
    assert all(len(s["text"]) <= 4000 for s in sources)
    assert len(sources) == 4


async def test_quotes_outside_the_actual_prompt_window_are_not_accepted():
    class Provider(MockProvider):
        async def generate_json(self, schema, prompt, **kwargs):
            assert schema.__name__ == "GeneratedQuestions"
            return {"questions": [{"kind": "MCQ", "prompt": "Which answer is supported?", "options": ["A", "B", "C", "D"],
                "answer": "A", "explanation": "A is the supported answer.", "source_chunk_id": "c", "source_quote": "This quote was never sent."}]}

    chunk = Chunk(id="c", user_id="u", document_id="d", ordinal=0, text="word " * 1000 + "This quote was never sent.",
                  page_start=1, page_end=1, token_count=1010)
    with pytest.raises(AppError) as error:
        await generate_questions(Provider(), [chunk])
    assert error.value.code == "insufficient_grounding"
