from pathlib import Path

from tools.rag_eval import evaluate_fixture_set, format_report


def test_rag_eval_reports_hit_rates_and_mrr_without_secrets(tmp_path: Path) -> None:
    report = evaluate_fixture_set(tmp_path)

    assert report["cases"] == 4
    assert report["hit_at_1"] == 1.0
    assert report["hit_at_3"] == 1.0
    assert report["mrr"] == 1.0
    rendered = format_report(report)
    assert "hit_at_1" in rendered
    assert "API_KEY" not in rendered
    assert "service-account" not in rendered
