import copy
import json

import httpx
import pytest

from glucotrust.assess import create_assessor
from glucotrust.corpus import load_corpus
from glucotrust.validate import Assessment, Citation, validate_assessment
from scripts.run_eval import PacedClient, check_configuration, summarize


def test_replay_rejects_mixed_model_or_settings():
    row = dict(model="model-a", prompt_version="2.1.0", run={"identity": {
        "provider": "groq", "model": "model-a", "options": {"temperature": 0}}})
    other = copy.deepcopy(row)
    other["run"]["identity"]["options"]["temperature"] = 1
    with pytest.raises(ValueError, match="Mixed experiment"):
        check_configuration([row, other])
    other = copy.deepcopy(row)
    other["model"] = "model-b"
    with pytest.raises(ValueError, match="Mixed experiment"):
        check_configuration([row, other])


def test_replay_rejects_changed_model_digest():
    config = {"model_identity": {"provider": "ollama", "model_digest": "frozen"}}
    with pytest.raises(ValueError, match="identity changed"):
        check_configuration([dict(configuration=config, run={"identity": {
            "provider": "ollama", "model_digest": "replaced"}})])


def test_explicit_provider_overrides_environment(monkeypatch):
    monkeypatch.setenv("GLUCOTRUST_PROVIDER", "ollama")
    assert create_assessor(provider="groq", api_key="").model == "openai/gpt-oss-20b"


def test_hosted_pacing_includes_every_request(monkeypatch):
    ticks = iter([0, 10, 60])
    monkeypatch.setattr("scripts.run_eval.time.monotonic", lambda: next(ticks))
    waits = []
    monkeypatch.setattr("scripts.run_eval.time.sleep", waits.append)
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **kw: "response")
    with PacedClient(60) as client:
        assert client.post("https://example.org") == "response"
        assert client.post("https://example.org") == "response"
    assert waits == [50]


def test_empty_oracle_and_validation_downgrade_are_counted_separately():
    claims = [dict(claim_id="a", label="insufficient", gold_passage_ids=[])]
    rows = [dict(claim_id="a", mode=mode, passage_ids=[],
                 configuration={"oracle_scope": "all_claims"},
                 assessment={"verdict": "insufficient", "validation_failed": mode == "end_to_end"})
            for mode in ("end_to_end", "oracle")]
    summary = summarize(claims, rows)
    assert summary["oracle"]["abstention"]["n"] == 1
    assert summary["oracle"]["model_abstentions_on_insufficient"] == 1
    assert summary["end_to_end"]["validation_downgrades"] == 1
    assert summary["end_to_end"]["model_abstentions_on_insufficient"] == 0


def test_adversarial_quotes_are_exact_but_cannot_prove_entailment():
    from scripts.run_eval import read_jsonl
    passages = load_corpus("data/curated/passages.jsonl")
    lookup = {p.passage_id: p for p in passages}
    cases = read_jsonl("eval/claims_adversarial.jsonl")
    assert 5 <= len(cases) <= 10
    for case in cases:
        assert case["label_rationale"]
        evidence = [lookup[pid] for pid in case["gold_passage_ids"]]
        assert any(case["tempting_quote"] in p.text for p in evidence)
    case = next(c for c in cases if c["claim_id"] == "adv-04")
    # Deliberately constructed output, not a recorded model result.
    misleading = Assessment(verdict="supported", explanation="An invalid inference.", citations=[
        Citation(passage_id=case["gold_passage_ids"][0], quote=case["tempting_quote"])])
    validated = validate_assessment(misleading, [lookup[case["gold_passage_ids"][0]]])
    assert not validated.validation_failed
    assert validated.verdict == "supported" and case["label"] == "insufficient"


def test_current_references_do_not_replace_archived_records():
    from pathlib import Path
    passages = {p.passage_id: p for p in load_corpus("data/curated/passages.jsonl")}
    refs = json.loads(Path("data/curated/current_references.json").read_text())["references"]
    assert len(refs) == 3
    for ref in refs:
        assert ref["url"].startswith("https://www.niddk.nih.gov/")
        assert ref["support_summary"] and ref["scope_limit"] and ref["section"]
        for pid in ref["passage_ids"]:
            assert passages[pid].provenance_status == "archived_record"
            assert passages[pid].url != ref["url"]
