from dataclasses import dataclass


@dataclass(frozen=True)
class RankedChunk:
    chunk_id: str
    score: float


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    top_k: int = 5,
    rrf_k: int = 60,
) -> list[RankedChunk]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        seen: set[str] = set()
        for rank, chunk_id in enumerate(ranked_list, start=1):
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (rrf_k + rank)
    return [RankedChunk(chunk_id, score) for chunk_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]]
