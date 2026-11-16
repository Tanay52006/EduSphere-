"""Development-only extraction of explicit numbered steps or repeated category words."""
import json
import re
from collections import Counter
from typing import Any


def mock_activity(schema_name: str, prompt: str) -> dict[str, Any]:
    if schema_name == "ActivityVerdict":
        # shortcut: mock checks exercise the pipeline, real semantic validation requires a configured provider.
        return {"supported": True, "unambiguous": True, "appropriate": True}
    data = json.loads(next(line for line in prompt.splitlines() if line.startswith('{"quoted_sources"')))
    for source in data["quoted_sources"]:
        steps = list(re.finditer(r"(?m)^\s*(\d{1,2})[.)]\s+([^\n]{5,140})", source["text"]))[:8]
        if len(steps) >= 4 and [int(step[1]) for step in steps] == list(range(1, len(steps) + 1)):
            items = [{"id": f"n{i + 1}", "label": step[2][:90], "source_chunk_id": source["id"],
                      "source_quote": step[0].strip()} for i, step in enumerate(steps)]
            return {"activity": {"mechanic": "sequence", "subject": "Your material", "title": "Rebuild the process",
                    "goal": "Put the documented steps back into their stated order.",
                    "why_fit": "The source explicitly numbers a sequence, so reconstructing its order practices that process.",
                    "explanation": "This order follows the numbered steps in your source. Open the cited page to review the complete process.",
                    "items": items, "order": [item["id"] for item in items], "buckets": [], "assignments": {}, "links": []}}
    facts: list[tuple[str, str, str, str]] = []
    for source in data["quoted_sources"]:
        for match in re.finditer(r"([A-Z][A-Za-z-]*(?: [a-z][A-Za-z-]*){0,2}) is (?:an?|the) ([a-z][a-z-]+)[^.!?\n]{8,220}[.!?]?", source["text"]):
            if match[1] not in {f[0] for f in facts}:
                facts.append((match[1], match[2], match[0], source["id"]))
    counts = Counter(f[1] for f in facts)
    categories = [key for key, count in counts.items() if count >= 2][:3]
    if len(categories) < 2:
        return {"activity": None}
    selected = [f for category in categories for f in [f for f in facts if f[1] == category][:2]]
    return {"activity": {"mechanic": "sort", "subject": "Your material", "title": "Find the family",
            "goal": "Group each example by the category explicitly named in your material.",
            "why_fit": "The source names repeated categories; sorting examples applies those explicit classification rules.",
            "explanation": "Each sample belongs to the category word in its cited source sentence. Review the original statements on your page.",
            "items": [{"id": f"n{i + 1}", "label": f[0], "source_chunk_id": f[3], "source_quote": f[2]} for i, f in enumerate(selected)],
            "buckets": [{"id": f"b{i + 1}", "label": key.capitalize(),
                         "rule": f"The source explicitly describes the example as {key}."} for i, key in enumerate(categories)],
            "assignments": {f"n{i + 1}": f"b{categories.index(f[1]) + 1}" for i, f in enumerate(selected)}, "order": [], "links": []}}
