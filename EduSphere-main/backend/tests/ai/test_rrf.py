from app.ai.retrieval.rrf import reciprocal_rank_fusion


def test_rrf_merges_rankings_with_deterministic_ties() -> None:
    merged = reciprocal_rank_fusion(
        [["chunk-a", "chunk-b"], ["chunk-b", "chunk-c"]],
        top_k=3,
    )

    assert [item.chunk_id for item in merged] == ["chunk-b", "chunk-a", "chunk-c"]
    assert merged[0].score > merged[1].score


def test_rrf_deduplicates_a_chunk_across_ranked_lists() -> None:
    merged = reciprocal_rank_fusion([["chunk-a", "chunk-a"]], top_k=5)

    assert [item.chunk_id for item in merged] == ["chunk-a"]
