import json
import re
from typing import Any

from app.ai.mock_activities import mock_activity


class MockProvider:
    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        return "Mock response"

    async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if getattr(schema, "__name__", "") in {"ActivityProposal", "ActivityVerdict"}:
            return mock_activity(schema.__name__, prompt)
        if getattr(schema, "__name__", "") in {"GeneratedQuestions", "ValidatedQuestions"}:
            data = json.loads(next(line for line in prompt.splitlines() if line.startswith('{"quoted_sources"')))
            if schema.__name__ == "ValidatedQuestions":
                return {"verdicts": [{"index": i, "supported": True} for i, _ in enumerate(data["proposals"])]}
            facts: list[tuple[str, str, str, str]] = []
            for source in data["quoted_sources"]:
                pattern = r"([A-Z][A-Za-z-]*(?: [a-z][A-Za-z-]*){0,2})\s+(?:is|are|means|refers to)\s+([^.!?\n]{12,250}[.!?]?)"
                for match in re.finditer(pattern, source["text"]):
                    if match[1] not in {f[0] for f in facts}:
                        facts.append((match[1], match[2], match[0], source["id"]))
            questions = []
            planned = [(False, f) for f in facts[:16]] + [(True, f) for f in facts[-8:]]
            for i, (memory, (term, definition, quote, chunk_id)) in enumerate(planned):
                if len(facts) < 4:
                    break
                options = [facts[(i + j) % len(facts)][0] for j in range(4)]
                questions.append({
                    "kind": "MATCH" if memory else "MCQ",
                    "prompt": f"Match the concept: {term}" if memory else f"Which concept fits this description? {definition}",
                    "options": [] if memory else options[i % 4:] + options[:i % 4],
                    "answer": definition if memory else term,
                    "explanation": quote, "term": term if memory else None,
                    "definition": definition if memory else None, "source_chunk_id": chunk_id,
                    "source_quote": quote, "difficulty": 1,
                })
            return {"questions": questions}
        return {}

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        return [0.0, 0.0, 0.0]
