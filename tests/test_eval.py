import pytest
from scripts.run_eval import summarize


def test_oracle_and_refusal_metrics():
    claims = [dict(claim_id="a", label="supported", gold_passage_ids=["p"]), dict(claim_id="b", label="insufficient", gold_passage_ids=[])]
    rows = [dict(claim_id="a", mode="end_to_end", assessment={"verdict": "insufficient"}, passage_ids=["other"]),
            dict(claim_id="b", mode="end_to_end", assessment={}, passage_ids=["other"]),
            dict(claim_id="a", mode="oracle", assessment={"verdict": "supported"}, passage_ids=["p"])]
    result = summarize(claims, rows)
    assert result["oracle"]["accuracy"]["rate"] == 1
    assert result["end_to_end"]["recall_at_3"]["n"] == 0
    assert result["end_to_end"]["abstention"]["n"] == 0
    with pytest.raises(ValueError, match="Incomplete"):
        summarize(claims, rows[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        summarize(claims, rows + [rows[0]])


def test_latency_excludes_cache_hits():
    claims = [dict(claim_id="a", label="supported", gold_passage_ids=["p"])]
    rows = [dict(claim_id="a", mode=mode, assessment={"verdict": "supported"}, passage_ids=["p"],
                 run={"cache_hit": mode == "oracle", "response": {"total_duration": 2_000_000_000}})
            for mode in ("end_to_end", "oracle")]
    summary = summarize(claims, rows)
    assert summary["end_to_end"]["inference_latency_seconds"]["mean"] == 2
    assert summary["oracle"]["inference_latency_seconds"]["n"] == 0
